from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InformationItem(BaseModel):
    id: str
    topic: str
    stance: Literal["positive", "mixed", "negative"]
    claim: str
    source_type: str
    credibility: float = Field(ge=0, le=1)
    emotional_intensity: float = Field(ge=0, le=1)
    origin_agent_id: str | None = None
    reached_agent_ids: list[str] = Field(default_factory=list)
    mutations: list[str] = Field(default_factory=list)


class SocialInteraction(BaseModel):
    id: str
    day: int
    speaker_id: str
    listener_id: str
    information_id: str
    relationship_type: str
    credibility: float = Field(ge=0, le=1)
    listener_reaction: str
    result: str
    opinion_shift: float = Field(ge=-1, le=1)


class OpinionCascade(BaseModel):
    information_id: str
    topic: str
    claim: str
    reached: int
    communities: list[str]
    key_agent_id: str | None = None


class CommunityInsight(BaseModel):
    name: str
    size: int
    most_discussed: str
    sentiment: str
    key_agent_id: str
