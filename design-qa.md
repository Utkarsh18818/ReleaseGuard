# Option 3 local design QA — October 18, 2026

final result: passed

Selected target: third displayed Product Design concept, “Every release has a history.” The source is retained at `.local/submission/option-3-reference.png`. Local implementation: http://127.0.0.1:8002/ . These checks were completed before publication. The user subsequently approved pushing and deploying the design; deployment evidence is recorded separately in docs/Public-Deployment.md.

## Visual comparison

The source and the rendered desktop were normalized to 1440 × 1024 and inspected together in `.local/submission/intro-comparison.png`. Checked the dark forest surface, large two-line ice-blue heading, spare navigation, left-hand copy and CTA, dominant right-hand video, orange playback control, graph atmosphere and bottom principles row. The generated UI illustration was replaced with the actual recorded ReleaseGuard workflow, with explicit recording/synthetic-data labels. Background art is a separate optimized generated asset, not a screenshot of the whole page.

Initial P2 issues corrected: headline overflow, loose heading rhythm, oversized first video treatment, and a missing mobile word space. Recaptured after fixes. No remaining P0/P1/P2 issue was found in the scoped design comparison. The custom reference lettering is approximated with licensed Archivo Black rather than copying MetaMask's proprietary typeface; exact letter shapes remain a P3 difference.

Desktop: `.local/submission/intro-desktop.png`. Mobile: `.local/submission/intro-mobile.png`. Full player: `.local/submission/intro-player.png`.

## Behavior and accessibility

Seven browser check groups passed: visible muted preview playback; persistent manual pause; full 2:39 video, English caption cues, Escape and focus restoration; desktop selected WCAG checks; entry into the working review UI, existing guide dialog and return to the introduction; 390 px layout and accessibility; and reduced-motion still poster with explicit play. No uncaught page errors were recorded. Axe WCAG 2 A/AA and 2.1 AA selected rules reported zero violations on the introduction at desktop and mobile sizes; this does not establish complete manual WCAG conformance.

Separate layout checks at 390, 600, 1000, 1440, 1500 and 1920 px found no horizontal page overflow. The real media endpoint test passed for byte-range delivery, WebVTT captions and refusal of unlisted filenames. Ruff passed. Application-only staging includes the actual media, background, font and font license.

## Boundary

The local design preview proxies read-only API requests to the existing public app. It does not connect directly to FalkorDB or admit model reviews. Review/edit actions are blocked in the preview. The agent, policy, persistence and deployed application were not changed or revalidated by this visual task. No new Gemini requests were needed. Full backend regression tests were not rerun; the focused media-delivery test and browser checks cover this change.
