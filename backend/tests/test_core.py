import hashlib
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from releaseguard.api import create_app
from releaseguard.application.ingestion import seed
from releaseguard.application.investigation import Investigator, snapshot
from releaseguard.application.mutations import apply_event
from releaseguard.config import Settings
from releaseguard.domain.models import DemoEvent
from releaseguard.domain.policy import verdict


def event(store, kind, entity, value, key):
    return apply_event(store, DemoEvent(kind=kind, entity_id=entity, value=value, request_key=key))


def test_real_paths_task_history_and_source(store):
    report = Investigator(store).assess("checkout-v2.4", "first")
    assert report["effective_status"] == "Blocked"
    assert {p["service_id"] for p in report["paths"]} == {"checkout", "payments", "ledger"}
    assert report["blockers"][0]["path"] == ["checkout", "payments", "inc-12"]
    assert report["blockers"][0]["owner"]["id"] == "money"
    assert report["blockers"][0]["supported"]
    assert "Overload worsened" in {h["observed_outcome"] for h in report["memory"]}
    rows = store.read("MATCH (t:Task)-[:ASSIGNED_TO]->(o:Team) RETURN t.id,o.id")
    assert rows == [[report["task_ids"][0], "money"]]
    for blocker in report["blockers"]:
        assert all(src in report["sources"] for src in blocker["source_ids"])


def test_idempotent_seed_and_concurrent_tasks(store, dataset):
    before = store.state()
    assert not seed(store, dataset)
    assert store.state() == before
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(
            pool.map(lambda i: Investigator(store).assess("checkout-v2.4", str(i)), range(4))
        )
    assert len({t for report in reports for t in report["task_ids"]}) == 1
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]


def test_replay_and_missing_release(store):
    investigator = Investigator(store)
    first = investigator.assess("checkout-v2.4", "same")
    again = investigator.assess("checkout-v2.4", "same")
    assert first["id"] == again["id"]
    assert store.read("MATCH (a:Assessment) RETURN count(a)") == [[1]]
    with pytest.raises(ValueError, match="Unknown release"):
        investigator.assess("missing", "bad")


def test_new_incident_revision_and_removed_relationship(store):
    investigator = Investigator(store)
    event(store, "incident_status", "inc-12", "resolved", "resolve")
    ready = investigator.assess("checkout-v2.4", "ready")
    assert ready["effective_status"] == "Ready"
    event(store, "new_incident", "inc-13", "ledger", "new-incident")
    assert investigator.latest("checkout-v2.4")["effective_status"] == "Needs reassessment"
    report = investigator.assess("checkout-v2.4", "blocked")
    assert report["blockers"][0]["path"] == ["checkout", "payments", "ledger", "inc-13"]
    event(store, "remove_dependency", "payments", "ledger", "remove")
    assert investigator.latest("checkout-v2.4")["effective_status"] == "Needs reassessment"
    assert investigator.assess("checkout-v2.4", "disconnected")["effective_status"] == "Ready"


def test_expiry_without_database_mutation(store):
    event(store, "incident_status", "inc-12", "resolved", "resolve")
    investigator = Investigator(store, clock=lambda: 1800000000)
    assert investigator.assess("checkout-v2.4", "ready")["effective_status"] == "Ready"
    before = store.state()
    later = Investigator(store, clock=lambda: 1893456001).latest("checkout-v2.4")
    assert later["effective_status"] == "Needs reassessment"
    assert store.state() == before


def test_missing_and_contradictory_verification(store):
    event(store, "incident_status", "inc-12", "resolved", "resolve")
    event(store, "verification_result", "integration-check", "expire", "expire")
    assert (
        Investigator(store).assess("checkout-v2.4", "missing")["effective_status"]
        == "Insufficient evidence"
    )
    event(store, "verification_result", "integration-check", "pass", "pass")
    store.write(
        "MATCH (r:Release {id:'checkout-v2.4'}) CREATE (v:Verification {id:'conflict',"
        "result:'fail',expires_at:1893456000,source_id:'check-record',check_type:'integration'}) "
        "CREATE (v)-[:VERIFIES]->(r)"
    )
    result = Investigator(store).assess("checkout-v2.4", "conflict")
    assert result["effective_status"] == "Insufficient evidence"
    assert "Failing or contradictory integration verification" in result["missing_checks"]


