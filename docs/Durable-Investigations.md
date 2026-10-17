# Durable investigations — October 17, 2026

## What changed

Agent HTTP requests now persist an `InvestigationJob` in FalkorDB and return HTTP 202. A Linux RQ worker executes the existing bounded investigator/verifier pipeline. A separate dispatcher reconciles queued/running graph intents every five seconds. Redis owns delivery metadata; FalkorDB owns request identity, progress, model checkpoints, findings, policy results and tasks.

The UI polls a persisted timeline: queued → running → investigating → awaiting_verifier → verifying → acting → terminal outcome. A reload does not cancel the worker. Model/graph failures remain explicit. Read-time freshness and deterministic action authority are unchanged.

The queue dependency addresses observed 40–51 second HTTP/model waits and interrupted-run recovery. No additional agent framework was introduced. RQ 2.11.0 and croniter 6.2.4 are locked. [RQ worker serialization](https://python-rq.org/docs/workers/) and [unique job behavior](https://python-rq.org/docs/) informed the adapter. Delivery uses JSON and passes only an opaque graph-job identifier, with an allowlisted function.

## Recovery and bounds

- Persist dispatch intent before enqueue. A deterministic delivery ID plus RQ uniqueness handles acknowledgement loss. The dispatcher can redeliver missing/failed transport records from the graph.
- Namespace queue names and job IDs by configured local/cloud target and graph. Integration tests exposed the original global RQ-ID collision; this was fixed before rollout. This is transport namespacing, not authenticated tenant isolation.
- Maximum three delivery attempts; agent model budget stays five admitted calls and ten tool calls, including replay/recovery. Transient provider failure permits one immediate bounded recovery attempt in the worker; it cannot reset model counters.
- Save native interaction cursor, sanitized model response and tool-call results. Recovery reuses a saved response and completed reads rather than starting the investigation again. A call interrupted before its response is saved may consume budget without a known result.
- Save the acting stage before policy publication. If a process exits after assessment commit but before run acknowledgement, recovery reads the committed assessment without another model call or duplicate task.
- RQ imposes a 180-second work-horse timeout. The agent has its existing per-invocation 90-second admission deadline. These are different bounds. Dead-worker transport recovery depends on RQ registry maintenance; it is not instant failover.
- API, worker and dispatcher run on Linux with the same lock directory. Do not mutate the active graph from a Windows CLI while these processes are running: Windows and Linux file locks are not an established shared writer boundary. Use the container CLI instead.

## Reproducible startup

From the repository root, install Python 3.12 dependencies and configure the ignored root `.env` using `.env.example`. Keep Gemini/cloud credentials out of the repository. On a fresh machine, create a Python 3.12 venv first; the workspace's existing venv uses a bundled runtime.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe environment/prepare-secrets.py
.\.venv\Scripts\python.exe environment/prepare-build.py
wsl -d Ubuntu -u root -- service docker start
wsl -d Ubuntu -u root -- docker compose --env-file /mnt/a/ReleaseGuard/.local/.env -f /mnt/a/ReleaseGuard/environment/jobs.compose.yaml build api
wsl -d Ubuntu -u root -- docker compose --env-file /mnt/a/ReleaseGuard/.local/.env -f /mnt/a/ReleaseGuard/environment/jobs.compose.yaml up -d
```

The cloud graph must already contain the synthetic fixture. On an empty configured graph, run the container CLI after startup:

```powershell
wsl -d Ubuntu -u root -- docker compose --env-file /mnt/a/ReleaseGuard/.local/.env -f /mnt/a/ReleaseGuard/environment/jobs.compose.yaml exec api python -m releaseguard.cli seed
```

Open http://127.0.0.1:8000 and choose **Review release**. `POST /api/releases/checkout-v2.4/agent-investigations` takes `{ "request_key": "review-1" }`; poll `/api/jobs/<returned-id>`. The latest job is also available at `/api/releases/checkout-v2.4/jobs/latest`. Graph-policy-only assessment remains a separate operation in Demo lab.

The application image contains only staged code, fixtures and dependency metadata. This avoids an observed NTFS cache-xattr build error and keeps `.env`, history, local data and outputs outside the image. Python and Redis base images are pinned by digest. API/queue ports bind only to localhost; internal Redis is password protected, noeviction, AOF everysec, with a persistent volume. This does not establish power-loss or backup recovery guarantees.

For explicit local operation, start the existing graph Compose service and add `-f /mnt/a/ReleaseGuard/environment/jobs.local.yaml` after the jobs Compose file on all up/exec commands. This joins the local graph network and overrides the database target. Cloud failures do not silently select local storage. Change A-drive paths to match a different checkout.

## Validation evidence

Dataset: synthetic Northstar fixture (six services, Checkout → Payments → Ledger, ownership, incidents, verification, failed attempts and source checksums). API/worker run Python 3.12 on Linux Docker/WSL; local graph uses the pinned existing FalkorDB image. Operational Redis uses the pinned official Redis 8 image. Gemini model: 3.8 Flash.

Measurement uses `perf_counter` around HTTP intake/model/database operations; database server time is from actual query statistics and is included in client time. Individual smoke-test samples are not a controlled latency benchmark. The older synchronous sample used cloud and a Ready state; current local samples use a Blocked state, so no speedup ratio or model-performance improvement is claimed.

| Sample | Measured result |
|---|---|
| Previous synchronous native workflow, Oct 15 | 50,636.85 ms wall; 45,938.20 ms model/API; Ready |
| Queued local API acceptance, Oct 17 | HTTP 202 in 52.66 ms; completed later in worker |
| Same queued local main workflow | Blocked; 39,604.34 ms execution; 39,258.38 ms model/API; 171.27 ms graph client; 11.80 ms graph server (subset of client); 174.70 ms other application |
| Isolated live Linux RQ validation | Blocked; 52,378.30 ms execution; 51,870.63 ms model/API; 246.59 ms graph client; 261.08 ms other application; four model calls, seven tool calls, one open Money-owned blocker |
| Reconnected cloud API intake | HTTP 202 in 5,057.18 ms; returned while worker was running |
| Reconnected cloud worker | Ready at preserved revision 3; 50,418.94 ms execution; 43,738.40 ms model/API; 4,860.24 ms graph client; 21.83 ms graph server (subset); 1,820.30 ms other application |
| Redis graceful restart | Same queued delivery ID and JSON arguments present before/after restart |

Execution timing excludes the last checkpoint write and final freshness read. Progress writes are included. Queue wait is separate: the isolated case waited while the validation worker was being started and is not a service latency benchmark. Model/API time remains the dominant measured cost; moving work off HTTP improves interaction behavior, not model speed.

Raw files: `outputs/configuration/background-live-intake.json`, `background-live-result.json`, `background-api-intake.json`, `background-api-result.json`, `queue-before-restart.json`, and `queue-after-restart.json`.

Cloud evidence: `cloud-background-intake.json` and `cloud-background-result.json`. Cloud intake was much slower than the local sample; serial graph operations and worker/domain-lock contention remain candidates for measurement. Do not present the local 53 ms sample as cloud acceptance latency.

**48 tests pass** against real local FalkorDB and authenticated Redis, including dispatch outage/recovery, enqueue/mark gap, transport-record loss, duplicate delivery, delivery-budget exhaustion, source/ID/freshness gates and actual process exits. One child exits immediately after a model response is saved; another exits after assessment commit. Recovery completes without repeated reads/model calls or duplicate tasks. Scripted model responses in failure-injection tests establish safety/recovery behavior, not model quality. Live Gemini/RQ runs separately establish the actual tool workflow. Existing Starlette HTTPX deprecation warning remains. Ruff and dependency checks pass; the application image/wheel builds.

Evidence for this original checkpoint: `outputs/configuration/background-tests.xml`. Subsequent approved local Chromium visual/interaction checks and the redesigned UI are documented in [UI review](UI-Redesign-Review.md); the built-in browser startup problem was bypassed with user permission.

## Cloud connection incident

The saved cloud hostname initially failed ordinary DNS while Google API DNS worked. After the user reported the instance Healthy, the same hostname resolved again. Authentication succeeded and the original cloud graph remained at revision 3 with its original generation and release. No cloud data was replaced. The API and worker were then switched back from the explicitly selected local validation runtime to cloud. See `cloud-reconnected-oct17.json` and cloud background-check artifacts.

An optional external DNS lookup was rejected by automatic approval review to avoid disclosing the hostname to a third party. It was not executed; ordinary local DNS was sufficient once the instance became reachable. Browser control also failed before page access, so account state was reported by the user and connection state independently checked through the official client.

## Remaining limits and next work

One active worker/writer deployment remains the boundary; this is not distributed fencing or HA. Redis/fsync is not a backup plan. Full work-horse kill/recovery timing under every network/acknowledgement interleaving is not proven. There is no authenticated multi-tenant API or public deployment. Provider retries may still exhaust the five-call budget. Visual QA and a polished connected-evidence presentation remain unfinished.

October 17 follow-up: the evidence/timeline redesign and live Ready provider check are in [UI review](UI-Redesign-Review.md). Failed runs remain in the evidence. See [submission readiness](Submission-Readiness.md) for remaining handoff gates.
