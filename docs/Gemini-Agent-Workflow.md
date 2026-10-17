# Gemini graph investigation — October 15, 2026

Historical checkpoint: [October 17 durable workflow report](Durable-Investigations.md) supersedes the synchronous API and missing-dispatch limitations below.

## Implemented behavior

An engineering lead selects a release. The application captures a bounded canonical graph snapshot containing dependency paths, open blockers, ownership, verification coverage and source identifiers. Gemini then chooses actual history/source lookups through allowlisted tools. It submits structured blocker IDs, adverse attempts to avoid, procedures to review, source citations and a next-step category.

The investigator saves its proposal, retrieved tool results, budgets, timing and evidence snapshot in an `AgentRun` node linked to the Release. A separate Gemini verifier invocation rereads that persisted handoff and current evidence. Deterministic verification checks complete blocker coverage, retrieved history IDs, adverse outcomes, citation completeness, source checksums, missing checks, expiry and domain revision. Only accepted, current findings enter the existing deterministic policy and idempotent task pipeline.

This follows the researched [Gemini native function-calling protocol](https://ai.google.dev/gemini-api/docs/function-calling): server-produced function calls are executed locally and their results returned with the interaction ID. Provider-specific handling stays in the adapter. No new agent framework or SDK was added.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `adapters/gemini.py` | Credential-safe Interactions HTTP transport; sanitized native function calls; no hidden thoughts in saved output |
| `domain/agent.py` | Strict schemas for tools, findings and review |
| `application/agent_tools.py` | Parameterized real graph reads constrained to release scope |
| `application/agent_runs.py` | Durable run/checkpoint reads and writes without changing domain revision |
| `application/agent_verification.py` | Deterministic evidence/claim gate |
| `application/agent_investigation.py` | Budgeted investigator, persisted handoff, separate verifier and final policy gate |
| Existing investigation/actions | Current release verdict and idempotent graph task effects |

Model calls occur outside the domain lock. The final freshness check and policy/action stage share that lock. An observed Windows nested-file-lock failure was fixed with thread-local ownership inside the shared process lock. Tests cover nested adapters and exception cleanup; distributed fencing remains unsupported.

## Actual validation

Environment: Windows, Python 3.12.14, official FalkorDB client 1.8.0, cloud Free instance in AWS ap-south-1 (dashboard database version 4.22.0), Gemini 3.8 Flash. Dataset: fictional Northstar fixture, six services, dependency chain Checkout → Payments → Ledger, incident and attempt/source records. No production data.

Each number below is an individual smoke-test sample, not a benchmark or speedup result. Wall time uses Python `perf_counter`; model time wraps HTTP calls, graph client/server times come from the adapter/query statistics. Server time is part of client time, not additive. The successful run exposed a timing collector reset in the policy stage, so its full graph time was not captured. Collection was fixed for later invocations; do not infer a graph performance benefit.

| Live case | Outcome | Wall ms | Model/API ms | Graph client ms | Evidence |
|---|---|---:|---:|---:|---|
| First native attempt | Incomplete; connection timeout; no tools | 16101.11 | 15255.34 | Not fully recorded | `live-agent-run.json` |
| Unreserved final turn | Rejected after 4 turns, 7 real reads, no findings | 41707.74 | 39046.32 | Not fully recorded | `live-agent-run-2.json` |
| Reserved submission turn | Completed Ready on user-resolved incident state; separate verifier accepted; 4 calls / 9 tools | 50636.85 | 45938.20 | Only policy subset recorded | `live-agent-run-3.json` |
| Isolated blocked-case investigator | Persisted awaiting_verifier, 3 calls; zero tasks before review | 29424.24 | 27899.37 | Not fully recorded at handoff | `live-agent-handoff.json` |
| New-process verifier | HTTP 503; Incomplete; zero tasks | 6281.18 end-to-end | 5015.78 for this invocation | 1177.72 before final checkpoint/read | `live-agent-restarted-verifier.json` |
| Explicit saved-verifier retry | HTTP 503; five total calls exhausted; zero tasks | 8175.87 end-to-end | 7158.83 for this invocation | 900.92 before final checkpoint/read | `live-agent-verifier-retry.json` |

Raw evidence is in `outputs/configuration`. The Ready run retrieved historical records and proposed avoiding increased retries because the recorded outcome worsened overload. It proposed reviewing the timeout/circuit-breaker procedure with current validation. Its captured revision was 3, matching the user's resolved incident state. No task creation was needed in that live Ready case. The separate live blocked case did **not** complete because both verifier attempts returned 503; do not claim successful live model-approved blocker creation from it.

**41 tests passed**, one existing Starlette HTTPX deprecation warning, 10.45 seconds, against actual local FalkorDB. These include provider failure, invalid/out-of-scope tools, invented attempt IDs, checksum mismatch, missing checks, expiry, graph mutation during model review, nested lock cleanup, idempotent actions, persistence, and bounded verifier retry. Adversarial provider responses are scripted solely to test safety boundaries; they do not establish Gemini's answer quality. Test evidence: `outputs/configuration/agent-tests.xml`.

## Run and recovery

From the configured root:

```powershell
.\.venv\Scripts\python.exe -m releaseguard.cli agent --request-key release-review-1
.\.venv\Scripts\python.exe -m releaseguard.cli agent-latest
```

UI: **Investigate with Gemini**. The persisted trace survives page reload. **Run graph policy only** remains separate. An incomplete agent does not silently turn into a completed policy-only agent.

To retry a verifier after a provider failure, when a saved proposal exists and fewer than five calls have been admitted:

```powershell
.\.venv\Scripts\python.exe -m releaseguard.cli agent --request-key release-review-1 --resume-verifier
```

The UI exposes **Retry saved verifier** only for eligible new runs. Repeating a terminal run without explicit resume returns its saved result. Exhausted budget requires a new request key and a new investigation; there is no unlimited retry. A graph revision/expiry change prevents acting on the old handoff.

## Judge-facing demonstration

1. Select Checkout v2.4 and explain the synthetic release-review problem.
2. Show the dependency path and source details. Explain that Notifications is unrelated.
3. Click Investigate with Gemini. Show actual chosen graph tools and the separate verifier decision.
4. Show the historical retry failure and the qualified procedure-review proposal. Each displayed observation comes from verified IDs and source records.
5. For a current blocking scenario, use the synthetic New Ledger incident control, then investigate. Expect Blocked with the longer path if the provider completes; if it fails, show Incomplete and withheld agent actions. Never narrate a failed run as successful.
6. Change a relevant fact and show the prior run's stale evidence indicator. Reload to show persisted findings/trace. Existing task ownership and policy-only operation remain inspectable.

## Answers and limitations

**Why a graph?** Release dependencies determine which incidents and history are relevant, and paths connect findings to owners/actions and sources. The existing competent same-facts adjacency baseline agreed on all four core cases and was faster on this tiny fixture. No retrieval superiority is claimed.

**Why FalkorDB?** It is the actual execution store for paths, provenance, canonical runs, historical attempts, release state and tasks. Removing access prevents this workflow; there is no fixture-answer fallback.

**What does the agent do?** Chooses bounded evidence lookups and proposes complete source-backed findings and historical cautions; a separate role reviews them. Deterministic policy retains verdict/action authority. These are separate invocations of the same model, not statistically independent reviewers.

**What is distinctive?** Failed-attempt retrieval, a persistent source-backed handoff, strict evidence checks and read-time freshness around idempotent owner-assigned actions. Structured selections produce traceable explanations; arbitrary model prose is not accepted as a verified fact.

**What fails?** Providers can time out or return 503, evidence can be incomplete or stale, and budgets can expire. Those outcomes are persisted and actions withheld. The graph-only core remains explicitly separate. Free cloud uses plaintext transport and has disabled HA/backups; use synthetic evaluation data only.

**Remaining work:** synchronous API work has no durable job dispatcher; restart in the middle of a provider turn lacks full replay/lease recovery. The 90-second admission deadline is per invocation, with cumulative call budgets across handoff resume; HTTP phase timeouts do not enforce a hard process deadline. Interrupted calls can leave duration unknown. Handoff graph timing needs the same complete checkpoint accounting as terminal runs. Model reliability and quality have only smoke-test evidence, and a live blocked model-approved action remains unverified. No scalable/multi-writer or production tenant-isolation claim is made.

Highest-value next improvement: run this pipeline as durable jobs with visible progress and bounded recovery, then evaluate Ready, Blocked and insufficient-evidence cases repeatedly under real provider failures. The measured bottleneck is model/API time.
