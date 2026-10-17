# Release review interface — October 17, 2026

The existing ReleaseGuard UI was inspected in a real local Chromium browser with explicit user approval after the built-in browser failed before loading. The redesign keeps the existing graph core, policy, model tools and durable worker workflow. This report describes product/design choices, not published hackathon requirements.

## Before: two captured steps

1. **Open release review:** [overview](../outputs/ui-review/01-before-overview.png), [full page](../outputs/ui-review/01-before-full.png). The actual decision competed with tool calls, background-job controls and raw identifiers. It was difficult to identify the user problem, current result and next action without scrolling through technical content.
2. **Inspect a source:** [source inspection](../outputs/ui-review/02-before-source.png). Evidence existed, but the screen did not clearly connect the source, dependency path, current finding and responsible owner.

This was a narrow two-step audit, not user research or a complete accessibility audit. The user's reported inability to understand the product was the motivating outcome; no new usability-study success rate is claimed.

## Implemented

- Decision first: Ready, Blocked, Review outdated, Needs evidence and Connection lost. Labels translate canonical backend statuses; raw values remain inspectable.
- A plain-language question, product explanation, one primary Review release action and a short guide.
- Actual dependency paths rendered as selectable service nodes, with source snapshot/version/checksum inspection. Arrows are derived from returned paths, not a decorative illustration. Reachability is explicitly distinguished from an outage.
- Blocker and historical-fix tabs, responsible team/tasks, and a next step derived from canonical evidence. Historical procedures retain their validation qualification.
- Persisted background-review progress in everyday language. Model/graph timings, calls and IDs are inside Technical details. An unfinished/failed model review stays separate from the earlier policy decision.
- Demo mutations moved into a clearly labeled synthetic-data dialog, including resolving the inserted Ledger incident. Production deployment remains outside the application.
- Polling preserves open source dialogs, expanded details and focus when their data has not changed. Keyboard tabs, Escape/focus restoration, mobile navigation and contained graph scrolling are implemented.
- Locally served Inter variable font and Lucide static icons; no runtime font/icon CDN. License files accompany assets. [Lucide license](https://lucide.dev/license).

Code: `backend/src/releaseguard/web/{index.html,styles.css,app.js}`. FastAPI serves packaged `/assets`; the source distribution and application image include the font/icon files. No frontend runtime framework or agent framework was added.

## Verification

Browser tests are in `backend/tests/ui`; install their pinned development dependencies with `npm ci --prefix backend/tests/ui`, then install Chromium with `npx --prefix backend/tests/ui playwright install chromium`. Set `RELEASEGUARD_UI_URL` to the running app and run `npm test --prefix backend/tests/ui`; use `npm run accessibility --prefix backend/tests/ui` for the axe scan. Invoke from the repository root so output and recorded fixture paths resolve.

The current workspace uses a local browser cache via `PLAYWRIGHT_BROWSERS_PATH` and has the same pinned packages in ignored `.local/ui-tools`. These tools are not application runtime dependencies.

Evidence in `outputs/ui-review`:

| Check | Evidence / scope |
|---|---|
| 11 browser interaction checks | `ui-test-results.json`; actual API reads plus explicitly labeled recorded response fixtures |
| Desktop 1440×1000 and mobile 390×844 | `03-redesign-desktop-viewport.png`, `05-redesign-mobile-viewport.png`; no document horizontal overflow in tested narrow layout |
| Real source inspection | `04-redesign-source.png`; dialog and focus survive polling |
| Contrast | Initial scan identified muted text failures. Corrected colors; desktop, guide, source-dialog and mobile scans report zero violations in selected WCAG A/AA checks (`accessibility.json`). This does not establish full accessibility conformance. |
| Backend/assets | `backend-tests.xml`; real isolated FalkorDB/Redis tests, plus static CSS/JS/icon/font HTTP serving |
| Live provider/worker | `live-ui-review-before-tool-choice.json` retains a rejected run; updated results are recorded separately rather than replacing that failure |

After the tool-choice correction, `live-ui-review-after-tool-choice.json` records a completed Ready review: four model calls, nine tool calls, no page errors. Measured execution: 66,039.51 ms wall, 48,432.85 ms model/API, 5,868.31 ms graph client (20.58 ms server, included in client), 11,738.35 ms other application. These are one cloud smoke-test sample, with checkpoint/freshness timing scope described in the saved run; not a controlled before/after latency comparison. The preceding failure is a different model outcome, not a valid performance baseline.

The final updated backend suite passes **50 tests** in 49.99 seconds with one existing Starlette TestClient deprecation warning. Ruff and pip dependency checks pass. The Docker application image/wheel built and the Linux API/worker/dispatcher were recreated successfully. Eleven browser checks pass against the deployed `http://127.0.0.1:8000`, including source-dialog polling/focus, keyboard tabs, mobile navigation, presentation fixtures, and a disconnected/reconnected API.

Blocked, outdated, missing-evidence, queue and dependency-failure route fixtures exercise UI presentation only; they are not proof of a real model outcome or database-failure recovery. The backend and separate live runs provide those distinct evidence categories. No measured model-speed or usability improvement is claimed from this redesign.

## Live failure discovered during QA

An actual cloud review returned no native function call on its third admitted model request; it was rejected with actions withheld. The request used Gemini's default tool choice, which permits text. The adapter now sets `generation_config.tool_choice = "any"` only when tools are supplied, matching the workflow's existing structured contract. That run had zero visible output tokens, so it was inaccurate to initially describe the response as prose. Ordinary text generation is unchanged. [Official function-calling modes](https://ai.google.dev/gemini-api/docs/function-calling).

The five-call/ten-tool budgets, source/freshness gates and deterministic policy remain in place. A real-graph regression verifies that prose-only model output cannot publish an assessment or task. This correction addresses the observed protocol choice; it does not guarantee provider availability or correct model findings.

A subsequent real Ledger review also returned no function call on its final investigator turn despite `tool_choice=any`: zero visible output tokens and 1,966 thought tokens, retained in `live-ledger-before-thinking-limit.json`. This strongly suggests reasoning exhausted the shared 2,048-token response cap; the old checkpoint did not save provider status, so this cause is an inference from usage and documented semantics. The adapter now selects `thinking_level=low` for structured tool turns without increasing token/call caps. Provider completion status and function-call count are saved in timing metadata. Explicit incomplete responses remain Incomplete with actions withheld, rather than being classified as rejected proposals. Hidden reasoning text is never saved or displayed. [Official token-limit guidance](https://ai.google.dev/gemini-api/docs/thinking).

## Actual changed-evidence demonstration

The real Demo lab action inserted synthetic INC-13 on Ledger. The previous Ready assessment at revision 3 immediately read as Needs reassessment after revision 4; the UI called it Review outdated. With the updated provider configuration, a fresh native workflow completed **Blocked** and persisted an open **Money** task supported by `checkout → payments → ledger → inc-13`. The earlier resolved Payments task was preserved. Four model calls and six tool calls were used; all provider turns recorded `requires_action` with native calls. No browser page errors were observed.

| Real cloud sample | Wall ms | Model/API ms | Graph client ms | Graph server ms (subset) | Other application ms |
|---|---:|---:|---:|---:|---:|
| Ready after tool-choice setting | 66,039.51 | 48,432.85 | 5,868.31 | 20.58 | 11,738.35 |
| Ledger case, rejected before thinking setting | 58,447.35 | 43,009.65 | 3,391.87 | 12.99 | 12,045.83 |
| Ledger case, completed after thinking setting | 70,194.38 | 49,948.02 | 5,565.02 | 21.55 | 14,681.33 |

These are individual, different model outcomes, not a controlled speed comparison. The successful Ledger run includes a verifier and action work missing from the failed run. No speedup is claimed. Model/API time and other application/lock time remain material demo waits.

Raw evidence: `live-ledger-scenario.json`, `08-live-graph-change-outdated.png`, `09-live-ledger-blocker.png`, `10-live-blocked-overview.png`. Silent rehearsal clips are in `outputs/submission` with explicit failure/separate-take labels. The recorded Blocked, outdated and missing-evidence presentation fixtures also have zero violations in the selected automated checks (`state-accessibility.json`). Open tasks sort first, and generated event sources use a readable label with the full ID retained in their details. The current main workspace intentionally retains the real Blocked case so the user can inspect its path and owner task.

## Remaining limits

Small synthetic company, no authenticated public deployment, no broad browser/device coverage or screen-reader study. Old tasks may cite sources absent from the current assessment snapshot; the source dialog states unavailable instead of inventing text. The map is bounded to 24 returned services and does not replace a full infrastructure topology view. Final narrated submission video and public repository are external handoff items; see [submission readiness](Submission-Readiness.md).
