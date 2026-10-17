"""One Linux RQ worker and a bounded graph-intent reconciler."""

import argparse
import time

from rq import Worker

from releaseguard.adapters.falkordb import GraphStore
from releaseguard.adapters.gemini import GeminiProvider
from releaseguard.adapters.queue import DeliveryQueue, connection
from releaseguard.application.agent_investigation import AgentInvestigator
from releaseguard.application.jobs import TERMINAL, InvestigationJobs
from releaseguard.config import Settings


def perform(id, settings=None, provider=None):
    settings = settings or Settings.load()
    store = GraphStore(settings)
    jobs = InvestigationJobs(store, DeliveryQueue(settings))
    with store.serialized():
        job = jobs.get(id)
        if not job or job["state"] in TERMINAL:
            return
        if job["attempts"] >= jobs.MAX_DELIVERIES:
            job.update(state="incomplete", error="Delivery budget exhausted")
            jobs.save(job)
            return
        job.update(state="running", attempts=job["attempts"] + 1)
        job["events"].append({"stage": "running", "at": time.time()})
        jobs.save(job)

    def progress(run):
        with store.serialized():
            current = jobs.get(id)
            stage = run["state"]
            if current["events"][-1]["stage"] != stage:
                current["events"].append({"stage": stage, "at": time.time()})
            current.update(
                agent_run_id=run["id"], model_calls=run["model_calls"], tool_calls=run["tool_calls"]
            )
            jobs.save(current)

    agent = AgentInvestigator(store, provider or GeminiProvider(settings), progress=progress)
    try:
        run = agent.investigate(
            job["release_id"], job["request_key"], resume_verifier=job["resume"], recover=True
        )
        # One transient retry may resume a saved conversation/handoff; total call budget remains five.
        if (
            run["state"] == "incomplete"
            and run.get("retryable")
            and run["model_calls"] < agent.MAX_CALLS
        ):
            run = agent.investigate(job["release_id"], job["request_key"], recover=True)
        with store.serialized():
            current = jobs.get(id)
            current.update(
                state=run["state"],
                agent_run_id=run["id"],
                error=run.get("error"),
                model_calls=run["model_calls"],
                tool_calls=run["tool_calls"],
            )
            if current["events"][-1]["stage"] != run["state"]:
                current["events"].append({"stage": run["state"], "at": time.time()})
            jobs.save(current)
    except Exception as error:
        with store.serialized():
            current = jobs.get(id)
            current.update(state="failed", error="Worker failure: " + type(error).__name__)
            jobs.save(current)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--burst", action="store_true")
    parser.add_argument("--reconcile-only", action="store_true")
    args = parser.parse_args()
    settings = Settings.load()

    def reconcile():
        while True:
            try:
                InvestigationJobs(GraphStore(settings), DeliveryQueue(settings)).reconcile()
            except Exception:
                pass  # intent stays canonical; graph/queue health exposed by API
            time.sleep(5)

    if args.reconcile_only:
        reconcile()
        return
    InvestigationJobs(GraphStore(settings), DeliveryQueue(settings)).reconcile()
    Worker(
        [DeliveryQueue(settings).queue.name],
        connection=connection(settings),
        serializer="json",
        maintenance_interval=10,
    ).work(burst=args.burst)


if __name__ == "__main__":
    main()
