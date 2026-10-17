# ReleaseGuard — requirements specification

Version 1.0 • Research date: October 14, 2026 • Status: pre-event planning

Companion: [implementation pathway](ReleaseGuard-Implementation-Pathway.md). Canonical context: [project plan](ReleaseGuard-Project-Plan.md) and [demo strategy](ReleaseGuard-Demo-and-Judging-Strategy.md).

## 1. Objective and evidence standard

Build a competitive, complete release-investigation agent whose graph determines its findings and actions. The differentiators are failed-fix memory and recommendations that become stale when their evidence changes. No technical architecture can guarantee first place.

This document distinguishes verified documentation facts, our proposed engineering requirements, and unresolved implementation gates. All requirements below are project decisions unless explicitly attributed to an event rule or source. None describe already implemented application functionality.

The goal is a functioning agent, not a deterministic report disguised as one: the investigator must select bounded tools and propose evidence-linked next steps; the verifier must examine them. Deterministic policy governs which proposals can become verdicts and actions.

## 2. Event requirements rechecked

The current event rules require essential FalkorDB use, new main coding/design during the event, permitted data, and disclosure of AI assistance. Main work starts October 15, 12:01 AM IST; submissions close October 18, 11:59 PM IST. Submission needs a public repository, setup and graph model, core queries/algorithms, working video, deployment or complete local setup, and track selection. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).

