from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from releaseguard.adapters.queue import DeliveryQueue
from releaseguard.api import create_app
from releaseguard.application.jobs import InvestigationJobs
from releaseguard.application.public_demo import PublicReviewLimit, submit_public_review


def test_public_budget_reuses_jobs_and_survives_new_admission_objects(store):
    queue = DeliveryQueue(store.settings)
    now = [2000000000]
    try:
        jobs = InvestigationJobs(store, queue, clock=lambda: now[0])
        first = submit_public_review(jobs, "checkout-v2.4", clock=lambda: now[0])
        assert submit_public_review(jobs, "checkout-v2.4", clock=lambda: now[0])["id"] == first["id"]
        for index in range(12):
            current = jobs.latest("checkout-v2.4")
            with store.serialized():
                current["state"] = "incomplete"
                jobs.save(current)
            assert submit_public_review(jobs, "checkout-v2.4", clock=lambda: now[0])["id"] == current["id"]
            now[0] += 601
            jobs = InvestigationJobs(store, queue, clock=lambda: now[0])
            if index < 11:
                submit_public_review(jobs, "checkout-v2.4", clock=lambda: now[0])
        with pytest.raises(PublicReviewLimit):
            submit_public_review(jobs, "checkout-v2.4", clock=lambda: now[0])
        with pytest.raises(ValueError, match="only Checkout"):
            submit_public_review(jobs, "unknown", clock=lambda: now[0])
    finally:
        queue.queue.delete(delete_jobs=True)


def test_public_http_disables_editing_but_queues_one_real_shared_job(store):
    queue = DeliveryQueue(store.settings)
    try:
        client = TestClient(create_app(replace(store.settings, public_demo=True, demo_enabled=True)))
        health = client.get("/api/health").json()
        assert health["public_demo"] and not health["demo_enabled"]
        for path in ("/api/demo/seed", "/api/demo/events", "/api/releases/checkout-v2.4/assessments",
                     "/api/releases/checkout-v2.4/agent-verifier-resume"):
            assert client.post(path, json={"request_key": "denied"}).status_code == 403
        endpoint = "/api/releases/checkout-v2.4/agent-investigations"
        first = client.post(endpoint, json={"request_key": "visitor-one"})
        second = client.post(endpoint, json={"request_key": "visitor-two"})
        assert first.status_code == second.status_code == 202
        assert first.json()["id"] == second.json()["id"]
        assert queue.queue.count == 1
        assert client.get("/api/jobs/" + first.json()["id"]).json()["state"] == "queued"
    finally:
        queue.queue.delete(delete_jobs=True)
