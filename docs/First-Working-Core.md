# First working ReleaseGuard core — October 15, 2026

## Implemented and verified

The application now runs at http://127.0.0.1:8000. It is explicitly a **deterministic graph core**, not a configured LLM agent. No generated model output is used or simulated.

- Typed synthetic dataset ingestion, source references/checksums, stable IDs and no-op seed replay.
- Real parameterized FalkorDB queries for release dependencies, applicable incidents, owners, verification and historical attempts.
- Four-hop traversal, row budgets, frontier check and missing-evidence abstention.
- Release policy and owner-assigned persisted blocker tasks; duplicate requests produce one logical task.
- Persistent assessments with domain generation/revision, policy version and evidence expiry.
- Read-time freshness checks after new facts/relationships and expiry without a database mutation.
- Single-host serialization across CLI/API processes, dirty mutation journals and explicit recovery command.
- FastAPI endpoints and a source-linked browser interface with polling/disconnect states.

This is the first vertical slice of the existing modular-monolith plan. A static HTML interface keeps this stage small; React, RQ, investigator/verifier model calls and agent handoff are not implemented yet. Synchronous short core investigations run in FastAPI's thread pool. Model calls must not later be added inside the writer lock.

## Source map

| Responsibility | Source |
|---|---|
| Domain/input validation | backend/src/releaseguard/domain/models.py |
| Verdict/freshness policy | backend/src/releaseguard/domain/policy.py |
| Official client, timing and serialized access | backend/src/releaseguard/adapters/falkordb.py |
| Idempotent synthetic ingestion | backend/src/releaseguard/application/ingestion.py |
| Evidence investigation and assessment | backend/src/releaseguard/application/investigation.py |
| Persistent task effect | backend/src/releaseguard/application/actions.py |
| Synthetic evidence changes and recovery | backend/src/releaseguard/application/mutations.py; recovery.py |
| API / UI | backend/src/releaseguard/api.py; web/index.html |
| Representative dataset | fixtures/northstar.json |
| Tests and fair baseline | backend/tests; backend/src/releaseguard/evaluation.py |

## Verification evidence

23 tests pass against actual local FalkorDB plus deterministic policy cases. Tests include graph paths, task ownership, source support, failed-attempt retrieval, no-op seed, concurrent duplicate actions, missing release/owner/source, contradictory or expired verification, relationship removal, new incident, cycles/depth frontier, command-key conflict, interrupted-write recovery, cross-graph separation, parameter injection rejection and real connection failure.

A separate Python subprocess successfully retrieved a persisted assessment. The actual FalkorDB container was restarted; the production-demo assessment ID/revision and task IDs matched before/after. This establishes the tested graceful-restart behavior, not power-loss durability or LLM handoff.

Artifacts: `outputs/implementation/test-results.xml`, `persistence-before.json`, `persistence-after.json`, `graph-comparison.json`, and `releaseguard-core.png`.

Browser actions were verified: Blocked -> resolve incident -> Needs reassessment -> assess -> Ready -> create Ledger incident -> Needs reassessment -> assess -> Blocked. Final path: Checkout -> Payments -> Ledger -> INC-13. UI displayed Money as owner and real task state.

Ruff passes, pip dependency check passes, and wheel packaging builds successfully. Starlette emits one test-client deprecation warning concerning httpx; it does not fail tests. No additional dependency was added merely to suppress it.

## Measured results

Dataset: 22 initial nodes, 18 initial edges, six synthetic services. Windows 11/Ubuntu WSL 2, Python 3.12.14, FalkorDB Python client 1.8.0, pinned server image in environment/compose.yaml. Five warmups, 30 measured runs on the final mutated/cyclic test fixture, one reused connection; raw samples and query text are retained in graph-comparison.json. Ingestion/initialization excluded from warm query timings.

| Measurement | Observed result |
|---|---:|
| Four relationship cases: graph versus same-facts adjacency-list baseline | 4/4 agree |
| Graph client + mapping median / p95 | 1.597 / 2.260 ms |
| Graph server execution median / p95 | 0.164 / 0.272 ms |
| In-memory baseline median / p95 | 0.037 / 0.065 ms |
| One complete deterministic assessment with task | 29.956 ms |
| Graph client spans within that assessment | 29.176 ms |
| Server execution within client spans | 1.390 ms |
| Other application/lock/serialization time | 0.780 ms |
| Model time | Not applicable; no model configured |

Graph and baseline both retrieve the indirect Ledger incident, exclude unrelated Notifications, remove the incident when its connecting relationship is removed, and handle the cycle. **No accuracy superiority or speedup is established.** The simpler in-memory baseline is faster on this tiny dataset. The demonstrated graph contribution is persisted centrally queryable relationships and path-backed actions, not a performance advantage over Python BFS.

The complete assessment is one observation, not a p95 workflow benchmark. Investigation timings stored in assessments exclude assessment persistence/final status read; immediate API responses also carry request_timing with the full application operation. Graph server time is a subset of graph client time, not an additional duration to sum.

## Reliability boundary and limitations

The serialized protocol avoids reliance on undocumented multi-query rollback: journal intent/dirty flag precede changes; dirty clears last; replay uses stable command identity and target revision. Failures preserve a stale/dirty state until an explicit replay completes. Tested callback interruption exercises a real persisted partial mutation, not a fake graph.

Supported boundary: one trusted local host, one configured synthetic tenant, cooperating code using the same lock directory. External database writes, distributed writers/fencing, authenticated multi-tenant authorization, HA and consistent backup restores are not validated. Cross-graph tests show database separation, not tenant security.

Source/version fields and immutable assessment snapshots support this fixed synthetic fixture. General document ingestion, entity resolution, full immutable fact history and migrations for arbitrary changed datasets remain work. Do not rerun a modified fixture as if it were a production ingestion pipeline.

No provider, tool-using investigator, model verifier, persistent model handoff, durable queue or production deployment exists yet. Historical attempts are retrieved, but no model has been shown to change a proposal based on them.

## Highest-value next improvement

Choose a locally available tool-capable provider, configure credentials outside chat, and connect a bounded investigator plus evidence verifier to the tested graph tools. Preserve deterministic policy/action gates. Demonstrate that failed-fix memory changes the actual proposed plan and that the verifier rejects unsupported findings. Add queued model execution when long-running calls make the current synchronous path unsuitable.
