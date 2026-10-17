import hashlib
import json
import time

from releaseguard.application.actions import persist_task
from releaseguard.domain.policy import POLICY_VERSION, effective_status, verdict

DEPENDENCIES = """
MATCH (r:Release {id:$release})-[:HAS_CHANGE]->(c:Change)-[:TOUCHES]->(root:Service)
MATCH p=(root)-[:DEPENDS_ON*0..4]->(s:Service)
RETURN s.id,[n IN nodes(p) | n.id],[e IN relationships(p) | e.source_id],
       [e IN relationships(p) | e.fact_id],c.source_id,r.source_id,[e IN relationships(p) | e.version]
LIMIT 501
"""


def snapshot(store, release: str, now: int):
    records = store.read(DEPENDENCIES, {"release": release})
    if not records:
        raise ValueError("Unknown release or no linked changed service")
    paths = {}
    for service, path, sources, facts, change_source, release_source, fact_versions in records:
        item = {
            "service_id": service,
            "path": path,
            "fact_ids": facts,
            "fact_versions": fact_versions,
            "source_ids": list(dict.fromkeys([release_source, change_source, *sources])),
        }
        if service not in paths or len(path) < len(paths[service]["path"]):
            paths[service] = item
    ids = sorted(paths)
    missing = []
    if len(records) > 500 or len(ids) > 200:
        missing.append("Dependency traversal exceeded result budget")
    boundary = store.read(
        "MATCH (a:Service)-[e:DEPENDS_ON]->(b:Service) "
        "WHERE a.id IN $ids AND NOT b.id IN $ids RETURN a.id,b.id LIMIT 1",
        {"ids": ids},
    )
    if boundary:
        missing.append("Dependency scope exceeds four hops")
    owners = store.read(
        "MATCH (s:Service) WHERE s.id IN $ids "
        "OPTIONAL MATCH (s)-[e:OWNED_BY]->(t:Team) "
        "RETURN s.id,t.id,t.name,e.source_id LIMIT 401",
        {"ids": ids},
    )
    owner_map = {}
    for service, team, name, source in owners:
        owner_map.setdefault(service, []).append({"id": team, "name": name, "source_id": source})
    for service in ids:
        options = owner_map.get(service, [])
        if len(options) != 1 or not options[0]["id"]:
            missing.append("Missing or ambiguous owner: " + service)
    if len(owners) > 400:
        missing.append("Ownership result budget exceeded")
    incidents = store.read(
        "MATCH (i:Incident)-[e:AFFECTED]->(s:Service) "
        "WHERE s.id IN $ids AND i.status='open' AND i.blocking=true "
        "RETURN i.id,i.summary,s.id,i.source_id,e.source_id LIMIT 201",
        {"ids": ids},
    )
    if len(incidents) > 200:
        missing.append("Incident result budget exceeded")
    blockers = []
    for incident, summary, service, source, edge_source in incidents:
        options = owner_map.get(service, [])
        owner = options[0] if len(options) == 1 and options[0]["id"] else None
        blockers.append(
            {
                "incident_id": incident,
                "summary": summary,
                "service_id": service,
                "path": paths[service]["path"] + [incident],
                "source_ids": list(
                    dict.fromkeys(
                        [
                            *paths[service]["source_ids"],
                            source,
                            edge_source,
                            *([owner["source_id"]] if owner else []),
                        ]
                    )
                ),
                "owner": owner,
            }
        )
    checks = store.read(
        "MATCH (v:Verification)-[:VERIFIES]->(r:Release {id:$release}) "
        "RETURN v.id,v.result,v.expires_at,v.source_id,v.check_type LIMIT 201",
        {"release": release},
    )
    relevant = [v for v in checks if v[4] == "integration" and v[2] is not None and v[2] > now]
    if len(checks) > 200:
        missing.append("Verification result budget exceeded")
    if not relevant:
        missing.append("Fresh integration verification required for this release")
    elif {v[1] for v in relevant} != {"pass"}:
        missing.append("Failing or contradictory integration verification")
    history = store.read(
        "MATCH (i:Incident)-[e:AFFECTED]->(s:Service), "
        "(i)-[:HAD_ATTEMPT]->(a:Attempt) WHERE s.id IN $ids "
        "RETURN i.id,s.id,a.id,a.technique,a.outcome,a.source_id LIMIT 101",
        {"ids": ids},
    )
    memory = [
        {
            "incident_id": i,
            "service_id": s,
            "attempt_id": a,
            "technique": t,
            "observed_outcome": o,
            "source_id": src,
            "interpretation": "Historical outcome; present applicability requires verification",
        }
        for i, s, a, t, o, src in history
    ]
    if len(history) > 100:
        missing.append("Historical evidence result budget exceeded")
    source_ids = {src for path in paths.values() for src in path["source_ids"]}
    source_ids.update(src for blocker in blockers for src in blocker["source_ids"])
    source_ids.update(v[3] for v in relevant)
    source_ids.update(
        option["source_id"]
        for options in owner_map.values()
        for option in options
        if option["source_id"]
    )
    source_ids.update(h["source_id"] for h in memory)
    sources = store.read(
        "MATCH (s:Source) WHERE s.id IN $ids RETURN s.id,s.text,s.synthetic,s.version,s.checksum LIMIT 1001",
        {"ids": sorted(source_ids)},
    )
    source_map = {
        id_: {"text": text, "synthetic": synthetic, "version": version, "checksum": checksum}
        for id_, text, synthetic, version, checksum in sources
    }
    if source_ids - source_map.keys():
        missing.append("One or more evidence sources are missing")
    for blocker in blockers:
        blocker["supported"] = all(src in source_map for src in blocker["source_ids"])
    return {
        "paths": list(paths.values()),
        "blockers": blockers,
        "missing_checks": sorted(set(missing)),
        "memory": memory,
        "sources": source_map,
        "expires_at": min((v[2] for v in relevant), default=None),
    }


