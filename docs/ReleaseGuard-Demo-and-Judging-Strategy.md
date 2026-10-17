# ReleaseGuard — locked demo and judging strategy

Planning notes, October 12, 2026. No implementation. Main coding begins October 15, 12:01 AM IST. Companion to the canonical project plan and build preparation notes.

## 1. Product thesis and pitch

ReleaseGuard investigates a proposed release using connected evidence, remembers failed mitigations, creates a justified blocker, and marks its own recommendation stale when relevant facts change.

Pitch: **“An agent that remembers failed fixes and knows when its last recommendation is no longer valid.”**

User value: an engineering lead sees the relevant risk, accountable owner, missing verification, and evidence behind the decision in one workflow.

Competitive hypothesis, not verified competitor analysis: a focused demonstration of recommendation invalidation and failed-fix memory may stand out among graph-backed question-answering projects. Validate this through a working product, not claims of being first or unique worldwide.

## 2. Frozen scenario

Fictional company: Northstar Shop. Release: checkout-v2.4. Change: retry policy in Checkout. Mandatory release checks: known owner, fresh integration verification covering Checkout/Payments, no open applicable blocking incident, and complete bounded dependency coverage for the modeled release scope.

Relevant dependencies:

```text
Web Store -> Checkout -> Payments -> Ledger
Mobile API -> Checkout
```

Each arrow means DEPENDS_ON. Both consumer impact and downstream release dependencies must be queried in the correct direction. Notifications and Analytics are deliberately unrelated to the blocking path.

Historical incident HIST-07: retry increase worsened overload during a Payments incident. A timeout/circuit-breaker procedure was later associated with recovery under recorded conditions. Store both outcomes; do not imply the historical procedure automatically fixes the current issue.

Current incident INC-12: active Payments timeout incident, designated blocking by an explicit fixture rule. Commerce owns the changed service; Money owns the implicated service and receives the blocker.

Later incident INC-13: a newly inserted blocking Ledger incident, not present in the first recommendation's evidence list. Its dependency relationship to Payments is what makes it relevant.

## 3. Narrative beats and expected outputs

| Beat | Event | Expected observable outcome | Why it matters |
|---|---|---|---|
| A | Lead requests assessment | Investigation ID and real progress; no verdict until checks finish | Shows a working agent loop |
| B | Graph connects changed service to INC-12 | Blocked; Checkout -> Payments -> INC-12 path, source and owner | Graph materially changes the decision |
| C | Historical outcome retrieved | Warn against repeating retry increase; distinguish history from inferred relevance | Memory changes the proposed plan |
| D | Agent creates blocker | Exactly one Money-owned task linked to release and finding | Agent acts on evidence |
| E | Same action/job replayed | Existing task returned; count stays one | Reliability under retries |
| F | Incident resolved but required verification absent | Insufficient evidence; identify missing integration check | No unjustified Ready state |
| G | Passing fresh verification supplied | New Ready recommendation, timestamp/revision and check list | Evidence drives progression |
| H | INC-13 inserted | Previous Ready immediately becomes Needs reassessment | Detects a new fact absent from old evidence |
| I | Reassessment finishes | Blocked through Checkout -> Payments -> Ledger -> INC-13 | Multi-hop impact and updated action |
| J | Worker restarted before verifier finishes | New verifier resumes pending checks and existing actions | Persisted coordination, not in-memory theater |

Task resolution at F must satisfy its own workflow conditions. Closing a task alone never resolves an incident or creates passing test evidence. Ready at G requires both current valid verification and no remaining blocker.

## 4. Short recording storyboard

Target about three minutes for planning; the actual submission limit remains unverified and takes precedence. Keep a longer backup recording for a reviewer who wants detail.

| Time | On screen | Spoken point |
|---|---|---|
| 0:00–0:20 | Release and its changed service | “A release decision depends on more than the changed file.” |
| 0:20–0:55 | Real assessment; relevant path and source drawer | “The agent found a blocking incident through the dependency graph.” |
| 0:55–1:20 | Historical failed retry attempt and assigned task | “It remembers what failed and creates an evidence-backed blocker.” |
| 1:20–1:45 | Missing verification, then passing verification | “It requires current evidence before changing the recommendation.” |
| 1:45–2:20 | New Ledger incident; stale badge; changed verdict | “New facts invalidate its previous answer—even facts it had never seen.” |
| 2:20–2:45 | Persisted handoff after restart | “The next agent continues the investigation from the same graph.” |
| 2:45–3:00 | Measured evaluation and reproducible setup | “These are actual queries, persisted actions, and measured results.” |

