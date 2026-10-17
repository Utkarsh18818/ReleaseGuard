import hashlib
import json
import time

from releaseguard.domain.models import DemoEvent


def apply_event(store, event: DemoEvent):
    payload = event.model_dump()
    key = "event-" + hashlib.sha256(event.request_key.encode()).hexdigest()
    source = "source-" + key
    with store.serialized():
        if event.kind == "incident_status":
            if event.value not in {"open", "resolved"}:
                raise ValueError("Incident status must be open or resolved")
            found = store.read("MATCH (i:Incident {id:$id}) RETURN i.id", {"id": event.entity_id})
        elif event.kind == "verification_result":
            if event.value not in {"pass", "fail", "expire"}:
                raise ValueError("Verification result must be pass, fail or expire")
            found = store.read(
                "MATCH (v:Verification {id:$id}) RETURN v.id", {"id": event.entity_id}
            )
        else:
            ids = [event.value] if event.kind == "new_incident" else [event.entity_id, event.value]
            found = store.read("MATCH (s:Service) WHERE s.id IN $ids RETURN s.id", {"ids": ids})
            if {r[0] for r in found} != set(ids):
                raise ValueError("Unknown service")
            if event.kind == "new_incident":
                current = store.read(
                    "MATCH (i:Incident {id:$id}) RETURN i.source_id", {"id": event.entity_id}
                )
                if current and current[0][0] != source:
                    raise ValueError("Incident identifier already exists")
        if not found:
            raise ValueError("Unknown event target")

        def apply():
            text = "Synthetic demo event: " + json.dumps(payload, sort_keys=True)
            store.write(
                "MERGE (s:Source:Entity {id:$id}) SET s.text=$text,s.synthetic=true,s.version=1,s.checksum=$checksum",
                {
                    "id": source,
                    "text": text,
                    "checksum": hashlib.sha256(text.encode()).hexdigest(),
                },
            )
            params = {"id": event.entity_id, "value": event.value, "source": source}
            if event.kind == "incident_status":
                store.write(
                    "MATCH (i:Incident {id:$id}) SET i.status=$value,i.source_id=$source,"
                    "i.version=coalesce(i.version,0)+1",
                    params,
                )
                if event.value == "resolved":
                    store.write(
                        "MATCH (t:Task)-[:JUSTIFIED_BY]->(:Incident {id:$id}) SET t.status='resolved'",
                        params,
                    )
                else:
                    store.write(
                        "MATCH (t:Task)-[:JUSTIFIED_BY]->(:Incident {id:$id}) SET t.status='open'",
                        params,
                    )
            elif event.kind == "verification_result":
                if event.value == "expire":
                    store.write(
                        "MATCH (v:Verification {id:$id}) SET v.expires_at=$now,v.source_id=$source",
                        {**params, "now": int(time.time()) - 1},
                    )
                else:
                    store.write(
                        "MATCH (v:Verification {id:$id}) SET v.result=$value,v.source_id=$source,v.expires_at=$expiry",
                        {**params, "expiry": int(time.time()) + 86400},
                    )
            elif event.kind == "new_incident":
                store.write(
                    "MATCH (s:Service {id:$value}) MERGE (i:Incident:Entity {id:$id}) "
                    "SET i.status='open',i.blocking=true,i.summary='New synthetic downstream incident',"
                    "i.source_id=$source,i.version=1 "
                    "MERGE (i)-[e:AFFECTED {fact_id:$id}]->(s) SET e.source_id=$source,e.version=1",
                    params,
                )
            elif event.kind == "remove_dependency":
                store.write(
                    "MATCH (:Service {id:$id})-[e:DEPENDS_ON]->(:Service {id:$value}) DELETE e",
                    params,
                )
            else:
                store.write(
                    "MATCH (a:Service {id:$id}),(b:Service {id:$value}) "
                    "MERGE (a)-[e:DEPENDS_ON {fact_id:$fact}]->(b) SET e.source_id=$source,e.version=1",
                    {**params, "fact": "dep-" + event.entity_id + "-" + event.value},
                )

        changed = store.journal(key, payload, apply)
        return {"applied": changed, "state": store.state()}
