# ReleaseGuard — pre-event build preparation

Prepared October 12, 2026. Planning notes only; no application code, queries, UI implementation, or executable fixtures. Read alongside ReleaseGuard-Project-Plan.md. Main implementation starts October 15, 2026, 12:01 AM IST.

## Frozen MVP decision

One synthetic company, one release workflow, two agent roles, and six observable capabilities: graph investigation, sourced findings, blocker creation, failed-fix memory, stale recommendation detection, and persistent handoff. Rehearsal is optional after these work.

The recommendation is a verdict against explicit checks, not a guarantee of deployment safety. Every screen must distinguish observation from inference and current evidence from expired evidence.

## Synthetic company story

Company: Northstar Shop, entirely fictional. Its checkout release modifies retry behavior in Checkout. Checkout calls Payments; Payments calls Ledger. Web Store and Mobile API consume Checkout. Notifications and Analytics are nearby services but are not blocking dependencies in this scenario.

Teams: Commerce owns Checkout and Web Store; Money owns Payments and Ledger; Platform owns shared runtime infrastructure. All reviewer names and source records will be synthetic.

Proposed source notes to write during the event:

- Release specification identifies changed retry behavior and required checks.
- Service catalog identifies dependency direction, ownership, and critical versus optional edges.
- A historical incident records retry amplification and an unsuccessful retry increase.
- The same incident records a successful timeout/circuit-breaker procedure, with conditions and observed outcome.
- A current Payments incident establishes the first blocker.
- Fresh integration verification and incident resolution support the next assessment.
- A newly created Ledger incident makes the old recommendation stale.

Historical success is evidence to investigate a procedure, not proof it will work for the new release.

## Graph sketch

```text
Release checkout-v2.4 -> HAS_CHANGE -> retry-change -> TOUCHES -> Checkout
Web Store -> DEPENDS_ON -> Checkout -> DEPENDS_ON -> Payments -> DEPENDS_ON -> Ledger
Mobile API -> DEPENDS_ON -> Checkout
Checkout -> OWNED_BY -> Commerce
Payments -> OWNED_BY -> Money
Current incident -> AFFECTED -> Payments
Historical incident -> AFFECTED -> Payments
Historical incident -> HAD_ATTEMPT -> retry-increase -> RESULTED_IN -> overload-worsened
Historical incident -> HAD_ATTEMPT -> timeout-procedure -> RESULTED_IN -> recovery-observed
Finding -> USES_EVIDENCE -> versioned fact/source
Task -> JUSTIFIED_BY -> Finding; Task -> BLOCKS -> Release
Recommendation -> DEPENDS_ON_FACT -> versioned facts
Investigation -> HAS_FINDING -> Finding; Handoff -> FOR_INVESTIGATION -> Investigation
```

Traversal questions: What does the changed service depend on? Which consumers could be affected? Who owns the implicated service? Which applicable incident remains unresolved? Which previous attempt failed? Which required verification is missing? Which new relationship lies inside the assessed scope?

## Verdict decision table

Apply the following precedence to a completed assessment. Infrastructure errors remain failed investigations rather than fabricated verdicts.

| Condition | Result | UI behavior |
|---|---|---|
| Relevant evidence changed before publication or since assessment | Needs reassessment | Immediately mark previous verdict stale; schedule reevaluation |
| Current verified mandatory violation exists | Blocked | Show violation and actionable blocker; list missing evidence separately |
| No verified violation, but required evidence is missing, expired, or traversal is incomplete | Insufficient evidence | Identify exact missing checks and limits |
| All configured checks pass against current complete evidence | Ready | Show assessed time, revision, supporting checks, and scope |

This precedence avoids hiding a known blocker behind another missing check. Reassessment may finish as Blocked, Insufficient evidence, or Ready. Do not treat an ongoing reassessment as a completed verdict.

## Demo storyboard and acceptance criteria

| Step | User/judge sees | Required proof |
|---|---|---|
| 1. Assess checkout release | Investigation progresses through actual tools | Query execution and persisted investigation, not predefined answer |
| 2. Discover dependency risk | Checkout -> Payments -> incident path | Actual matching entities and source records |
| 3. Retrieve failed-fix memory | Earlier retry increase worsened overload | Persisted attempt/outcome; relevance explained as inference |
| 4. Act | Money team receives one blocker task | Task linked to finding, release, and owner; replay creates no duplicate |
| 5. Resolve | Fresh checks and resolution enable a new assessment | Required checks validated before recommendation changes |
| 6. Inject new Ledger incident | Previous Ready result becomes Needs reassessment | Inserted incident caught despite absent old fact reference |
| 7. Restart worker and hand off | Verifier continues saved investigation | IDs, pending checks, actions, and remaining budget survive restart |

