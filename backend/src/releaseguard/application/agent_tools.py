"""Allowlisted read tools with scope, source and result bounds."""

from releaseguard.domain.agent import HistoryRequest, SourceRequest


class EvidenceTools:
    def __init__(self, store, evidence):
        self.store = store
        self.services = {p["service_id"] for p in evidence["paths"]}
        self.sources = set(evidence["sources"])

    def execute(self, name, arguments):
        if name == "read_history":
            request = HistoryRequest.model_validate(arguments)
            if request.service_id not in self.services:
                raise ValueError("History request outside release scope")
            rows = self.store.read(
                "MATCH (i:Incident)-[:AFFECTED]->(s:Service {id:$service}), "
                "(i)-[:HAD_ATTEMPT]->(a:Attempt) "
                "RETURN i.id,s.id,a.id,a.technique,a.outcome,a.source_id LIMIT 101",
                {"service": request.service_id},
            )
            if len(rows) > 100:
                raise ValueError("History tool result exceeds budget")
            return {
                "attempts": [
                    dict(
                        zip(
                            (
                                "incident_id",
                                "service_id",
                                "attempt_id",
                                "technique",
                                "observed_outcome",
                                "source_id",
                            ),
                            row,
                            strict=True,
                        )
                    )
                    for row in rows
                ]
            }
        if name == "read_source":
            request = SourceRequest.model_validate(arguments)
            if request.source_id not in self.sources:
                raise ValueError("Source request outside release scope")
            rows = self.store.read(
                "MATCH (s:Source {id:$id}) RETURN s.text,s.version,s.checksum LIMIT 2",
                {"id": request.source_id},
            )
            if len(rows) != 1:
                raise ValueError("Source missing or ambiguous")
            return {
                "source_id": request.source_id,
                "text": rows[0][0],
                "version": rows[0][1],
                "checksum": rows[0][2],
            }
        raise ValueError("Unknown agent tool")
