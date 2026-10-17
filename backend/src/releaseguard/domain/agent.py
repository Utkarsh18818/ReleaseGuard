"""Strict proposal contracts. Model output never grants mutation authority."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class HistoryRequest(StrictModel):
    service_id: str = Field(min_length=1, max_length=100)


class SourceRequest(StrictModel):
    source_id: str = Field(min_length=1, max_length=100)


class Proposal(StrictModel):
    blocker_ids: list[str] = Field(max_length=200)
    avoid_attempt_ids: list[str] = Field(max_length=100)
    review_attempt_ids: list[str] = Field(max_length=100)
    source_ids: list[str] = Field(max_length=100)
    next_step: Literal[
        "review_historical_procedure", "resolve_blocker", "request_evidence", "no_action"
    ]


class Review(StrictModel):
    accept: bool
    reason: Literal["supported", "unsupported", "incomplete", "stale"]


def declaration(name, description, model):
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": model.model_json_schema(),
    }
