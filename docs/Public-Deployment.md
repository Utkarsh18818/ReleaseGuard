# Public judge demo deployment

**Verified live URL: https://releaseguard-7hx8.onrender.com/**

This is a bounded, shared synthetic demo, not a production or multi-tenant service. Render reported successful deployment of commit `e2e1001c4f5345210e786de669ce256946770e45` on October 18. Public UI and health checks confirmed the actual FalkorDB Cloud connection, connected evidence, saved decision and Money-owned task.

## Introduction rollout — October 18

Manual deploy `dep-db9ui9e1egvs738m9t50` succeeded at 03:02 AM IST. The approved third visual direction is live: a responsive product introduction, muted recorded preview, captioned full demo dialog and an Open workspace entry into the existing release review. The demo footage is explicitly historical and synthetic.

Public HTTP verification passed for eight static/media routes, including HTTP 206 byte ranges on both MP4 files. Cloud health was reachable, the current graph-backed assessment was Blocked, and public seed mutation returned HTTP 403. Browser verification confirmed the introduction, actual full-video playback (159.25 seconds), English track, dialog close/focus return, and workspace loading with three connected services, five sources, two historical attempts and the Money-owned blocker. This revision starts its own synthetic graph; no new native Gemini investigation was run during this UI rollout. The October 17 native execution below remains evidence of that earlier revision.

The focused media route test passed, Ruff and diff checks passed, and the local responsive/accessibility checks are recorded in `design-qa.md`. No latency improvement is claimed. Private deployment checks and screenshot are retained in `.local/submission/intro-production-checks.json` and `.local/submission/intro-production.png`.

## Runtime

Render Docker web service, one instance, Free plan, repository root context, Dockerfile `environment/hosted.Dockerfile`, port supplied by Render. The container runs one FastAPI process, one RQ worker, a dispatcher and a loopback-only password-protected Redis process. Its supervisor shuts down the service if any child exits. No paid service or persistent disk is required for this evaluation layout.

FalkorDB Cloud retains all evidence, tasks, assessments, checkpoints and public admission counts. Redis is disposable delivery metadata: graph intents are reconciled after restart. All cooperating writers share one container lock directory. Do not scale this to multiple instances. New Git commit revisions use different `releaseguard_public_<commit-prefix>` graphs to avoid concurrent writers during rolling code deploys; these demo graphs are distinct from the original working graph. Same-revision overlapping replicas remain unsupported. A new code revision starts a fresh synthetic demo; earlier graph data remains in FalkorDB, not automatically migrated or deleted.

## Hosting settings

Choose Docker, branch `main`, Free instance, region nearest the configured graph, Dockerfile path `environment/hosted.Dockerfile`, health-check path `/api/health`. Disable automatic deploys while preparing the submission. Do not enable multiple instances or paid features.

Set these **runtime secrets** in the hosting dashboard, not Git:

- `FALKORDB_TARGET=cloud`
- `FALKORDB_CLOUD_HOST`, `FALKORDB_CLOUD_PORT`, `FALKORDB_CLOUD_USERNAME`, `FALKORDB_CLOUD_PASSWORD`, `FALKORDB_CLOUD_SSL` from the existing synthetic-only instance
- `GEMINI_API_KEY` and optional `GEMINI_MODEL` from the existing local configuration

The hosted service explicitly sets `GEMINI_MODEL=gemini-3.7-flash`. Gemini 3.8 Flash reached the account's 20 requests/day free limit during development. A Flash-Lite trial was rejected by the unchanged historical-evidence gate; it is not used. A 3.7 Flash trial passed locally and then through the public HTTP/worker workflow. This is an explicit hosting configuration, not a hidden model fallback. The earlier video remains labeled evidence of the earlier 3.8 Flash run.

Never print secret values or commit an environment file. This Free FalkorDB endpoint currently uses its documented configured plaintext transport; only synthetic evaluation data is permitted. TLS must remain enabled for any endpoint that supports it. Do not upload production evidence.

