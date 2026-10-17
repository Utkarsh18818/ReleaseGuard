# ReleaseGuard interface redesign brief — October 17

Target: existing release review application. Outcome: an engineering lead should understand the decision, evidence and next action without reading database or agent terminology.

Code inspection findings (not a visual audit):
- Technical background-job and tool traces precede the actual recommendation.
- Unfamiliar terms have no first-use explanation.
- Similar styling and heading size make primary and secondary information compete.
- Synthetic mutation controls sit alongside the everyday workflow.
- Rebuilding the entire DOM on polling can close evidence details or disrupt focus.

Redesign acceptance:
- Clearly state: ReleaseGuard checks whether a release is ready by following related service incidents, test evidence and previous failed fixes.
- One clear primary action: Review release.
- Lead with Ready / Blocked / Needs evidence / Review outdated, retaining the canonical policy status internally and in details.
- Explain why in a short sentence derived only from returned evidence.
- Display a real dependency path and allow inspecting the sources behind each relationship/finding.
- Put historical cautions and proposed next action beside the finding.
- Explain background progress in task language; put IDs, model calls and database timings under Technical details.
- Group synthetic event controls under a clearly labeled Demo lab.
- Preserve real backend actions, freshness, retry eligibility, explicit failures and synthetic-data labeling.
- Test desktop and narrow layouts, keyboard operation, loading, stale, missing evidence and provider failures.

Capture status: user approved local Playwright after the built-in browser failed to start. Desktop/mobile screenshots and interaction checks are now recorded in `outputs/ui-review`. See [the implementation review](UI-Redesign-Review.md) for evidence and limitations.
