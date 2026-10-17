# ReleaseGuard demonstration

[Watch the narrated MP4](ReleaseGuard-demo.mp4) · [Captions](captions.srt) · [Narration transcript](narration.txt)

Duration: approximately **2 minutes 39 seconds**. H.264 video, AAC audio, 1440×1080. Narration is locally synthesized with a stock Microsoft voice; it does not impersonate the participant.

This edited demonstration combines real localhost UI captures with result cards generated from measured run artifacts. The evidence-change and agent-review footage are separate recorded takes; waiting time is shortened and the edit is explicitly disclosed. Northstar company data is synthetic. FalkorDB queries, Gemini calls, reviews, tasks and freshness changes are real. No fabricated API responses establish the demonstrated outcomes.

The final cloud Ledger review completed Blocked, found `Checkout → Payments → Ledger → INC-13`, and persisted an open Money-owned task. It used four model requests and six tool calls. Wall time was 70,194.38 ms, model/API time 49,948.02 ms and graph-client time 5,565.02 ms. These are a single smoke-test sample, not a latency benchmark or speedup claim.

Prior rejected runs remain in `outputs/ui-review`. Fifty backend tests and eleven browser checks passed. The small same-facts graph comparison tied the adjacency baseline in correctness, with the in-memory baseline faster.

The MP4 was decoded end to end, narration had nonzero measured audio energy, and five exported frames were visually inspected. Caption timings are automatically allocated within narration segments; they are not manually word-aligned. `video-manifest.json` records scene timing and the edit disclosures.

AI assistance was used in project development, documentation, tests and this narration. The participant must understand and explain the submitted code and technical decisions; this video does not substitute for that understanding.
