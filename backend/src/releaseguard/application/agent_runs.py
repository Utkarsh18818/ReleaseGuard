"""Canonical run checkpoints in FalkorDB, separate from domain revisions."""

import json
import time


class AgentRuns:
    def __init__(self, store, on_save=None):
        self.store = store
        self.on_save = on_save

    def get(self, id):
        with self.store.serialized():
            rows = self.store.read("MATCH (a:AgentRun {id:$id}) RETURN a.payload", {"id": id})
            return json.loads(rows[0][0]) if rows else None

    def save(self, run):
        with self.store.serialized():
            self.store.write(
                "MATCH (r:Release {id:$release}) MERGE (a:AgentRun {id:$id}) "
                "SET a.payload=$payload,a.updated_at=$now MERGE (a)-[:FOR_RELEASE]->(r)",
                {
                    "release": run["release_id"],
                    "id": run["id"],
                    "payload": json.dumps(run),
                    "now": time.time(),
                },
            )
        if self.on_save:
            self.on_save(run)

    def latest(self, release):
        with self.store.serialized():
            rows = self.store.read(
                "MATCH (a:AgentRun)-[:FOR_RELEASE]->(:Release {id:$release}) "
                "RETURN a.payload ORDER BY a.updated_at DESC LIMIT 1",
                {"release": release},
            )
            return json.loads(rows[0][0]) if rows else None
