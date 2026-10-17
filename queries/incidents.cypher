MATCH (i:Incident)-[e:AFFECTED]->(s:Service)
WHERE s.id IN $ids AND i.status='open' AND i.blocking=true
RETURN i.id,i.summary,s.id,i.source_id,e.source_id
LIMIT 201
