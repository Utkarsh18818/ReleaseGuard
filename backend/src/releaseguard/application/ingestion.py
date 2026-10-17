import hashlib
import json

from releaseguard.domain.models import Dataset


def load_dataset(path) -> Dataset:
    data = Dataset.model_validate_json(path.read_text(encoding="utf-8"))
    data.validate_references()
    return data


def apply_source_metadata(store, rows):
    for id_, text in rows:
        updated = store.write(
            "MATCH (s:Source {id:$id}) WHERE s.text=$text SET s.checksum=$checksum RETURN s.id",
            {"id": id_, "text": text, "checksum": hashlib.sha256(text.encode()).hexdigest()},
        )
        if updated != [[id_]]:
            raise ValueError("Source changed during metadata reconciliation")


def seed(store, dataset: Dataset):
    dataset.validate_references()
    payload = dataset.model_dump()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    with store.serialized():
        store.initialize()

        def apply():
            for node in dataset.nodes:
                properties = dict(node.properties)
                if node.kind == "Source":
                    properties["checksum"] = hashlib.sha256(properties["text"].encode()).hexdigest()
                # kind is a validated Literal, never arbitrary query syntax.
                store.write(
                    f"MERGE (n:Entity {{id:$id}}) SET n:{node.kind} "
                    "SET n += $properties, n.version=1",
                    {"id": node.id, "properties": properties},
                )
            for edge in dataset.edges:
                store.write(
                    "MATCH (a:Entity {id:$start}),(b:Entity {id:$end}) "
                    f"MERGE (a)-[e:{edge.relation} {{fact_id:$id}}]->(b) "
                    "SET e.source_id=$source,e.version=1",
                    {"start": edge.start, "end": edge.end, "id": edge.id, "source": edge.source_id},
                )

        changed = store.journal("seed-" + digest, {"kind": "seed", "dataset": payload}, apply)
        # Early development seed predates checksum fields; reconcile without resetting domain facts.
        rows = store.read(
            "MATCH (s:Source) WHERE s.checksum IS NULL RETURN s.id,s.text ORDER BY s.id"
        )
        if rows:
            metadata = {"kind": "source_metadata", "rows": rows}
            key = (
                "metadata-"
                + hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
            )
            changed = (
                store.journal(key, metadata, lambda: apply_source_metadata(store, rows)) or changed
            )
        return changed
