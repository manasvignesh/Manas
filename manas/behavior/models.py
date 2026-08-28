from typing import Literal

from pydantic import BaseModel, Field


class Perception(BaseModel):
    perceived_problem_relevance: float = Field(ge=0, le=1)
    perceived_value: float = Field(ge=0, le=1)
    perceived_novelty: float = Field(ge=0, le=1)
    perceived_risk: float = Field(ge=0, le=1)
    perceived_status_value: float = Field(ge=0, le=1)
    perceived_effort: float = Field(ge=0, le=1)
    interpretation: str
    salient_features: list[str]
    concerns: list[str]


class Motivation(BaseModel):
    source: str
    direction: Literal["toward", "away"]
    strength: float = Field(ge=0, le=1)
    reason: str


class ConsiderationSet(BaseModel):
    actions: list[str]
    reasons: dict[str, str]
