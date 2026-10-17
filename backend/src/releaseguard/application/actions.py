import json


def persist_task(store, payload):
    blocker = payload["blocker"]
    store.write(
        "MATCH (r:Release {id:$release}),(i:Incident {id:$incident}),"
        "(o:Team {id:$owner}) MERGE (t:Task {id:$id}) "
        "SET t.status='open',t.evidence=$evidence "
        "MERGE (t)-[:BLOCKS]->(r) MERGE (t)-[:JUSTIFIED_BY]->(i) "
        "MERGE (t)-[:ASSIGNED_TO]->(o)",
        {
            "release": payload["release"],
            "incident": blocker["incident_id"],
            "owner": blocker["owner"]["id"],
            "id": payload["id"],
            "evidence": json.dumps(blocker),
        },
    )
