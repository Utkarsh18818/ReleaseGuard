import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError

from releaseguard.adapters.falkordb import GraphStore
from releaseguard.adapters.gemini import GeminiProvider
from releaseguard.adapters.queue import DeliveryQueue
from releaseguard.application.agent_investigation import AgentInvestigator
from releaseguard.application.ingestion import load_dataset, seed
from releaseguard.application.investigation import Investigator
from releaseguard.application.jobs import InvestigationJobs
from releaseguard.application.mutations import apply_event
from releaseguard.application.public_demo import PublicReviewLimit, submit_public_review
from releaseguard.config import ROOT, Settings
from releaseguard.domain.models import AssessmentRequest, DemoEvent


def create_app(settings: Settings | None = None):
    settings = settings or Settings.load()
    store = GraphStore(settings)
    investigator = Investigator(store)
    app = FastAPI(title="ReleaseGuard", version="0.1.0")
    app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "web"), name="assets")
    app.state.store = store

    @app.exception_handler(PublicReviewLimit)
    def public_limit(request, exc):
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.middleware("http")
    async def public_boundary(request, call_next):
        if settings.public_demo and request.method not in {"GET", "HEAD"}:
            allowed = "/api/releases/checkout-v2.4/agent-investigations"
            if request.method != "POST" or request.url.path != allowed:
                return JSONResponse(status_code=403, content={"detail": "Editing is disabled in the shared public demo"})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.exception_handler(RedisError)
    def graph_error(request, exc):
        logging.getLogger("releaseguard").error("Graph unavailable: %s", type(exc).__name__)
        return JSONResponse(
            status_code=503,
            content={
                "error": "graph_unavailable",
                "detail": "FalkorDB unavailable; no fallback verdict",
            },
        )

    @app.exception_handler(ValueError)
    def validation_error(request, exc):
        return JSONResponse(status_code=409, content={"error": "invalid_state", "detail": str(exc)})

    @app.get("/")
    def index():
        return FileResponse(Path(__file__).parent / "web" / "index.html")

    @app.get("/demo-media/{filename}")
    def demo_media(filename: str):
        allowed = {
            "demo-preview.mp4": "video/mp4", "demo-poster.jpg": "image/jpeg",
            "ReleaseGuard-demo.mp4": "video/mp4", "captions.vtt": "text/vtt",
        }
        path = ROOT / "demo" / filename
        if filename not in allowed or not path.is_file():
            raise HTTPException(404, "Unknown demo media")
        return FileResponse(path, media_type=allowed[filename])

    @app.get("/api/health")
    def health():
        store.client.list_graphs()
        return {
            "graph": "reachable",
            "database_target": settings.target,
            "mode": "deterministic-core",
            "llm": "Gemini native graph tools available"
            if settings.gemini_api_key
            else "not configured",
            "demo_enabled": settings.demo_enabled and not settings.public_demo,
            "public_demo": settings.public_demo,
        }

    @app.get("/api/releases")
    def releases():
        with store.serialized():
            return [
                {"id": id_, "name": name}
                for id_, name in store.read("MATCH (r:Release) RETURN r.id,r.name LIMIT 101")
            ]

    @app.post("/api/releases/{release}/assessments")
    def assess(release: str, body: AssessmentRequest):
        return investigator.assess(release, body.request_key)

    @app.post("/api/releases/{release}/agent-investigations", status_code=202)
    def agent_investigate(release: str, body: AssessmentRequest):
        jobs = InvestigationJobs(GraphStore(settings), DeliveryQueue(settings))
        if settings.public_demo:
            return submit_public_review(jobs, release)
        return jobs.submit(release, body.request_key)

    @app.get("/api/releases/{release}/agent-investigations/latest")
    def agent_latest(release: str):
        return AgentInvestigator(GraphStore(settings), GeminiProvider(settings)).latest(release)

    @app.post("/api/releases/{release}/agent-verifier-resume", status_code=202)
    def agent_resume(release: str, body: AssessmentRequest):
        return InvestigationJobs(GraphStore(settings), DeliveryQueue(settings)).submit(
            release, body.request_key, resume=True
        )

    @app.get("/api/jobs/{id}")
    def job_status(id: str):
        job = InvestigationJobs(GraphStore(settings), DeliveryQueue(settings)).get(id)
        if job is None:
            raise HTTPException(404, "Unknown investigation job")
        if job.get("agent_run_id"):
            agent = AgentInvestigator(GraphStore(settings), GeminiProvider(settings))
            run = agent.runs.get(job["agent_run_id"])
            job["run"] = agent._view(run) if run else None
        return job

    @app.get("/api/releases/{release}/jobs/latest")
    def latest_job(release: str):
        return InvestigationJobs(GraphStore(settings), DeliveryQueue(settings)).latest(release)

    @app.get("/api/releases/{release}/latest")
    def latest(release: str):
        return investigator.latest(release)

    @app.get("/api/tasks")
    def tasks():
        with store.serialized():
            rows = store.read(
                "MATCH (t:Task)-[:ASSIGNED_TO]->(o:Team),"
                "(t)-[:BLOCKS]->(r:Release) RETURN t.id,t.status,o.name,r.id,t.evidence LIMIT 201"
            )
            return [
                {
                    "id": id_,
                    "status": status,
                    "owner": owner,
                    "release_id": release,
                    "evidence": evidence,
                }
                for id_, status, owner, release, evidence in rows
            ]

    def require_demo():
        if not settings.demo_enabled:
            raise HTTPException(403, "Synthetic demo mutations are disabled")

    @app.post("/api/demo/seed")
    def demo_seed():
        require_demo()
        return {"applied": seed(store, load_dataset(ROOT / "fixtures" / "northstar.json"))}

    @app.post("/api/demo/events")
    def event(body: DemoEvent):
        require_demo()
        return apply_event(store, body)

    return app


app = create_app()
