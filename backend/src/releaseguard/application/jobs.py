"""Durable intake and dispatch reconciliation; no alternative reasoning store."""

import hashlib
import json
import time

from redis.exceptions import RedisError

TERMINAL = {"completed", "rejected", "stale", "incomplete", "failed"}


class InvestigationJobs:
    MAX_DELIVERIES = 3

    def __init__(self, store, queue, clock=time.time):
        self.store, self.queue, self.clock = store, queue, clock

    def get(self, id):
        with self.store.serialized():
            rows = self.store.read(
                "MATCH (j:InvestigationJob {id:$id}) RETURN j.payload", {"id": id}
            )
            return json.loads(rows[0][0]) if rows else None

    def save(self, job):
        job["updated_at"] = self.clock()
        self.store.write(
            "MATCH (r:Release {id:$release}) MERGE (j:InvestigationJob {id:$id}) "
            "SET j.payload=$payload,j.state=$state,j.created_at=$created "
            "MERGE (j)-[:FOR_RELEASE]->(r)",
            {
                "id": job["id"],
                "release": job["release_id"],
                "payload": json.dumps(job),
                "state": job["state"],
                "created": job["created_at"],
            },
        )

    def submit(self, release, key, resume=False):
        id = hashlib.sha256(
            (
                self.store.settings.target
                + "\0"
                + self.store.name
                + "\0"
                + release
                + "\0job\0"
                + key
                + str(resume)
            ).encode()
        ).hexdigest()
        with self.store.serialized():
            if not self.store.read("MATCH (r:Release {id:$id}) RETURN r.id", {"id": release}):
                raise ValueError("Unknown release")
            job = self.get(id)
            if not job:
                if resume:
                    from releaseguard.application.agent_runs import AgentRuns

                    run_id = hashlib.sha256((release + "\0agent\0" + key).encode()).hexdigest()
                    run = AgentRuns(self.store).get(run_id)
                    if (
                        not run
                        or run["state"] != "incomplete"
                        or "proposal" not in run
                        or run["model_calls"] >= 5
                    ):
                        raise ValueError("No resumable verifier handoff or call budget exhausted")
                job = {
                    "id": id,
                    "release_id": release,
                    "request_key": key,
                    "resume": resume,
                    "state": "queued",
                    "attempts": 0,
                    "dispatches": 0,
                    "created_at": self.clock(),
                    "events": [{"stage": "queued", "at": self.clock()}],
                }
                self.save(job)  # intent survives failure before/after enqueue
        self.dispatch(id)
        return self.get(id)

    def dispatch(self, id):
        with self.store.serialized():
            job = self.get(id)
            if not job or job["state"] in TERMINAL:
                return
            try:
                status = self.queue.status(job.get("delivery_id", "not-dispatched"))
                if status in {"queued", "started", "scheduled", "deferred"}:
                    return
                if job["attempts"] >= self.MAX_DELIVERIES or (
                    status is not None and job["dispatches"] >= self.MAX_DELIVERIES
                ):
                    job.update(state="incomplete", error="Delivery recovery budget exhausted")
                    self.save(job)
                    return
                # A deterministic next delivery ID closes the enqueue/mark crash gap.
                if status is not None or not job.get("delivery_id"):
                    job.update(
                        delivery_id=id + "-" + str(job["dispatches"]),
                        dispatches=job["dispatches"] + 1,
                    )
                    self.save(job)
                delivery = job["delivery_id"]
                self.queue.enqueue(id, delivery)
                job.update(state="queued")
                job.pop("dispatch_error", None)
            except (RedisError, OSError):
                job["dispatch_error"] = "Operational queue unavailable; intent saved for recovery"
            self.save(job)

    def reconcile(self):
        with self.store.serialized():
            rows = self.store.read(
                "MATCH (j:InvestigationJob) WHERE j.state IN ['queued','running'] "
                "RETURN j.id LIMIT 101"
            )
        for (id,) in rows[:100]:
            self.dispatch(id)
        return len(rows[:100])

    def latest(self, release):
        with self.store.serialized():
            rows = self.store.read(
                "MATCH (j:InvestigationJob)-[:FOR_RELEASE]->(:Release {id:$release}) "
                "RETURN j.payload ORDER BY j.created_at DESC LIMIT 1",
                {"release": release},
            )
            return json.loads(rows[0][0]) if rows else None