def test_missing_owner_withholds_action(store):
    store.write("MATCH (:Service {id:'payments'})-[e:OWNED_BY]->() DELETE e")
    report = Investigator(store).assess("checkout-v2.4", "owner")
    assert report["effective_status"] == "Blocked"
    assert not report["task_ids"]
    assert "Missing or ambiguous owner: payments" in report["missing_checks"]


def test_missing_source_no_unsupported_action(store):
    store.write("MATCH (s:Source {id:'incident-record'}) DELETE s")
    report = Investigator(store).assess("checkout-v2.4", "source")
    assert report["effective_status"] == "Insufficient evidence"
    assert not report["task_ids"]
    assert report["blockers"][0]["supported"] is False


def test_cycles_and_depth_boundary(store):
    event(store, "add_dependency", "ledger", "checkout", "cycle")
    data = snapshot(store, "checkout-v2.4", 1800000000)
    assert {p["service_id"] for p in data["paths"]} == {"checkout", "payments", "ledger"}
    with store.serialized():

        def apply():
            store.write(
                "MATCH (a:Service {id:'ledger'}) "
                "CREATE (b:Service:Entity {id:'b',source_id:'catalog'}),"
                "(c:Service:Entity {id:'c',source_id:'catalog'}),"
                "(d:Service:Entity {id:'d',source_id:'catalog'}) "
                "CREATE (a)-[:DEPENDS_ON {source_id:'catalog',fact_id:'ab'}]->(b),"
                "(b)-[:DEPENDS_ON {source_id:'catalog',fact_id:'bc'}]->(c),"
                "(c)-[:DEPENDS_ON {source_id:'catalog',fact_id:'cd'}]->(d)"
            )

        store.journal("depth", {"kind": "test-depth"}, apply)
    assert (
        "Dependency scope exceeds four hops"
        in snapshot(store, "checkout-v2.4", 1800000000)["missing_checks"]
    )


def test_dirty_journal_and_recovery(store):
    investigator = Investigator(store)
    investigator.assess("checkout-v2.4", "first")

    def fail():
        store.write("MATCH (i:Incident {id:'inc-12'}) SET i.status='resolved'")
        raise RuntimeError("Injected process failure after domain write")

    with store.serialized(), pytest.raises(RuntimeError):
        store.journal("fault", {"kind": "test"}, fail)
    assert investigator.latest("checkout-v2.4")["effective_status"] == "Needs reassessment"
    with pytest.raises(ValueError, match="Interrupted"):
        investigator.assess("checkout-v2.4", "new")
    with store.serialized():
        store.journal(
            "fault",
            {"kind": "test"},
            lambda: store.write("MATCH (i:Incident {id:'inc-12'}) SET i.status='resolved'"),
        )
    assert not store.state()["dirty"]
    assert investigator.assess("checkout-v2.4", "recovered")["effective_status"] == "Ready"


def test_command_key_conflict_and_invalid_event(store):
    event(store, "incident_status", "inc-12", "resolved", "same")
    with pytest.raises(ValueError, match="conflicts"):
        event(store, "incident_status", "inc-12", "open", "same")
    with pytest.raises(ValueError, match="Unknown"):
        event(store, "add_dependency", "checkout", "unknown", "bad")


def test_malformed_fixture_rejected_before_write(store, dataset):
    before = store.state()
    invalid = dataset.model_copy(deep=True)
    incident = next(n for n in invalid.nodes if n.id == "inc-12")
    del incident.properties["status"]
    with pytest.raises(ValueError, match="Required domain properties"):
        seed(store, invalid)
    assert store.state() == before