Use explicit event injection controls labeled as synthetic data changes. Resetting the demo clears only designated synthetic demo state through a documented mechanism. Never delete arbitrary user graphs.

## Day-one vertical slice

During the event, implement one complete path before broadening:

1. Validate synthetic release input and resolve a server-selected graph.
2. Traverse changed service dependencies with bounded depth and rows.
3. Retrieve an applicable current incident and its source.
4. Persist a finding and Blocked verdict through deterministic policy.
5. Display that verdict and evidence path in the frontend.

Exit criterion: fresh startup produces the same graph-backed finding; missing FalkorDB fails visibly. This first slice needs no polished model prose or elaborate animation.

## Implementation backlog in dependency order

| Item | Depends on | Done when |
|---|---|---|
| Verify client and database semantics | Environment | Parameterization, transaction limitations, indexing, timeouts documented |
| Domain states and ports | Semantic verification | Policies and transitions separated from adapters |
| Idempotent fixture ingestion | Graph adapter | Replayed input changes neither node counts nor revision |
| Graph investigation tools | Fixture ingestion | Direction, cycles, truncation, and source paths correct |
| Assessment persistence and policy | Tools and domain | Current verdict stored with exact evidence scope |
| Minimal frontend evidence workflow | API | One usable end-to-end release assessment |
| Blocker actions and retry handling | Findings | Duplicate delivery produces exactly one task |
| Investigator/verifier model flow | Structured tools | Invalid model output cannot create unsupported findings or override policy |
| Failed-fix retrieval and handoff | Persistent investigation | Restarted verifier continues from canonical state |
| Mutation invalidation | Evidence dependencies | Changed facts and newly inserted relationships both mark affected verdicts stale |
| Evaluation and final presentation | Core workflow | Measured results, reliable reset, reproducible setup and truthful demo |

If model work slips, preserve structured graph findings and incomplete assessment state. Do not represent a model-free fallback as completed autonomous reasoning.

## Planned evaluation cases

Write executable fixtures and expected-answer files only during the event. Keep answer keys outside the agent's accessible tools.

- Direct ownership lookup succeeds with source.
- Consumer impact follows incoming dependency edges and excludes unrelated services.
- Dependency cycles terminate without duplicate findings.
- Bound exhaustion reports incomplete coverage and prevents Ready.
- Relevant failed retry attempt is retrieved; unrelated history is excluded.
- Expired verification cannot satisfy a required check.
- Missing owner produces an explicit missing-evidence finding.
- Confirmed blocker plus missing test stays Blocked while exposing both.
- Duplicate action requests create one task even under concurrent delivery.
- New incident and newly added dependency each invalidate a prior recommendation.
- Mutation during publication cannot leave an apparently current Ready verdict.
- Worker restart retains handoff and action history.
- Graph outage fails explicitly; model outage preserves unfinished state.

Baseline: same model, source corpus, comparable budget, document retrieval without graph tools. Report case-level outcomes and failures, not just an aggregate score. Do not tune only against the frozen answer set.

## Risks and decision notes

- FalkorDB multi-query atomicity: verify before relying on it; serialize tenant writes in MVP and preserve durable recovery markers.
- New facts are absent from old evidence lists: maintain query scope watches and conservatively invalidate where completeness is uncertain.
- A: bind-mount performance: measure; never claim production throughput from tiny fixture timings.
- Existing WSL has about 4 GB RAM: keep local services bounded; inspect resource use before adding a queue or increasing worker concurrency.
- No configured LLM key was observed in the current shell: provider credentials must be set locally when chosen. Never expose them in chat or frontend.
- Docker does not use systemd in this WSL instance: startup instructions use `service docker start`; verify after a WSL shutdown.
- AI-generated code: participant reviews, verifies, explains, and discloses assistance. Avoid claims of wholly manual authorship.

## October 15 kickoff checklist

Confirm current rules and submission fields; verify A: workspace instructions; start Docker/FalkorDB; verify environment; choose model/provider; configure local credentials; initialize implementation tooling and dependency locks; execute the day-one slice; update actual progress and architecture decisions.

No automatic future run is scheduled. Implementation requires returning to this workspace when the event opens.
