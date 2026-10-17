# Actual measurement results — October 14, 2026

## Scope and method

This is an infrastructure readiness measurement, not a ReleaseGuard workflow benchmark. Dataset: zero graphs, zero domain records. No model/API calls or application execution exist.

Windows 11 build 22621; isolated Python 3.12.14; Ubuntu 24.04 WSL 2; Docker Engine 29.9.0; Compose 5.6.0; server image pinned in environment/compose.yaml; Redis INFO reports 8.10.2. No dependency changes were made for timing.

One Windows-to-WSL loopback TCP connection, authenticated once, three PING warmups then 30 sequential PINGs. Elapsed time uses `perf_counter_ns`; includes socket transport, server command and client parsing. p95 is nearest-rank. Before = original ignored template after starting the service; after = new template using the same image and data directory. Sessions were sequential and subject to warmup/scheduling effects, not a randomized controlled performance experiment.

Raw evidence: [before](environment-before.json), [after](environment-after.json). Diagnostic script is `work/audit_environment.py` (ignored intermediate; read-only Redis commands, no application client).

Additional verification: [configuration/authentication checks](checks-evidence.json). An unauthenticated PING returned NOAUTH; configured authentication succeeded. This verifies database authentication, not tenant isolation.

| Measurement | Before | After | Interpretation |
|---|---:|---:|---|
| Docker available on arrival | No | Yes after documented startup | Availability restored |
| Version-control-eligible Compose template | No | Yes | Reproduction gap corrected |
| Missing-password rejection on new template | Not tested | Pass | Configuration fails closed |
| Authenticated PING | Pass | Pass | Local endpoint reachable |
| Unauthenticated PING | Not tested | Rejected with NOAUTH | Database authentication enforced |
| Graph count | 0 | 0 | No application workload |
| PING median, ms | 0.6460 | 0.3754 | Observed samples only; no attributable speedup claim |
| PING p95, ms | 0.9702 | 0.7214 | Same caveat |
| PING minimum / maximum, ms | 0.5050 / 1.1039 | 0.3691 / 0.7467 | Local empty-server round trips |
| AOF enabled / last write status | 1 / ok | 1 / ok | Configuration/health, not crash durability proof |
| Current data directory | /var/lib/falkordb/data | /var/lib/falkordb/data | Original symlink and new direct mount resolve to same A: folder |
| Graph-query execution time | Not measured | Not measured | No domain graph/query |
| Model/API time | Not applicable | Not applicable | No model integration |
| Other application time | Not applicable | Not applicable | No application |
| End-to-end accuracy, latency, cost | Not measured | Not measured | Must not infer from PING |

## Future application measurement protocol — not executed

Record cold initialization separately. For warm runs, use 5 warmups and at least 30 repetitions for deterministic graph/baseline queries; preserve raw samples and failures. Model trials need repeated runs within a declared budget, identical model/version, source content and recorded retrieval limits.

Capture per-query server execution time where returned by the actual client, per-query client wall time, model HTTP wall time/tokens/cost, and application stage time. Label parallel spans; do not add overlapping durations and call them end-to-end time. End-to-end uses one wall clock; queue waiting is a separate span. Client query wall time minus server execution is transport/client overhead, not pure network time.

Do not optimize until a real trace identifies a bottleneck. Keep dataset, hardware, query bounds, connection reuse and model settings fixed for an attributable before/after experiment. Verify correctness again after any query/index/context change.

Application evaluation and graph-benefit proof remain unrun because the project contains preparation only and the main coding window has not opened.
