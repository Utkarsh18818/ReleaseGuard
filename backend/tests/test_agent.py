"""Safety and recovery tests execute real queries; scripted model is adversarial input only."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from releaseguard.adapters.gemini import ProviderUnavailable
from releaseguard.api import create_app
from releaseguard.application.agent_investigation import AgentInvestigator
from releaseguard.application.agent_runs import AgentRuns
from releaseguard.application.agent_tools import EvidenceTools
from releaseguard.application.agent_verification import verify
from releaseguard.application.investigation import snapshot
from releaseguard.application.mutations import apply_event
from releaseguard.domain.agent import Proposal
from releaseguard.domain.models import DemoEvent


def proposal():
    return {
        "blocker_ids": ["inc-12"],
        "avoid_attempt_ids": ["retry-increase"],
        "review_attempt_ids": ["timeout-fix"],
        "source_ids": ["release-brief", "catalog", "incident-record", "history-record"],
        "next_step": "review_historical_procedure",
    }


class ScriptedProvider:
    """Deliberately not used as evidence of Gemini capability."""

    def __init__(self, calls=None, hook=None):
        self.calls = calls or [
            ("read_history", {"service_id": "payments"}),
            ("submit_findings", proposal()),
            ("submit_review", {"accept": True, "reason": "supported"}),
        ]
        self.hook = hook
        self.index = 0

    def interact(self, *args, **kwargs):
        if self.hook:
            self.hook(self.index)
        name, arguments = self.calls[self.index]
        self.index += 1
        return {
            "id": str(self.index),
            "calls": [{"id": str(self.index), "name": name, "arguments": arguments}],
            "elapsed_ms": 1,
            "usage": {},
        }


def test_persisted_handoff_new_instance_and_idempotent_action(store):
    agent = AgentInvestigator(store, ScriptedProvider())
    run = agent.investigate("checkout-v2.4", "handoff", stop_at_handoff=True)
    assert run["state"] == "awaiting_verifier"
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    persisted = AgentRuns(store).get(run["id"])
    assert persisted["trace"][0]["result"]["attempts"]
    resumed = AgentInvestigator(
        store, ScriptedProvider([("submit_review", {"accept": True, "reason": "supported"})])
    ).investigate("checkout-v2.4", "handoff")
    assert resumed["state"] == "completed"
    assert resumed["assessment"]["verdict"] == "Blocked"
    assert resumed["explanation"]["avoid"][0]["attempt_id"] == "retry-increase"
    assert store.read("MATCH (t:Task)-[:ASSIGNED_TO]->(o:Team) RETURN o.id") == [["money"]]
    assert agent.investigate("checkout-v2.4", "handoff")["id"] == run["id"]
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]


@pytest.mark.parametrize(
    "call",
    [
        ("raw_cypher", {"query": "MATCH (n) DELETE n"}),
        ("read_history", {"service_id": "notifications"}),
        ("read_source", {"source_id": "unknown"}),
        ("read_history", {"service_id": "payments", "query": "injected"}),
    ],
)
def test_untrusted_tool_input_rejected_without_action(store, call):
    run = AgentInvestigator(store, ScriptedProvider([call])).investigate("checkout-v2.4", "bad")
    assert run["state"] == "rejected"
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    assert store.read("MATCH (s:Service) RETURN count(s)") == [[6]]


def test_unknown_citations_and_incomplete_history_rejected(store):
    bad = proposal()
    bad["avoid_attempt_ids"] = ["invented"]
    run = AgentInvestigator(
        store,
        ScriptedProvider([("read_history", {"service_id": "payments"}), ("submit_findings", bad)]),
    ).investigate("checkout-v2.4", "bad-citation")
    assert run["state"] == "rejected"
    assert any("unknown" in issue for issue in run["verification_issues"])
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_provider_failure_persists_incomplete_no_action(store):
    class Failed:
        def interact(self, *args, **kwargs):
            raise ProviderUnavailable("Gemini request failed (HTTP 503)")

    run = AgentInvestigator(store, Failed()).investigate("checkout-v2.4", "failure")
    assert run["state"] == "incomplete" and run["actions_withheld"]
    assert AgentRuns(store).get(run["id"])["error"].endswith("(HTTP 503)")
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_prose_only_model_cannot_publish_decision_or_task(store):
    class ProseOnly:
        def interact(self, *args, **kwargs):
            return {"id": "prose-turn", "calls": [], "elapsed_ms": 1, "usage": {}}

    run = AgentInvestigator(store, ProseOnly()).investigate("checkout-v2.4", "prose-only")
    assert run["state"] == "rejected" and run["actions_withheld"]
    assert run["error"] == "Model returned no native function call"
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    assert store.read("MATCH (a:Assessment) RETURN count(a)") == [[0]]


def test_incomplete_model_output_is_not_an_accepted_or_rejected_proposal(store):
    class Truncated:
        def interact(self, *args, **kwargs):
            return {
                "id": "budget-limited-turn",
                "status": "incomplete",
                "calls": [],
                "elapsed_ms": 1,
                "usage": {"total_output_tokens": 0},
            }

    run = AgentInvestigator(store, Truncated()).investigate("checkout-v2.4", "truncated")
    assert run["state"] == "incomplete" and run["actions_withheld"]
    assert run["model_turns"][-1]["status"] == "incomplete"
    assert run["model_turns"][-1]["function_calls"] == 0
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    assert store.read("MATCH (a:Assessment) RETURN count(a)") == [[0]]


def test_revision_change_during_model_wait_withholds_action(store):
    def mutation(index):
        if index == 2:
            apply_event(
                store,
                DemoEvent(kind="new_incident", entity_id="new", value="ledger", request_key="new"),
            )

    run = AgentInvestigator(store, ScriptedProvider(hook=mutation)).investigate(
        "checkout-v2.4", "changed"
    )
    assert run["state"] == "stale" and not run["fresh"]
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_budget_exhaustion_and_verifier_rejection(store):
    repeat = [("read_history", {"service_id": "payments"})] * 4
    run = AgentInvestigator(store, ScriptedProvider(repeat)).investigate("checkout-v2.4", "budget")
    assert run["state"] == "rejected" and run["model_calls"] == 4
    calls = [
        ("read_history", {"service_id": "payments"}),
        ("submit_findings", proposal()),
        ("submit_review", {"accept": False, "reason": "unsupported"}),
    ]
    run = AgentInvestigator(store, ScriptedProvider(calls)).investigate("checkout-v2.4", "review")
    assert run["state"] == "rejected"
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_source_checksum_and_missing_checks_gate(store):
    evidence = snapshot(store, "checkout-v2.4", 1800000000)
    trace = [
        {
            "tool": "read_history",
            "result": EvidenceTools(store, evidence).execute(
                "read_history", {"service_id": "payments"}
            ),
        }
    ]
    evidence["sources"]["history-record"]["text"] = "Changed without checksum"
    evidence["missing_checks"] = ["Fresh verification missing"]
    issues = verify(Proposal.model_validate(proposal()), evidence, trace)
    assert "Source checksum mismatch" in issues
    assert "Missing checks require evidence request" in issues


def test_expired_handoff_cannot_act(store):
    first = AgentInvestigator(store, ScriptedProvider(), clock=lambda: 1800000000)
    first.investigate("checkout-v2.4", "expiry", stop_at_handoff=True)
    later = AgentInvestigator(store, ScriptedProvider(), clock=lambda: 1893456001)
    run = later.investigate("checkout-v2.4", "expiry")
    assert run["state"] == "stale" and not run["fresh"]
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_api_missing_key_returns_incomplete_and_persisted_trace(store):
    app = create_app(replace(store.settings, gemini_api_key=""))
    client = TestClient(app)
    response = client.post(
        "/api/releases/checkout-v2.4/agent-investigations", json={"request_key": "missing-key"}
    )
    assert response.status_code == 202
    assert response.json()["state"] == "queued"
    from releaseguard.worker import perform

    perform(response.json()["id"], settings=replace(store.settings, gemini_api_key=""))
    latest = client.get("/api/releases/checkout-v2.4/agent-investigations/latest").json()
    assert latest["state"] == "incomplete"
    assert client.get("/api/jobs/" + response.json()["id"]).json()["state"] == "incomplete"
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]


def test_nested_domain_lock_across_adapters_and_failure_release(store):
    from releaseguard.adapters.falkordb import GraphStore

    other = GraphStore(store.settings, store.lock_path.parent)
    with pytest.raises(RuntimeError), store.serialized(), other.serialized():
        assert other.state() == store.state()
        raise RuntimeError("Nested operation failed")
    with other.serialized():
        assert not other.state()["dirty"]


def test_explicit_verifier_retry_preserves_budget_and_handoff(store):
    AgentInvestigator(store, ScriptedProvider()).investigate(
        "checkout-v2.4", "resume", stop_at_handoff=True
    )

    class Failed:
        def interact(self, *args, **kwargs):
            raise ProviderUnavailable("Gemini request failed (HTTP 503)")

    run = AgentInvestigator(store, Failed()).investigate("checkout-v2.4", "resume")
    assert run["state"] == "incomplete" and run["model_calls"] == 3
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[0]]
    run = AgentInvestigator(
        store, ScriptedProvider([("submit_review", {"accept": True, "reason": "supported"})])
    ).investigate("checkout-v2.4", "resume", resume_verifier=True)
    assert run["state"] == "completed" and run["model_calls"] == 4
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]
    with pytest.raises(ValueError, match="No resumable"):
        AgentInvestigator(store, Failed()).investigate(
            "checkout-v2.4", "resume", resume_verifier=True
        )
