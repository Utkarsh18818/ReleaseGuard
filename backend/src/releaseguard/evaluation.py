"""Same-facts relationship benchmark. No model or workflow speed claims."""

import json
import math
import platform
import statistics
import time
from collections import deque
from dataclasses import replace
from uuid import uuid4

from releaseguard.adapters.falkordb import GraphStore
from releaseguard.application.ingestion import load_dataset, seed
from releaseguard.application.investigation import Investigator
from releaseguard.application.mutations import apply_event
from releaseguard.config import ROOT, Settings
from releaseguard.domain.models import DemoEvent

QUERY = """
MATCH (:Release {id:$release})-[:HAS_CHANGE]->(:Change)-[:TOUCHES]->(root:Service)
MATCH p=(root)-[:DEPENDS_ON*0..4]->(s:Service)
OPTIONAL MATCH (i:Incident)-[:AFFECTED]->(s) WHERE i.status='open' AND i.blocking=true
RETURN s.id,[n IN nodes(p) | n.id],i.id LIMIT 501
"""


def baseline(data):
    """Full structured facts, BFS with cycle handling and equal four-hop scope."""
    nodes = {node["id"]: node for node in data["nodes"]}
    adjacency = {}
    relations = {}
    for edge in data["edges"]:
        relations.setdefault((edge["start"], edge["relation"]), []).append(edge["end"])
        if edge["relation"] == "DEPENDS_ON":
            adjacency.setdefault(edge["start"], []).append(edge["end"])
    roots = [
        service
        for change in relations.get(("checkout-v2.4", "HAS_CHANGE"), [])
        for service in relations.get((change, "TOUCHES"), [])
    ]
    queue = deque((root, [root]) for root in roots)
    paths = {}
    while queue:
        service, path = queue.popleft()
        if service in paths:
            continue
        paths[service] = path
        if len(path) <= 4:
            queue.extend((neighbor, [*path, neighbor]) for neighbor in adjacency.get(service, []))
    blockers = {}
    for id_, node in nodes.items():
        props = node["properties"]
        if node["kind"] == "Incident" and props.get("status") == "open" and props.get("blocking"):
            for affected in relations.get((id_, "AFFECTED"), []):
                if affected in paths:
                    blockers[id_] = paths[affected] + [id_]
    return {"paths": paths, "blockers": blockers}


def graph_result(store):
    rows = store.read(QUERY, {"release": "checkout-v2.4"})
    if len(rows) > 500:
        raise ValueError("Benchmark graph exceeded query budget")
    paths, blockers = {}, {}
    for service, path, incident in rows:
        if service not in paths or len(path) < len(paths[service]):
            paths[service] = path
        if incident and (incident not in blockers or len(path) + 1 < len(blockers[incident])):
            blockers[incident] = path + [incident]
    return {"paths": paths, "blockers": blockers}


def stats(values):
    return {
        "n": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": sorted(values)[math.ceil(len(values) * 0.95) - 1],
    }


def main():
    dataset = load_dataset(ROOT / "fixtures" / "northstar.json")
    data = dataset.model_dump()
    store = GraphStore(replace(Settings.load(), graph="releaseguard_eval_" + uuid4().hex))
    output = {
        "dataset": dataset.name,
        "synthetic": True,
        "nodes_initial": len(data["nodes"]),
        "edges_initial": len(data["edges"]),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "query": QUERY,
        "cases": [],
        "measurement_scope": "Same-facts dependency paths and active blocking incidents only; excludes ingestion, model, actions, policy and source rendering",
        "baseline": "Python adjacency BFS, full identical structured facts, equal four-hop limit",
        "model_api_ms": None,
        "query_timeout_ms": 2000,
    }
    try:
        seed(store, dataset)

        def compare(name):
            graph, simple = graph_result(store), baseline(data)
            output["cases"].append(
                {"name": name, "graph": graph, "baseline": simple, "equal": graph == simple}
            )
            assert graph == simple

        compare("initial Payments risk; unrelated Notifications excluded")
        apply_event(
            store,
            DemoEvent(
                kind="incident_status", entity_id="inc-12", value="resolved", request_key="resolve"
            ),
        )
        for node in data["nodes"]:
            if node["id"] == "inc-12":
                node["properties"]["status"] = "resolved"
        apply_event(
            store,
            DemoEvent(kind="new_incident", entity_id="inc-13", value="ledger", request_key="new"),
        )
        data["nodes"].append(
            {"id": "inc-13", "kind": "Incident", "properties": {"status": "open", "blocking": True}}
        )
        data["edges"].append({"start": "inc-13", "end": "ledger", "relation": "AFFECTED"})
        compare("new two-hop Ledger risk")
        apply_event(
            store,
            DemoEvent(
                kind="remove_dependency", entity_id="payments", value="ledger", request_key="remove"
            ),
        )
        data["edges"] = [
            e
            for e in data["edges"]
            if not (
                e["start"] == "payments" and e["end"] == "ledger" and e["relation"] == "DEPENDS_ON"
            )
        ]
        compare("relationship removed: Ledger incident out of scope")
        apply_event(
            store,
            DemoEvent(
                kind="add_dependency", entity_id="payments", value="ledger", request_key="restore"
            ),
        )
        data["edges"].append({"start": "payments", "end": "ledger", "relation": "DEPENDS_ON"})
        apply_event(
            store,
            DemoEvent(
                kind="add_dependency", entity_id="ledger", value="checkout", request_key="cycle"
            ),
        )
        data["edges"].append({"start": "ledger", "end": "checkout", "relation": "DEPENDS_ON"})
        compare("cycle: finite distinct paths")
        # Warm same connection; measure both algorithms on exactly the final graph facts.
        for _ in range(5):
            graph_result(store)
            baseline(data)
        graph_wall, graph_server, simple_wall = [], [], []
        for _ in range(30):
            start = time.perf_counter()
            result = graph_result(store)
            graph_wall.append((time.perf_counter() - start) * 1000)
            graph_server.append(store.timings[-1]["server_ms"])
            start = time.perf_counter()
            expected = baseline(data)
            simple_wall.append((time.perf_counter() - start) * 1000)
            assert result == expected
        output["graph_client_and_mapping"] = stats(graph_wall)
        output["graph_server_execution"] = stats(graph_server)
        output["baseline_in_memory"] = stats(simple_wall)
        output["warmups"] = 5
        output["raw_samples_ms"] = {
            "graph_client": graph_wall,
            "graph_server": graph_server,
            "baseline": simple_wall,
        }
        output["accuracy_conclusion"] = (
            "Tie on all four synthetic relationship cases; no accuracy superiority established"
        )
        output["speed_conclusion"] = (
            "Baseline is simpler and faster on tiny in-memory data; graph contribution is persisted queryable relationships, not proven speedup"
        )
        # Measure the actual complete deterministic assessment separately.
        run = Investigator(store).assess("checkout-v2.4", "workflow")
        output["single_core_workflow"] = {
            "verdict": run["effective_status"],
            "timing": run["request_timing"],
            "task_count": len(run["task_ids"]),
            "mode": run["mode"],
        }
        directory = ROOT / "outputs" / "implementation"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "graph-comparison.json").write_text(json.dumps(output, indent=2) + "\n")
        print(json.dumps(output, indent=2))
    finally:
        assert store.name.startswith("releaseguard_eval_")
        store.graph.delete()


if __name__ == "__main__":
    main()
