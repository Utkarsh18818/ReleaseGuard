# Submission readiness — October 17, 2026

ReleaseGuard helps an engineering lead decide whether a proposed release has unresolved risks in its connected services. Its two distinctive behaviors are remembering failed fixes and withdrawing an earlier recommendation when connected evidence changes.

Primary track: **Agents That Act on Connected Data**. Real dependency queries find relevant incidents and owners; accepted findings create graph-persisted tasks. Persistent investigator/verifier handoff also supports a secondary Memory and Coordination entry, but the application does not claim authenticated tenant isolation or high availability.

## Published requirements

Rechecked October 17 against the [official rules](https://www.wemakedevs.org/hackathons/falkordb/rules) and [schedule](https://www.wemakedevs.org/hackathons/falkordb/schedule). Deadline: **October 18, 2026, 11:59 PM IST**. Required deliverables: public source repository, README/setup and graph model, essential queries/algorithms, working demo video, deployment or complete local setup, named track(s), and AI-assistance disclosure. Main implementation/design must be event-period work. Participants must understand and explain the system.

The public pages do not specify a video length or judging weights. On October 17 the authenticated submission form was inspected: it specifically requires a public/unlisted **YouTube** demo link and includes two required feedback questions. The local app is not a public deployment. Registration was verified for the existing one-member team RAGDOR; the site warns that team membership cannot change after submission. Final submission status must be verified separately.

## Submission copy

**Title:** ReleaseGuard — an agent that remembers failed fixes.

**Short description:** ReleaseGuard investigates a release through FalkorDB service dependencies, current incidents, owners and verification records. Gemini selects bounded evidence tools; a separate verifier and deterministic rules gate its actions. It creates traceable blocker tasks and marks its previous decision outdated when the graph changes.

**What is distinctive:** The release decision, failed-fix memory, task ownership and saved agent handoff share a connected evidence model. Freshness is checked when a result is read, rather than trusting a previously generated answer indefinitely. The model proposes structured findings; it does not receive deployment authority.

**AI disclosure:** AI assistance was used for planning, implementation, documentation and testing. The participant must review and understand the submitted implementation and demonstrate meaningful contribution. Do not claim independent manual authorship.

## Architecture a judge can follow

Browser → FastAPI → FalkorDB-persisted job → Redis delivery → Linux worker → investigator tools → saved handoff → verifier → evidence gates → release policy → owner-assigned task. A dispatcher reconciles pending jobs. The browser reads canonical APIs and never receives provider/database credentials.

FalkorDB holds dependency/ownership relationships, source records, incident history, release assessments, model checkpoints and tasks. Redis holds transport metadata. Single-host file locks serialize domain changes; this is not a distributed transaction or HA system.

## Demonstration script

This is our recommended sequence, not an official duration requirement. Record a continuous real run where practical; label any waiting-time cuts. Company data and demo events are synthetic. Database calls, model requests and task persistence are real.

1. **Problem:** “A Checkout release can be blocked by a Payments or Ledger incident even when Checkout itself looks fine.” Show the release decision and scope.
2. **Connected evidence:** Select Payments or Ledger on the service map. Open the catalog/source and trace Checkout → Payments → Ledger. A path establishes potential impact, not a proven outage.
3. **Memory:** Open Past fixes. Show the retry increase that worsened overload and the historical timeout/circuit-breaker procedure. Explain that the latter still needs current validation.
4. **Agent action:** Select Review release. Show background progress, then the accepted outcome and Money-owned blocker if an applicable incident is open. Open its supporting source. If the provider fails, show the explicit failure; do not present a graph-only assessment as a successful model review.
5. **Changing facts:** From a Ready state, Demo lab → Add incident inserts INC-13 on Ledger. The saved result becomes Review outdated. Review again; the new blocker follows the multi-hop dependency path. Resolve INC-13 only after it exists; review again to check the new evidence.
6. **Missing evidence:** Expire check, then review or Check rules. Show missing verification. Record pass supplies a synthetic check record, not a real CI run. These operations are explicitly labeled in Demo lab.
7. **Proof:** Open Technical details for model/graph time and tool IDs. Point to saved tests and the fair graph/baseline comparison. Both approaches agree on the small comparison dataset; the in-memory baseline was faster. Claim traceable connected behavior, not an unsupported accuracy/speed advantage.

If INC-13 already exists, Add incident will not overwrite it. For a repeated recording, use a fresh isolated demo graph or change its status through the supported API. Do not erase the main graph to stage a result.

## Questions to rehearse

| Question | Evidence-based answer |
|---|---|
| Why a graph? | Relevance depends on dependency paths, ownership and incident/history links. Changing a relevant edge changes the investigation scope. A competent adjacency-list implementation can also solve these cases; our small baseline shows parity. |
| Why FalkorDB? | It executes the bounded Cypher tools and persists the connected evidence and agent handoff. A graph outage stops current investigation; no canned fallback verdict is returned. |
| What does the agent do? | It selects allowed history/source reads, submits structured findings, and hands them to a separate verifier. Policy accepts only supported/current actions. |
| What is real? | Real FalkorDB, Gemini calls, saved jobs, source checksums and tasks. Company incidents, verification and historical records are synthetic. No real deployment or external ticket integration. |
| What fails? | Provider/network failures, unsupported findings, expired sources and changed revisions can withhold actions. Hard budgets can end a review incomplete or rejected. |
| What are the limits? | Single worker deployment, no authenticated multi-tenant API, no production deployment safety guarantee, small evaluation dataset, unproven disaster recovery. |

## Final gates

- Runtime UI and real provider smoke test: evidence in [UI review](UI-Redesign-Review.md).
- Reproducible setup: [README](../README.md) and [queued runtime](Durable-Investigations.md).
- Graph model and query implementation: [core report](First-Working-Core.md), [queries](../queries/dependencies.cypher).
- Before publication: review source/history/artifacts for credentials and check the selected repository content. Do not publish `.env`, `.local`, database volumes or browser profiles.
- Public repository created by the participant: https://github.com/Utkarsh18818/ReleaseGuard. Source publication must be verified against the remote commit.
- Narrated demo: https://youtu.be/qnejDVhVe-E; local MP4, captions, transcript and edit disclosures are in `demo/`.
- Registration and the actual submission form were inspected while signed in. Submission completion requires its own confirmation from the site. A localhost link is not a public deployment.

Highest-value final improvement: rehearse and record the same connected-evidence scenario end to end, explaining it in your own words. Avoid adding new features before those gates pass.
