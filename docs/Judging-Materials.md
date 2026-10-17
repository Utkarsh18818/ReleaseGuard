# Architecture, graph evaluation and demo materials

Audit edition: October 14, 2026. Everything below describing an agent is proposed. The current executable example is infrastructure PING in README. Do not record this as a completed application demonstration.

## Concise architecture explanation

Planned flow: release UI -> typed API -> bounded investigator graph tools -> persisted evidence and handoff -> verifier -> deterministic policy -> idempotent owner-assigned task. FalkorDB is intended to store dependency paths, provenance, incident/fix history and canonical investigation state. Current runtime contains only FalkorDB infrastructure; no part of that application flow exists yet.

Retain the modular monolith. First establish one vertical slice. Do not add a framework, extra model, integration or agent just to decorate the architecture. Existing plans for two roles and a durable worker are proposals requiring implementation and reliability checks.

## Representative relationship cases and fair baseline

The following examples use planned **synthetic Northstar Shop data**. Expected answers are reasoning specifications, not measured results. No data or queries were executed for these cases during this pre-event audit.

Baseline A: ordinary Python adjacency-list traversal over the exact same exported structured facts, with incident/owner lookups and visited-node cycle handling. It may traverse all permitted relationships and return complete paths; do not limit it to keyword lookup. Include import/export time separately from warm query time. A simple in-memory baseline will plausibly be faster for a tiny dataset; report that if observed.

Optional baseline B: document retrieval with the same model/corpus and comparable budget for narrative historical-fix questions. Separate extraction differences from traversal differences. It is secondary to the stronger same-facts structural baseline, not a substitute designed to lose.

| Case | Same facts supplied to both | Expected support | Mutation and expected effect | Actual result |
|---|---|---|---|---|
| Indirect release risk | Checkout depends on Payments; Payments depends on Ledger; open blocking incident affects Ledger | Checkout -> Payments -> Ledger <- incident | Remove Payments -> Ledger: incident leaves Checkout dependency scope if no alternate path | Not run |
| Accountable blocker | Checkout -> Payments; Payments owned by Money; active Payments blocker | Checkout -> Payments -> Money plus incident source | Replace Money ownership with unknown: no invented assignee; missing ownership exposed | Not run |
| Failed mitigation | Prior Payments incident -> retry attempt -> worsened overload | Linked attempt, outcome and source; current relevance is inference | Remove affected-service relation: history should not be asserted as Payments-specific | Not run |
| Irrelevant incident | Notifications incident; no path from Checkout | Absence of modeled path, with explicit traversal coverage | Add required dependency to Notifications: reassess scope and applicability | Not run |
| Cycle and direct lookup | Checkout/Payments cycle; known Commerce owner | Finite distinct results; direct ownership source | Cycle removal changes paths, not necessarily final risk | Not run |

When executed during the event, create an isolated explicitly named synthetic graph; use actual parameterized FalkorDB read queries and save query text, result IDs, source paths, server/client timing and baseline outputs. Mutate only the isolated fixture, rerun both approaches, and restore it. Preserve all alternate paths when judging edge-removal effects.

Acceptance: both methods should agree on deterministic graph semantics. A tie is a valid result. FalkorDB contribution may be centralized persistent queryable relationships and shared updates rather than higher accuracy or speed than Python on small data. Claim advantages only when measured. Tenant isolation, crash recovery and freshness are separate system tests, not retrieval accuracy wins.

## Demo script — execute only after features pass

The current rules require a working video and core queries; no video duration limit was verified in the pages checked. Recheck the submission panel and adapt length. The approximately three-minute plan below is our target, not an event rule.

1. User problem: “Can we release checkout-v2.4?” State that company data is synthetic.
2. Connected evidence: show the real dependency query/path to the incident, the source, and owner. Include actual IDs and times.
3. Agent decision/action: show verified Blocked and creation of one owner-assigned task. Replay once to prove no duplicate effect.
4. Traceable memory: show the previous failed retry attempt. Distinguish the historical observation from the agent's inference about this release.
5. Update evidence: incident resolution without passing verification remains incomplete; valid current checks support Ready.
6. New relationship/fact: insert a relevant Ledger incident, mark the old recommendation stale, and show the new evidence path.
7. Measured benefit: show real case-level graph/baseline results, including ties, losses and costs. If none exists, the demo is not ready.
8. Optional restart/handoff: show only if actual checkpoint recovery passes; do not substitute a rerecorded sequence for continuous state.

Every beat is currently pending application implementation. A real demo must show functioning queries and action state, not read this script over mock screens.

## Likely questions and honest answers today

**Why a graph?** The modeled release risks span several explicit relationships. The baseline may answer them equally well; comparative benefit is not established yet.

**Why FalkorDB?** It is the event's required central graph technology and our local service is working. We intend to use its traversals and persisted shared relationships. No application throughput advantage has been measured.

**What does the agent do?** No agent is implemented today. The intended action is an evidence-backed local release blocker assigned using ownership relationships.

**What is technically distinctive?** Planned combination of failed-fix memory and withdrawal of stale recommendations. Distinctiveness is a product hypothesis until working and evaluated; do not claim world-first novelty.

**What fails and how is it handled?** We observed the Docker daemon stopped; documented startup restored it. Model failure, graph failure during an assessment, interrupted writes, contradictory sources and cross-tenant access are planned tests, not verified handling.

**Is persistence verified?** Configuration and A: mount are verified. There is no persisted application state to test. Historical empty infrastructure/restart checks do not prove agent memory or disaster recovery.

**Is it ready for submission?** No. No application, working release example, graph comparison, public repository history or final video exists yet.
