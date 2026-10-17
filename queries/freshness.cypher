// Business-domain revision. This is NOT FalkorDB's schema-cache version parameter.
MATCH (s:DomainState {id:'domain'})
RETURN s.revision,s.generation,s.dirty