def test_new_store_reads_persisted_assessment(store):
    from releaseguard.adapters.falkordb import GraphStore

    first = Investigator(store).assess("checkout-v2.4", "persist")
    second_store = GraphStore(replace(Settings.load(), graph=store.name), store.lock_path.parent)
    second = Investigator(second_store).latest("checkout-v2.4")
    assert first["id"] == second["id"]
    assert second["task_ids"] == first["task_ids"]
    code = "from dataclasses import replace; from releaseguard.config import Settings; from releaseguard.adapters.falkordb import GraphStore; from releaseguard.application.investigation import Investigator; import sys; s=GraphStore(replace(Settings.load(),graph=sys.argv[1])); print(Investigator(s).latest('checkout-v2.4')['id'])"
    child = subprocess.run(
        [sys.executable, "-c", code, store.name], capture_output=True, text=True, check=True
    )
    assert child.stdout.strip() == first["id"]


def test_recovery_replays_actual_event_journal(store):
    from releaseguard.application.recovery import recover

    payload = DemoEvent(
        kind="incident_status", entity_id="inc-12", value="resolved", request_key="recover-event"
    ).model_dump()
    key = "event-" + hashlib.sha256(payload["request_key"].encode()).hexdigest()

    def interrupted():
        store.write("MATCH (i:Incident {id:'inc-12'}) SET i.status='resolved'")
        raise RuntimeError("Injected interruption")

    with store.serialized(), pytest.raises(RuntimeError):
        store.journal(key, payload, interrupted)
    assert recover(store)["recovered"]
    assert (
        Investigator(store).assess("checkout-v2.4", "after-recovery")["effective_status"] == "Ready"
    )


def test_database_graph_separation(store):
    from releaseguard.adapters.falkordb import GraphStore

    other = GraphStore(
        replace(Settings.load(), graph=store.name + "_other"), store.lock_path.parent
    )
    try:
        with other.serialized():
            other.initialize()
        assert other.read("MATCH (t:Task) RETURN count(t)") == [[0]]
        Investigator(store).assess("checkout-v2.4", "task")
        assert other.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    finally:
        other.graph.delete()


def test_api_round_trip_and_demo_disabled(store):
    client = TestClient(create_app(replace(Settings.load(), graph=store.name)))
    assert client.get("/").status_code == 200
    for asset in ("styles.css", "app.js", "icons/shield-check.svg", "fonts/inter-latin.woff2"):
        response = client.get(f"/assets/{asset}")
        assert response.status_code == 200
        assert response.content
    assert client.get("/api/health").status_code == 200
    response = client.post("/api/releases/checkout-v2.4/assessments", json={"request_key": "api"})
    assert response.status_code == 200
    assert response.json()["effective_status"] == "Blocked"
    assert client.get("/api/tasks").json()[0]["owner"] == "Money"
    assert client.post("/api/demo/seed").status_code == 403
    assert (
        client.post(
            "/api/releases/checkout-v2.4/assessments", json={"request_key": "x", "graph": "other"}
        ).status_code
        == 422
    )


def test_real_dependency_failure_no_fallback():
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        client = TestClient(create_app(replace(Settings.load(), port=port)))
        response = client.get("/api/health")
        assert response.status_code == 503
        assert response.json()["error"] == "graph_unavailable"


@pytest.mark.parametrize(
    "blockers,missing,stale,expected",
    [
        ([], [], False, "Ready"),
        ([1], [], False, "Blocked"),
        ([1], [1], False, "Blocked"),
        ([], [1], False, "Insufficient evidence"),
        ([1], [], True, "Needs reassessment"),
    ],
)
def test_policy_precedence(blockers, missing, stale, expected):
    assert verdict(blockers, missing, stale) == expected


def test_no_parameter_injection(store):
    assert (
        store.read("MATCH (s:Service {id:$id}) RETURN s.id", {"id": "checkout' RETURN 1 //"}) == []
    )
    assert store.read("MATCH (s:Service) RETURN count(s)") == [[6]]
