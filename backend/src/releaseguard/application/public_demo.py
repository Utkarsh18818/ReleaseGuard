"""Persistent shared-demo admission. This is a spending bound, not user authentication."""

import time

from releaseguard.application.jobs import TERMINAL


class PublicReviewLimit(ValueError):
    pass


def submit_public_review(jobs, release, clock=time.time):
    if release != "checkout-v2.4":
        raise ValueError("The public demo supports only Checkout v2.4")
    now = int(clock())
    day = now // 86400
    with jobs.store.serialized():
        latest = jobs.latest(release)
        # Share active/recent reviews across visitors instead of charging for every click.
        if latest and (latest["state"] not in TERMINAL or now - latest["created_at"] < 600):
            return latest
        rows = jobs.store.read(
            "MATCH (b:PublicReviewBudget {id:$day}) RETURN b.used", {"day": str(day)}
        )
        used = int(rows[0][0]) if rows else 0
        if used >= 12:
            raise PublicReviewLimit(
                "The shared demo's daily AI review limit is reached. "
                "Saved evidence and review results remain available."
            )
        # Reserve before dispatch. A crash may consume a slot but cannot reset the bound.
        jobs.store.write(
            "MERGE (b:PublicReviewBudget {id:$day}) SET b.used=$used",
            {"day": str(day), "used": used + 1},
        )
        return jobs.submit(release, f"public-{day}-{used + 1}")
