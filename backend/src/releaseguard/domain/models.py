from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

KINDS = {"Source", "Service", "Team", "Release", "Change", "Incident", "Attempt", "Verification"}
RELATIONS = {
    "DEPENDS_ON",
    "OWNED_BY",
    "HAS_CHANGE",
    "TOUCHES",
    "AFFECTED",
    "HAD_ATTEMPT",
    "VERIFIES",
}


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    kind: Literal[
        "Source", "Service", "Team", "Release", "Change", "Incident", "Attempt", "Verification"
    ]
    properties: dict


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    start: str
    end: str
    relation: Literal[
        "DEPENDS_ON", "OWNED_BY", "HAS_CHANGE", "TOUCHES", "AFFECTED", "HAD_ATTEMPT", "VERIFIES"
    ]
    source_id: str


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    synthetic: Literal[True]
    name: str
    nodes: list[Node] = Field(max_length=500)
    edges: list[Edge] = Field(max_length=1000)

    def validate_references(self):
        ids = {node.id for node in self.nodes}
        sources = {node.id for node in self.nodes if node.kind == "Source"}
        if len(ids) != len(self.nodes) or len({edge.id for edge in self.edges}) != len(self.edges):
            raise ValueError("Duplicate identifiers")
        for node in self.nodes:
            if any(
                not isinstance(value, (str, int, float, bool, type(None)))
                for value in node.properties.values()
            ):
                raise ValueError("Only scalar fixture properties are supported")
            if "id" in node.properties or "kind" in node.properties:
                raise ValueError("Reserved property")
            if node.kind != "Source" and node.properties.get("source_id") not in sources:
                raise ValueError("Node has no valid source")
            if node.kind == "Source" and (
                node.properties.get("synthetic") is not True
                or not isinstance(node.properties.get("text"), str)
                or len(node.properties["text"]) > 4000
            ):
                raise ValueError("Sources must be bounded and explicitly synthetic")
            required = {
                "Team": ("name",),
                "Service": ("name",),
                "Release": ("name",),
                "Change": ("name",),
                "Incident": ("summary", "status", "blocking"),
                "Attempt": ("technique", "outcome"),
                "Verification": ("check_type", "result", "expires_at"),
                "Source": ("text",),
            }
            if any(field not in node.properties for field in required[node.kind]):
                raise ValueError("Required domain properties are missing")
            if node.kind == "Incident" and (
                node.properties["status"] not in {"open", "resolved"}
                or type(node.properties["blocking"]) is not bool
            ):
                raise ValueError("Invalid incident status/blocking evidence")
            if node.kind == "Verification" and (
                node.properties["result"] not in {"pass", "fail"}
                or type(node.properties["expires_at"]) is not int
            ):
                raise ValueError("Invalid verification result/expiry")
        for edge in self.edges:
            if edge.start not in ids or edge.end not in ids or edge.source_id not in sources:
                raise ValueError("Broken relationship/source reference")
        kinds = {node.id: node.kind for node in self.nodes}
        endpoints = {
            "DEPENDS_ON": ("Service", "Service"),
            "OWNED_BY": ("Service", "Team"),
            "HAS_CHANGE": ("Release", "Change"),
            "TOUCHES": ("Change", "Service"),
            "AFFECTED": ("Incident", "Service"),
            "HAD_ATTEMPT": ("Incident", "Attempt"),
            "VERIFIES": ("Verification", "Release"),
        }
        for edge in self.edges:
            if (kinds[edge.start], kinds[edge.end]) != endpoints[edge.relation]:
                raise ValueError("Relationship endpoint types are invalid")


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_key: str = Field(min_length=1, max_length=100)


class DemoEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal[
        "incident_status",
        "verification_result",
        "remove_dependency",
        "add_dependency",
        "new_incident",
    ]
    entity_id: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=100)
    request_key: str = Field(min_length=1, max_length=100)
