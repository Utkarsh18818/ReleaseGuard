# Public judge demo deployment

This is a bounded, shared synthetic demo, not a production or multi-tenant service. Deployment is being validated; a hosting URL is only verified after the actual service is running.

## Runtime

Render Docker web service, one instance, Free plan, repository root context, Dockerfile `environment/hosted.Dockerfile`, port supplied by Render. The container runs one FastAPI process, one RQ worker, a dispatcher and a loopback-only password-protected Redis process. Its supervisor shuts down the service if any child exits. No paid service or persistent disk is required for this evaluation layout.

FalkorDB Cloud retains all evidence, tasks, assessments, checkpoints and public admission counts. Redis is disposable delivery metadata: graph intents are reconciled after restart. All cooperating writers share one container lock directory. Do not scale this to multiple instances. New Git commit revisions use different `releaseguard_public_<commit-prefix>` graphs to avoid concurrent writers during rolling code deploys; these demo graphs are distinct from the original working graph. Same-revision overlapping replicas remain unsupported. A new code revision starts a fresh synthetic demo; earlier graph data remains in FalkorDB, not automatically migrated or deleted.

## Hosting settings

Choose Docker, branch `main`, Free instance, region nearest the configured graph, Dockerfile path `environment/hosted.Dockerfile`, health-check path `/api/health`. Disable automatic deploys while preparing the submission. Do not enable multiple instances or paid features.

Set these **runtime secrets** in the hosting dashboard, not Git:

- `FALKORDB_TARGET=cloud`
- `FALKORDB_CLOUD_HOST`, `FALKORDB_CLOUD_PORT`, `FALKORDB_CLOUD_USERNAME`, `FALKORDB_CLOUD_PASSWORD`, `FALKORDB_CLOUD_SSL` from the existing synthetic-only instance
- `GEMINI_API_KEY` and optional `GEMINI_MODEL` from the existing local configuration

Never print secret values or commit an environment file. This Free FalkorDB endpoint currently uses its documented configured plaintext transport; only synthetic evaluation data is permitted. TLS must remain enabled for any endpoint that supports it. Do not upload production evidence.

## Public boundary

Public reads expose the fictional company and its saved model/tool evidence. Demo events, seed, direct policy writes and verifier-resume are blocked by middleware even if the local demo flag is accidentally enabled. The only public write is a review of the fixed Checkout release. Concurrent/recent clicks return the same job. A graph-persisted reservation permits at most 12 newly admitted reviews per UTC day per deployed graph, each still bounded to five model calls and ten tool calls. A failed reservation can consume a slot. Redeploying new code creates a new graph/budget; this is an evaluation spending bound, not a provider-wide billing cap or authentication.

The interface explains these limits. Real provider failures remain visible. Completed results are retained, not replaced by fabricated responses when the provider fails or the daily limit is reached.

## Availability and limits

[Render Free](https://render.com/docs/free) sleeps after 15 minutes without inbound traffic, restarts with ephemeral local files and can take about a minute to wake. Graph persistence survives those local restarts. This bundled single-container layout is for the hackathon evaluation, not an independently scalable production deployment. Provider quota, graph availability, outbound network rules and the host's 512 MB limit remain deployment checks; none is claimed verified until measured on the service.

## Validation recorded before hosting

52 tests passed against real local FalkorDB/Redis, including public HTTP write denial, shared-job deduplication and the persisted 12-review admission limit. Existing full workflow tests retain their earlier evidence; model failure tests use labeled scripted responses. The deployment image built successfully. Actual hosted reachability and a native Gemini review still require the running hosting service.

The actual bundled image served HTTP 200 for the UI and graph health, retrieved Blocked from an isolated local graph, and rejected a seed mutation with HTTP 403. Measured idle memory after the worker test was 146.6 MiB within a 512 MiB container limit. One real queued Gemini request returned HTTP 429: the job persisted Incomplete with one admitted model call and zero tools; the independently recorded policy decision remained Blocked. This is a verified provider failure, not a successful native agent execution on the new image. Raw private verification: `.local/submission/hosted-layout-live-result.json`.