Target Track 01; enter Track 02 only when persisted memory and handoff work. The event emphasizes connected-data actions, memory/coordination, and company knowledge. [Official overview](https://www.wemakedevs.org/hackathons/falkordb).

The pages reviewed did not establish judging weights or a video duration limit. Our internal review criteria and three-minute storyboard are planning choices. Check authenticated submission fields at kickoff; record changes rather than assuming earlier information is final.

## 3. Product promise and exclusions

For an engineering lead: “Investigate this release, show its risks and missing checks, assign the right blocker, and tell me when your last answer is outdated.”

Ready means configured checks passed for the modeled scope at a stated revision/time. It does not mean a deployment is guaranteed safe. A dependency path establishes reachability, not an actual outage. A prior successful mitigation is historical evidence, not proof of present effectiveness.

In scope: Northstar Shop synthetic company, Checkout/Payments/Ledger dependency chain, ownership, sources, incidents, verification, local tasks, two agent roles, persistent investigation, freshness checks, and evidence UI.

Excluded: production deployment authority, unrestricted shell/Cypher tools, private company ingestion, elaborate enterprise auth, broad connectors, generic company chat, automatic code fixes, many agent roles. A bounded blast-radius rehearsal and MCP adapter are optional additions after the core passes.

## 4. Functional requirements and acceptance

P0 = mandatory core; P1 = required for the competitive complete entry; P2 = optional.

| ID | Priority | Requirement | Acceptance evidence |
|---|---|---|---|
| RG-01 | P0 | FalkorDB owns relationships, provenance, findings, memory and task justification | Removing access prevents investigation; no hidden answer fallback |
| RG-02 | P0 | Deterministic structured ingestion with stable identifiers | Replaying identical input creates no duplicate facts or domain revision |
| RG-03 | P0 | Bounded multi-hop traversal in both dependency directions | Correct indirect services; cycles terminate; unrelated services excluded |
| RG-04 | P0 | All factual findings cite source-backed graph paths | Each path resolves to matching IDs and fact versions; no unsupported factual statement accepted |
| RG-05 | P0 | Deterministic release policy | All verdict cases and precedence tests pass |
| RG-06 | P0 | Agent creates an owner-assigned local blocker | Persisted task links to release, finding, owner and incident |
| RG-07 | P0 | Action effects are idempotent under redelivery | Repeated/concurrent requests yield one logical task |
| RG-08 | P0 | Recommendations record domain revision, source versions and expiry | Read after relevant mutation or expiry cannot present an unqualified current Ready |
| RG-09 | P0 | Newly inserted facts/dependencies invalidate old conclusions | New Ledger incident and new dependency both make prior Ready stale |
| RG-10 | P0 | Interrupted mutations fail closed | Process termination during a write prevents current Ready until recovery |
| RG-11 | P1 | Investigator makes real bounded tool choices | Recorded model tool calls explain which context was requested; not a fixed prose-only wrapper |
| RG-12 | P1 | Verifier independently checks evidence and unresolved questions | Rejects invalid IDs, unsupported claims, stale facts and missing checks |
| RG-13 | P1 | Failed-fix memory changes a proposal | Relevant failed retry increase retrieved and avoided; irrelevant incident excluded |
| RG-14 | P1 | Handoff persists across worker restart | Verifier resumes saved stage/checks/actions without duplicating effects |
| RG-15 | P0 | Graph and provider failures remain explicit | Graph unavailable fails investigation; missing model leaves agent run incomplete |
| RG-16 | P1 | Usable release/evidence/history interface | Full story operable by keyboard; textual paths available; stale and missing states visible |
| RG-17 | P1 | Reproducible evaluation | Frozen cases, documented baseline/budgets, individual failures and measured results |
| RG-18 | P0 | Clean startup and reproducible submission | Independent fresh clone/reset produces working graph-backed flow |
| RG-19 | P0 | Trusted tool and graph boundaries | Arbitrary graph names, raw model queries, unsupported tools and unauthorized mutations rejected |
| RG-20 | P1 | Useful observability | Trace joins request, job, tool, query, evidence, model usage and action outcome without secrets |
| RG-21 | P2 | Read-only blast-radius comparison | Hypothesis changes only its result, never canonical graph; reachability labeled |
| RG-22 | P2 | Read-only MCP access to the same graph tools | MCP invokes the same application contracts; no second reasoning implementation |

P0 alone is an engineering milestone, not a claim that the complete agent entry is finished. The intended submission includes P1; cut P2 first.

## 5. Verdict semantics

| Ordered rule | Effective result |
|---|---|
| Dirty mutation, changed domain generation/revision, expired evidence, or unverified snapshot | Needs reassessment |
| Otherwise a verified current mandatory violation | Blocked |
| Otherwise missing required evidence, unresolved source contradiction, or incomplete traversal | Insufficient evidence |
| Otherwise every mandatory check passes | Ready |

Infrastructure failure is investigation state failed, not a successful release verdict. Retain the last historical verdict with a clear freshness label. A task closure cannot by itself resolve an incident or satisfy a verification requirement.

Store policy version. Changing policy invalidates old recommendations. Mandatory checks: valid ownership, relevant passing verification for the exact release/change identity, current source coverage, no applicable unresolved blocking incident, and complete traversal within declared scope. Severity and applicability follow explicit fixture policy; model intuition alone cannot designate a blocker.

## 6. Domain data and provenance requirements

Use typed nodes: Service, Team, Release, Change, Incident, Attempt, Outcome, Procedure, Verification, Source, Fact, Investigation, Finding, Recommendation, Task, Episode, Handoff, Command, MutationJournal, DomainState.

Use direct typed edges for traversal; give decision-critical facts stable application IDs and versions. An addressable Fact record can describe a relationship while the direct relationship carries its fact ID/version. Keep both consistent through the mutation pipeline. Never use transient graph-internal IDs as public domain identity.

DomainState includes generation UUID, monotonic revision, dirty flag and recovery marker. Increment only for decision-relevant changes; writing an investigation log or rendering progress must not invalidate every assessment. A restored backup gets a new generation before serving existing recommendations. Ordinary process restart preserves the generation unless state cannot be reconciled.

Source metadata: immutable ID/version, source checksum, observed time, validity, synthetic/source kind and fixture-relative location. Keep source records needed to resolve historical citations. An active view chooses the current fact; history remains inspectable. Missing source support blocks promotion to a verified factual finding.

Verification must identify exact release/change, check type, result, measured time and expiry. A passing check for another release cannot satisfy the current one. Contradictory incident/source claims remain explicit until reconciled.

## 7. Core system requirements

### Agent contract

Investigator tools: release context, downstream dependencies, upstream consumers, incident search, failed-attempt history, source fetch, verification status, owner lookup, proposed finding and proposed blocker. These are conceptual tool contracts, not executable code.

Verifier tools: fetch canonical finding/evidence, reread fact versions, check coverage/expiry, inspect current blockers, reject/accept finding, save handoff. Read and proposed-action capabilities are separate. The model cannot directly issue database mutations or authorize its own proposal.

A deterministic context seed guarantees mandatory facts are checked even if the investigator overlooks a tool. A real model selects additional investigative tools and explains relevance. A second role is a separate bounded invocation with persisted input, not two labels on one model response. It provides no statistical independence guarantee when using the same model.

### Freshness contract

Use a tenant-wide domain revision as the first correctness fallback; any domain mutation invalidates existing assessments. This may cause unnecessary reassessment but catches new facts. Scope-based invalidation is a later optimization with its own tests.

At API read time, calculate effective status against current domain generation/revision, dirty state, policy version, and earliest evidence expiry. Background stale marking improves UX; it is not the sole freshness guarantee. The frontend polls while visible and sets an expiry timer. A browser cannot know about an offline mutation instantly: show last-check time and disconnected/stale state. Revalidate current status before an action.

### Mutation and delivery contract

One active domain writer for the MVP; no other component may bypass it. A command journal, idempotent effects, monotonic revision and recovery scan must handle interruption between graph write and queue publication. Queue state is delivery metadata; FalkorDB remains canonical domain state.

Do not claim exactly-once message delivery. The intended guarantee is one logical effect under retried delivery within the verified single-writer boundary. Public multi-writer/HA support is outside scope until fencing and concurrency guarantees are proven.

### Bounds and configuration

Initial proposed limits, to measure and adjust during implementation: maximum 4 dependency hops, 200 distinct services, 500 returned evidence paths, 24 tool calls, 8 model turns, 90-second assessment deadline, one structured-output repair, 2 transient provider retries within the total deadline. If a boundary prevents complete investigation, abstain; a LIMIT alone does not prove traversal work was bounded.

Cost cap must be configured from the chosen model's current pricing and available budget before running batches. Stop on exhausted budget; never silently switch to canned model answers. Use strict input validation and reject unknown fields where appropriate. Pydantic documents strict mode for limiting coercion. [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/).

## 8. Technical selection and research findings

| Component | Proposed selection | Reason and boundary |
|---|---|---|
| Graph | FalkorDB and official Python client | Central sponsor technology; parameterized typed tools |
| API | Python 3.12, FastAPI, Pydantic | Small typed application boundary; no long-lived agent loop inside requests |
| Worker | RQ on separate operational Redis, running Linux/WSL/container | Bounded jobs and retries; graph retains canonical checkpoints |
| UI | React, TypeScript, Vite, React Flow | Release workflow and source-linked paths; no graph editor needed |
| Model | One tool-capable provider behind a narrow port | Choose by available credentials and a small reliability/cost probe |
| Infrastructure | Existing WSL Docker + Compose | Local reproducibility; persistent graph data on A: |
| Tests | pytest; frontend behavior checks; reproducible evaluation runner | Focus on domain invariants and real database behavior |

Verified facts and implications:

- Official Python client documents query parameters, read-only queries and millisecond timeouts. Use its adapter; confirm installed package compatibility at kickoff. [Client reference](https://falkordb-py.readthedocs.io/en/stable/falkordb.html).
- FalkorDB's query version parameter is for schema-cache mappings, not our business revision. Parameterized queries and query timeouts are documented. [GRAPH.QUERY](https://docs.falkordb.com/commands/graph.query).
- FalkorDB documents eager-operation LIMIT behavior and relationship-counting differences. Do not use result LIMIT as mutation protection; test parallel edges explicitly. [Known limitations](https://docs.falkordb.com/cypher/known-limitations).
- The retrieved sources did not establish the complete transaction contract needed by our design. The atomicity documentation issue is closed, but its issue description is not a guarantee. Verify actual documentation/server behavior before implementation claims. [Maintainer issue](https://github.com/FalkorDB/docs/issues/393).
- FastAPI documents small background tasks and recommends separate tools for heavier distributed work. Our choice is a durable external worker. [FastAPI](https://fastapi.tiangolo.com/tutorial/background-tasks/).
- RQ documents one job at a time per worker, configurable serialization and worker lifecycle. Use JSON job arguments containing identifiers, not pickled untrusted objects. [RQ workers](https://python-rq.org/docs/workers/).
- RQ supports retry intervals and requires scheduler support for interval retries. Application recovery must separately handle interrupted work. [RQ retries](https://python-rq.org/docs/exceptions/).
- Redis AOF every-second persistence can lose about a second of writes in a disaster. Graceful restart persistence does not establish zero-loss crash durability. [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/).
- React Flow provides React graph UI primitives. Vite's guide lists Node compatibility; verify the locked template against available Node 24.15.0. [React Flow](https://reactflow.dev/learn), [Vite](https://vite.dev/guide/).
- Gemini and Claude both document application-executed tool calling. Their documentation does not prove one model is best for our tasks. Choose one accessible model at kickoff, pin the model ID, test it and record limits. [Gemini tools](https://ai.google.dev/gemini-api/docs/function-calling), [Claude tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview).
- GraphRAG SDK has its own ingestion/retrieval architecture. It is optional here: direct structured ingestion gives us clearer control of release facts and freshness. Avoid stacking Graphiti, Cognee and GraphRAG SDK without a concrete need. [SDK architecture](https://docs.falkordb.com/graphrag/architecture).
- MCP is an integration interface, not an authorization or correctness substitute. If added, wrap existing read-only tools first and preserve application checks. [MCP server concepts](https://modelcontextprotocol.io/docs/learn/server-concepts).

## 9. Acceptance and measurement matrix

| Suite | Must demonstrate | Release gate |
|---|---|---|
| Domain policy | All verdicts, precedence, policy changes, exact verification applicability | All deterministic cases pass |
| Graph integration | Correct directions, cycles, parallel edges, source versions, truncation | Expected IDs and citations match fixtures |
| Mutations | No-op replay, dirty recovery, journal replay, revision updates | No current Ready from interrupted/mixed state |
| Action reliability | Duplicate job and command, timeout after write, repeated handoff | One logical blocker |
| Freshness | New fact, new edge, expiry without write, restart/restore generation | Current API response is stale when required |
| Agent | Real tools, bounded loop, rejected invented IDs, failed-fix relevance | Unsupported factual outputs never promoted |
| Interface | Full demo story, keyboard flow, failure and disconnect states | One reproducible end-to-end run |
| Evaluation | Fair static baseline plus separate system tests | Publish outcomes, settings and failures |

Static comparison: same model and source corpus, comparable budgets, easy and relationship-heavy questions, abstention allowed. Keep answer keys unavailable to the agent. Do not present system recovery tests as evidence of retrieval accuracy superiority. Final performance numbers must be measured, with repetitions and hardware recorded.

## 10. Delivery gates and remaining decisions

G0: event-time semantics spike confirms adapter/query behavior and fail-closed mutation/read protocol. G1: real blocked assessment with source path. G2: actual agent proposal/verifier flow and one task. G3: memory, freshness, expiry and recovery. G4: UI, evaluation, setup and submission verification.

Unresolved: live submission fields and video limit; active provider credentials/model/cost cap; pinned dependency versions; tested transaction/constraint behavior; RQ/Redis/server compatibility; deployment access controls. These must be resolved or disclosed, not filled with assumptions.

No application implementation was performed in preparing these documents. Prior environment checks from October 12 are historical observations, not a claim of current service health.
