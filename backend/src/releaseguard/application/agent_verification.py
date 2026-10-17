"""Independent deterministic evidence gate, in addition to model review."""

import hashlib

from releaseguard.domain.agent import Proposal


def verify(proposal: Proposal, evidence, trace):
    issues = []
    supported = {b["incident_id"] for b in evidence["blockers"] if b["supported"]}
    if set(proposal.blocker_ids) != supported:
        issues.append("Proposed blockers do not match complete supported evidence")
    history = {a["attempt_id"]: a for a in evidence["memory"]}
    retrieved = {
        a["attempt_id"]
        for step in trace
        if step["tool"] == "read_history"
        for a in step["result"]["attempts"]
    }
    cited = set(proposal.avoid_attempt_ids + proposal.review_attempt_ids)
    if cited - retrieved or cited - history.keys():
        issues.append("Historical attempt was not retrieved or is unknown")
    if set(proposal.avoid_attempt_ids) & set(proposal.review_attempt_ids):
        issues.append("Conflicting attempt recommendations")
    if any(
        "worsened" not in history[a]["observed_outcome"].lower()
        for a in proposal.avoid_attempt_ids
        if a in history
    ):
        issues.append("Avoid recommendation lacks recorded adverse outcome")
    if any(
        "worsened" in history[a]["observed_outcome"].lower()
        for a in proposal.review_attempt_ids
        if a in history
    ):
        issues.append("Adverse historical attempt proposed for review")
    if history and not cited:
        issues.append("Relevant historical attempts were not considered")
    adverse = {a for a, item in history.items() if "worsened" in item["observed_outcome"].lower()}
    if not adverse <= set(proposal.avoid_attempt_ids):
        issues.append("Relevant adverse historical attempts must be acknowledged")
    required = {s for b in evidence["blockers"] if b["supported"] for s in b["source_ids"]}
    required.update(history[a]["source_id"] for a in cited if a in history)
    if (
        not required <= set(proposal.source_ids)
        or set(proposal.source_ids) - evidence["sources"].keys()
    ):
        issues.append("Missing or unknown source citations")
    for source in evidence["sources"].values():
        if hashlib.sha256(source["text"].encode()).hexdigest() != source["checksum"]:
            issues.append("Source checksum mismatch")
    if evidence["missing_checks"] and proposal.next_step != "request_evidence":
        issues.append("Missing checks require evidence request")
    if proposal.next_step == "review_historical_procedure" and not proposal.review_attempt_ids:
        issues.append("Historical review requires a retrieved attempt")
    if supported and proposal.next_step == "no_action":
        issues.append("Open blocker cannot be ignored")
    return sorted(set(issues))