class Investigator:
    def __init__(self, store, clock=time.time):
        self.store, self.clock = store, clock

    def assess(self, release, key, reset_timings=True):
        start = time.perf_counter()
        with self.store.serialized():
            if reset_timings:
                self.store.timings.clear()
            marker = len(self.store.timings)
            report_id = hashlib.sha256((release + "\0" + key).encode()).hexdigest()
            previous = self.store.read(
                "MATCH (a:Assessment {id:$id}) RETURN a.payload", {"id": report_id}
            )
            if previous:
                return self._fresh(json.loads(previous[0][0]))
            state = self.store.state()
            if state["dirty"]:
                raise ValueError("Interrupted domain mutation requires recovery")
            evidence = snapshot(self.store, release, int(self.clock()))
            # This is explicitly deterministic core automation, not a model agent run.
            tasks = []
            for blocker in evidence["blockers"]:
                if (
                    not blocker["owner"]
                    or "One or more evidence sources are missing" in evidence["missing_checks"]
                ):
                    continue
                task_key = (
                    "blocker-"
                    + hashlib.sha256((release + "\0" + blocker["incident_id"]).encode()).hexdigest()
                )
                existing_task = self.store.read(
                    "MATCH (t:Task {id:$id}) RETURN t.id", {"id": task_key}
                )
                if existing_task:
                    tasks.append(task_key)
                    continue
                payload = {"kind": "task", "id": task_key, "release": release, "blocker": blocker}

                self.store.journal(task_key, payload, lambda p=payload: persist_task(self.store, p))
                tasks.append(task_key)
            state = self.store.state()
            status = verdict(
                [b for b in evidence["blockers"] if b["supported"]], evidence["missing_checks"]
            )
            query_times = self.store.timings[marker:]
            report = {
                "id": report_id,
                "release_id": release,
                "verdict": status,
                "mode": "deterministic-core",
                "agent_run": "not configured",
                "synthetic": True,
                "generation": state["generation"],
                "revision": state["revision"],
                "policy_version": POLICY_VERSION,
                "assessed_at": int(self.clock()),
                "task_ids": tasks,
                **evidence,
                "timing": {
                    "graph_client_ms": sum(q["client_ms"] for q in query_times),
                    "graph_server_ms": sum(q["server_ms"] for q in query_times),
                    "query_count": len(query_times),
                    "model_ms": None,
                    "scope": "investigation and actions, excluding assessment persistence/status read",
                },
            }
            self.store.write(
                "MATCH (r:Release {id:$release}) MERGE (a:Assessment {id:$id}) "
                "SET a.payload=$payload,a.created_at=$now MERGE (a)-[:FOR_RELEASE]->(r)",
                {
                    "id": report_id,
                    "release": release,
                    "payload": json.dumps(report),
                    "now": time.time(),
                },
            )
            response = self._fresh(report)
            total = (time.perf_counter() - start) * 1000
            all_queries = self.store.timings[marker:]
            client_ms = sum(q["client_ms"] for q in all_queries)
            response["request_timing"] = {
                "wall_ms": total,
                "graph_client_ms": client_ms,
                "graph_server_ms": sum(q["server_ms"] for q in all_queries),
                "other_application_ms": max(0, total - client_ms),
                "model_ms": None,
            }
            return response

    def _fresh(self, report):
        state = self.store.state()
        status, reason = effective_status(report, state, int(self.clock()))
        return {
            **report,
            "effective_status": status,
            "freshness_reason": reason,
            "current_revision": state["revision"],
            "checked_at": int(self.clock()),
        }

    def latest(self, release):
        with self.store.serialized():
            rows = self.store.read(
                "MATCH (a:Assessment)-[:FOR_RELEASE]->(:Release {id:$release}) "
                "RETURN a.payload ORDER BY a.created_at DESC LIMIT 1",
                {"release": release},
            )
            if not rows:
                return None
            return self._fresh(json.loads(rows[0][0]))
