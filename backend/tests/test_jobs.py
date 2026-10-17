"""Integration tests use real FalkorDB and authenticated operational Redis."""

import os
import subprocess
import sys
from dataclasses import replace

import pytest
from releaseguard.adapters.queue import DeliveryQueue
from releaseguard.application.agent_investigation import AgentInvestigator
from releaseguard.application.jobs import InvestigationJobs
from releaseguard.worker import perform
from test_agent import ScriptedProvider, proposal


def test_durable_intake_duplicate_delivery_and_noop_replay(store):
    queue = DeliveryQueue(store.settings)
    jobs = InvestigationJobs(store, queue)
    job = jobs.submit("checkout-v2.4", "same")
    assert jobs.submit("checkout-v2.4", "same")["id"] == job["id"]
    assert queue.queue.count == 1
    assert queue.queue.fetch_job(job["delivery_id"]).args == [job["id"]]
    perform(job["id"], settings=store.settings, provider=ScriptedProvider())
    result = jobs.get(job["id"])
    assert result["state"] == "completed"
    assert [e["stage"] for e in result["events"]][:2] == ["queued", "running"]
    assert "verifying" in [e["stage"] for e in result["events"]]
    perform(job["id"], settings=store.settings, provider=ScriptedProvider())
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]
    queue.queue.delete(delete_jobs=True)


def test_dispatch_failure_recovers_saved_intent(store):
    bad = DeliveryQueue(replace(store.settings, queue_port=1))
    jobs = InvestigationJobs(store, bad)
    job = jobs.submit("checkout-v2.4", "outage")
    assert job["state"] == "queued" and "dispatch_error" in job
    real = DeliveryQueue(store.settings)
    recovered = InvestigationJobs(store, real)
    recovered.reconcile()
    assert real.queue.count == 1
    assert "dispatch_error" not in recovered.get(job["id"])
    recovered.reconcile()
    assert real.queue.count == 1
    real.queue.delete(delete_jobs=True)


def test_enqueue_mark_gap_and_lost_delivery_recovery(store):
    queue = DeliveryQueue(store.settings)
    jobs = InvestigationJobs(store, queue)
    job = jobs.submit("checkout-v2.4", "gap")
    # Equivalent durable state after enqueue acknowledgement is lost.
    with store.serialized():
        job.pop("delivery_id")
        job["dispatches"] = 0
        jobs.save(job)
    jobs.reconcile()
    assert queue.queue.count == 1
    # Actual transport metadata loss: remove this disposable test job, preserve graph intent.
    queue.queue.fetch_job(job["id"] + "-0").delete(remove_from_queue=True)
    jobs.reconcile()
    assert queue.queue.count == 1
    queue.queue.delete(delete_jobs=True)


def test_saved_model_turn_resumes_without_repeating_read(store):
    def crash(run):
        if run.get("saved_investigator_turn") and not run["trace"]:
            raise SystemExit("Injected worker death after saved model response")

    with pytest.raises(SystemExit):
        AgentInvestigator(store, ScriptedProvider(), progress=crash).investigate(
            "checkout-v2.4", "crash"
        )
    resumed = AgentInvestigator(
        store,
        ScriptedProvider(
            [
                ("submit_findings", proposal()),
                ("submit_review", {"accept": True, "reason": "supported"}),
            ]
        ),
    ).investigate("checkout-v2.4", "crash", recover=True)
    assert resumed["state"] == "completed"
    assert resumed["model_calls"] == 3
    assert len(resumed["trace"]) == 1
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]


def test_unknown_resume_and_delivery_budget_are_explicit(store):
    queue = DeliveryQueue(store.settings)
    jobs = InvestigationJobs(store, queue)
    with pytest.raises(ValueError, match="No resumable"):
        jobs.submit("checkout-v2.4", "missing", resume=True)
    job = jobs.submit("checkout-v2.4", "exhausted")
    queue.queue.fetch_job(job["delivery_id"]).delete(remove_from_queue=True)
    with store.serialized():
        job["attempts"] = 3
        jobs.save(job)
    jobs.reconcile()
    assert jobs.get(job["id"])["state"] == "incomplete"
    queue.queue.delete(delete_jobs=True)


def test_actual_process_exit_resumes_saved_turn(store):
    env = {**os.environ, "FALKORDB_GRAPH": store.name}
    code = """
import os,sys
from pathlib import Path
sys.path.insert(0,'backend/tests')
from test_agent import ScriptedProvider
from releaseguard.config import Settings
from releaseguard.adapters.falkordb import GraphStore
from releaseguard.application.agent_investigation import AgentInvestigator
def exit_after_response(run):
    if run.get('saved_investigator_turn'):
        os._exit(27)
store=GraphStore(Settings.load(), Path(sys.argv[1]))
AgentInvestigator(store,ScriptedProvider(),progress=exit_after_response).investigate('checkout-v2.4','process-exit')
"""
    child = subprocess.run([sys.executable, "-c", code, str(store.lock_path.parent)], env=env)
    assert child.returncode == 27
    resumed = AgentInvestigator(
        store,
        ScriptedProvider(
            [
                ("submit_findings", proposal()),
                ("submit_review", {"accept": True, "reason": "supported"}),
            ]
        ),
    ).investigate("checkout-v2.4", "process-exit", recover=True)
    assert resumed["state"] == "completed" and resumed["model_calls"] == 3
    assert len(resumed["trace"]) == 1
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]


def test_process_exit_after_assessment_commit_recovers_without_model(store):
    env = {**os.environ, "FALKORDB_GRAPH": store.name}
    code = """
import os,sys
from pathlib import Path
sys.path.insert(0,'backend/tests')
from test_agent import ScriptedProvider
from releaseguard.config import Settings
from releaseguard.adapters.falkordb import GraphStore
from releaseguard.application.agent_investigation import AgentInvestigator
class ExitAfterCommit(GraphStore):
    def write(self, query, params=None):
        result=super().write(query,params)
        if 'MERGE (a:Assessment' in query:
            os._exit(28)
        return result
store=ExitAfterCommit(Settings.load(),Path(sys.argv[1]))
AgentInvestigator(store,ScriptedProvider()).investigate('checkout-v2.4','commit-exit')
"""
    child = subprocess.run([sys.executable, "-c", code, str(store.lock_path.parent)], env=env)
    assert child.returncode == 28

    class NoMoreCalls:
        def interact(self, *args, **kwargs):
            raise AssertionError("Committed assessment must not call the provider again")

    resumed = AgentInvestigator(store, NoMoreCalls()).investigate(
        "checkout-v2.4", "commit-exit", recover=True
    )
    assert resumed["state"] == "completed" and resumed["assessment"]["verdict"] == "Blocked"
    assert resumed["model_calls"] == 3
    assert store.read("MATCH (t:Task) RETURN count(t)") == [[1]]
