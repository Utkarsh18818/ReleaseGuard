"""Local frontend preview: current source assets, read-only proxy to the Linux API.

Run python -m uvicorn environment.preview:app --host 127.0.0.1 --port 8001.
This process never opens FalkorDB or performs a graph mutation.
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=ROOT / "backend/src/releaseguard/web"), name="assets")
BACKEND = os.environ.get("RELEASEGUARD_PREVIEW_API", "http://127.0.0.1:8000").rstrip("/")


@app.get("/")
def index():
    return FileResponse(ROOT / "backend/src/releaseguard/web/index.html")


@app.get("/demo-media/{filename}")
def media(filename: str):
    types = {"demo-preview.mp4": "video/mp4", "demo-poster.jpg": "image/jpeg",
             "ReleaseGuard-demo.mp4": "video/mp4", "captions.vtt": "text/vtt"}
    if filename not in types:
        raise HTTPException(404)
    return FileResponse(ROOT / "demo" / filename, media_type=types[filename])


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api(path: str, request: Request):
    if request.method != "GET":
        return JSONResponse(status_code=403, content={"detail": "Local visual preview is read-only. Use the working app at localhost:8000 to start a review."})
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(BACKEND + "/api/" + path)
        if path == "health" and response.status_code == 200:
            return JSONResponse({**response.json(), "visual_preview": True, "demo_enabled": False})
        return Response(content=response.content, status_code=response.status_code,
                        media_type=response.headers.get("content-type", "application/json"))
    except httpx.HTTPError:
        return JSONResponse(status_code=503, content={"detail": "Start the existing Linux API at localhost:8000 to load live evidence. Video playback is available offline."})
