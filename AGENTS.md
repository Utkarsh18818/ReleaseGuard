# ReleaseGuard workspace
Read docs/ReleaseGuard-Project-Plan.md before implementation. Main coding and design begin October 15, 2026, 12:01 AM IST; deadline October 18, 11:59 PM IST.
Use the modular monolith architecture, essential FalkorDB, real evidence, persistent memory, idempotent actions, deterministic policy, and freshness checks in the plan.
The first deterministic graph-backed core was implemented October 15. Read docs/First-Working-Core.md for actual features, tests, measurements and remaining limitations. A bounded Gemini investigator/verifier workflow is now implemented. Read docs/Gemini-Agent-Workflow.md for live evidence and remaining limits.

Read docs/ReleaseGuard-Requirements-Specification.md and docs/ReleaseGuard-Implementation-Pathway.md before coding. They refine the main plan with researched requirements, single-writer recovery, read-time freshness/expiry, domain revision, bounded real tool calls, and acceptance gates. Research date: October 14, 2026. Distinguish their original proposals from the verified implementation report.

October 17: Read docs/Durable-Investigations.md for queued HTTP 202 workflows, Linux API/worker/dispatcher roles, recovery evidence, current measurements and limits. Use container CLI for writes to the active runtime; do not mix Windows and Linux writer locks.
