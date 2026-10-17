POLICY_VERSION = "release-policy-v1"


def verdict(blockers: list, missing: list, stale: bool = False) -> str:
    if stale:
        return "Needs reassessment"
    if blockers:
        return "Blocked"
    if missing:
        return "Insufficient evidence"
    return "Ready"


def effective_status(report: dict, state: dict, now: int) -> tuple[str, str | None]:
    if state["dirty"]:
        return "Needs reassessment", "Interrupted domain mutation requires recovery"
    if report["generation"] != state["generation"] or report["revision"] != state["revision"]:
        return "Needs reassessment", "Connected evidence changed"
    if report["policy_version"] != POLICY_VERSION:
        return "Needs reassessment", "Release policy changed"
    if report.get("expires_at") is not None and report["expires_at"] <= now:
        return "Needs reassessment", "Verification evidence expired"
    return report["verdict"], None