## Public boundary

Public reads expose the fictional company and its saved model/tool evidence. Demo events, seed, direct policy writes and verifier-resume are blocked by middleware even if the local demo flag is accidentally enabled. The only public write is a review of the fixed Checkout release. Concurrent/recent clicks return the same job. A graph-persisted reservation permits at most 12 newly admitted reviews per UTC day per deployed graph, each still bounded to five model calls and ten tool calls. A failed reservation can consume a slot. Redeploying new code creates a new graph/budget; this is an evaluation spending bound, not a provider-wide billing cap or authentication.

The interface explains these limits. Real provider failures remain visible. Completed results are retained, not replaced by fabricated responses when the provider fails or the daily limit is reached.

## Availability and limits

[Render Free](https://render.com/docs/free) sleeps after 15 minutes without inbound traffic, restarts with ephemeral local files and can take about a minute to wake. Graph persistence survives those local restarts. This bundled single-container layout is for the hackathon evaluation, not an independently scalable production deployment. Provider quota, graph availability, outbound network rules and the host's 512 MB limit remain deployment checks; none is claimed verified until measured on the service.

## Validation recorded before hosting

52 tests passed against real local FalkorDB/Redis, including public HTTP write denial, shared-job deduplication and the persisted 12-review admission limit. Existing full workflow tests retain their earlier evidence; model failure tests use labeled scripted responses. The deployment image built successfully. Subsequent public reachability and native Gemini validation are recorded below.

The actual bundled image served HTTP 200 for the UI and graph health, retrieved Blocked from an isolated local graph, and rejected a seed mutation with HTTP 403. Measured idle memory after the worker test was 146.6 MiB within a 512 MiB container limit. One real queued Gemini request returned HTTP 429: the job persisted Incomplete with one admitted model call and zero tools; the independently recorded policy decision remained Blocked. This is a verified provider failure, not a successful native agent execution on the new image. Raw private verification: `.local/submission/hosted-layout-live-result.json`.

## Actual public workflow — October 17

The public Review release button queued a real job. It completed **Blocked**, with four admitted model calls, six real graph tools, a separate accepted verifier and no evidence-gate violations. The UI displays the failed-retry warning and qualified historical procedure follow-up. A public attempt to seed data returned HTTP 403. Health returned HTTP 200 with cloud reachable and editing disabled.

| Single hosted sample | Measured value |
| --- | ---: |
| Worker invocation wall time | 89,325.80 ms |
| Model/API time | 31,957.27 ms |
| Graph client time | 20,172.46 ms |
| Graph server time, included in client | 23.56 ms |
| Other application/lock time | 37,196.08 ms |
| Timed graph queries | 104 |
| Queue-to-terminal elapsed time | 91,845.44 ms |

Environment: Render Free Docker, Ohio, 512 MB; remote synthetic-only FalkorDB Cloud; Gemini 3.7 Flash. The browser was polling and a separate verifier script was reading progress. This is one smoke-test observation, not a latency percentile or speed comparison. Stored invocation timing excludes the final checkpoint/freshness read. The long graph round trips and other/lock time warrant a separate controlled polling/contention measurement before any performance claim.

Restarting the isolated local hosted-layout container preserved the same graph-backed job, assessment and revision while replacing its Redis process. This proves that tested terminal-state retention, not every possible hosting crash/recovery interleaving.

The application's 12 admissions/day cap is an upper bound, not a promise of 12 successful reviews: provider per-model request quota can be lower (one review used four requests). Successful reviews are shared for ten minutes. Avoid repeatedly starting reviews merely to keep the service awake; saved evidence and results remain available. Reusing a completed review while its canonical evidence remains fresh is the highest-value next refinement for conserving the free quota.

Private raw verification: `.local/submission/public-deployment-verification.json`, `hosted-layout-restart.json`, `hosted-flash37-result.json`. The public live link is saved on the existing WeMakeDevs submitted entry.