Use honest cuts to shorten waiting periods. Label synthetic event injection and process restarts. Never splice different runs to imply continuity that did not occur. Do not display provider keys, generated database credentials, or private filesystem content.

## 5. Evidence package for a judge

Every factual finding includes entity IDs, actual ordered graph path, source identifier, observation time, and fact revision. Recommendations include mandatory checks, graph revision, watched query scope, and missing/truncated information. Task detail links back to the finding. History links superseded recommendations to their replacements.

A concise architecture view should explain four responsibilities: graph stores connected evidence and memory; tools retrieve bounded context; agents investigate and verify; deterministic policy validates the final verdict and permitted actions.

Do not show hidden chain-of-thought. Show tool calls, graph results, evidence, decisions, and action history. These are sufficient to explain and audit behavior.

## 6. Judge questions and our required answers

| Likely question | Answer must be demonstrated by |
|---|---|
| Why FalkorDB? | Dependency traversals, source paths, historical relationships, persistent handoff, and invalidation scope |
| What breaks without the graph? | Core investigation fails visibly; no alternative canned decision engine |
| Is this just a chatbot? | A release-specific workflow with actual task writes, verification, and state transitions |
| What makes memory useful? | A retrieved failed attempt changes the next proposed mitigation |
| What happens when the world changes? | New incident and new dependency both invalidate affected recommendations |
| Is the agent safe to trust? | Current sources, explicit uncertainty, bounded tools, policy gates, and visible failures |
| Does it coordinate? | Verifier resumes a persisted handoff with pending checks and existing action IDs |
| What did you measure? | Frozen cases, same-model baseline, case-level results, resource and budget disclosure |
| What is real versus synthetic? | Synthetic company data; real database queries, model calls, task state and persistence |
| What was built during the event? | Accurate repository history and disclosure of pre-event planning/environment work |

These are our review questions, not a published official rubric.

## 7. Baseline experiment design

Prepare 12 planned cases: 3 simple direct lookups; 4 multi-hop relationship cases; 2 historical outcome cases; 3 freshness/missing-evidence cases. Write datasets and executable evaluation tooling during the event.

For static answer comparison, both approaches receive the same source facts and model, with recorded comparable token and elapsed-time budgets. Baseline uses document retrieval; graph variant uses bounded graph tools. Both may abstain. Log model/version, prompt version, corpus, retrieval settings, query limits, and run count. Run multiple repetitions for model-dependent cases if time permits.

For persistence, stale marking, duplicate delivery, and agent handoff, run separate system acceptance checks. Do not compare a full workflow engine against a document-answering baseline and claim that difference proves graph retrieval superiority.

Metrics: correct entities and paths, source support, correct verdict/abstention, latency and cost. Record false positives as well as missed risks. Publish failures. Never claim causality or production reliability from this small synthetic benchmark.

## 8. What gets priority

P0: actual traversals, policy checks, evidence paths, task writes, idempotency, stale-state correctness, reproducible startup.

P1: failed-fix retrieval, persisted verifier handoff, accessible polished release screen, fair evaluation and clear recording.

P2: optional blast-radius rehearsal and additional track entry, only after P0/P1 are verified.

Cut first: graph animation flourishes, extra integrations, broad chat capabilities, multiple provider support beyond a narrow adapter, additional agent roles, and elaborate hypothetical simulation.

## 9. Failure modes that would weaken the entry

- Calling a dependency path proof of an actual outage.
- Claiming a past mitigation is guaranteed to work now.
- Displaying a current-looking Ready badge after relevant evidence changed.
- Saving conversations without demonstrating memory's effect on behavior.
- Listing multiple agents that do not exchange persistent state.
- Showing a graph visualization whose underlying data does not determine actions.
- Tuning the demo model against an accessible expected-answer file.
- Claiming sub-millisecond or production-scale performance without measurements.
- Presenting mocked model output as a real agent run.

## 10. Final planning decisions

The centerpiece is recommendation invalidation; failed-fix memory provides the emotional hook; evidence-backed task creation proves usefulness. Every feature should strengthen that one story.

Our first event-time milestone is an actual blocked release assessment with a source path. Our final milestone is the same workflow surviving new information and process restart. A polished complete workflow is the entry; optional scope remains optional.
