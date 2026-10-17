import json

from releaseguard.application.actions import persist_task
from releaseguard.application.ingestion import apply_source_metadata, seed
from releaseguard.application.mutations import apply_event
from releaseguard.domain.models import Dataset, DemoEvent


def recover(store):
    with store.serialized():
        if not store.state()["dirty"]:
            return {"recovered": False, "reason": "No pending mutation"}
        rows = store.read(
            "MATCH (s:DomainState {id:'domain'}),(c:Command) "
            "WHERE c.id=s.command_id RETURN c.id,c.payload"
        )
        if len(rows) != 1:
            raise ValueError("Pending journal cannot be resolved; fresh verdicts remain disabled")
        key, encoded = rows[0]
        payload = json.loads(encoded)
    # Every replay operation reacquires the same cross-process lock and validates its command key.
    if payload.get("kind") == "seed":
        seed(store, Dataset.model_validate(payload["dataset"]))
    elif payload.get("kind") == "task":
        with store.serialized():
            store.journal(key, payload, lambda: persist_task(store, payload))
    elif payload.get("kind") == "source_metadata":
        with store.serialized():
            store.journal(key, payload, lambda: apply_source_metadata(store, payload["rows"]))
    else:
        apply_event(store, DemoEvent.model_validate(payload))
    return {"recovered": not store.state()["dirty"], "command_id": key}
