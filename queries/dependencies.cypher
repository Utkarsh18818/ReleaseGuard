// Used by application/investigation.py. Application clamps depth/results and checks frontier.
// Values supplied as parameters; graph identity is server-configured.
MATCH (r:Release {id:$release})-[:HAS_CHANGE]->(c:Change)-[:TOUCHES]->(root:Service)
MATCH p=(root)-[:DEPENDS_ON*0..4]->(s:Service)
RETURN s.id,[n IN nodes(p) | n.id],[e IN relationships(p) | e.source_id],
       [e IN relationships(p) | e.fact_id],c.source_id,r.source_id,[e IN relationships(p) | e.version]
LIMIT 501
