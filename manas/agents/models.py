from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Personality(BaseModel):
    curiosity: float = Field(ge=0, le=1)
    impulsiveness: float = Field(ge=0, le=1)
    skepticism: float = Field(ge=0, le=1)
    risk_tolerance: float = Field(ge=0, le=1)
    social_conformity: float = Field(ge=0, le=1)
    novelty_seeking: float = Field(ge=0, le=1)
    frugality: float = Field(ge=0, le=1)


class DynamicState(BaseModel):
    mood: float = Field(default=0.5, ge=0, le=1)
    motivation: float = Field(default=0.5, ge=0, le=1)
    financial_pressure: float = Field(default=0.5, ge=0, le=1)
    product_trust: float = Field(default=0.2, ge=0, le=1)
    product_awareness: float = Field(default=0, ge=0, le=1)
    current_interest: float = Field(default=0.2, ge=0, le=1)
    urgency: float = Field(default=0.2, ge=0, le=1)
    peer_pressure: float = Field(default=0, ge=0, le=1)


class Memory(BaseModel):
    id: str
    day: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    content: str
    importance: float = Field(ge=0, le=1)
    emotional_weight: float = Field(ge=-1, le=1)
    source_agent_id: str | None = None

    def relevance(self, current_day: int) -> float:
        age = max(0, current_day - self.day)
        return self.importance * (0.5 ** (age / (3.0 + self.importance * 17.0)))


class ProductOpinion(BaseModel):
    awareness: float = 0
    interest: float = 0.2
    trust: float = 0.2
    perceived_value: float = 0.25
    price_acceptance: float = 0.3
    purchase_intent: float = 0.1
    recommendation_intent: float = 0.1

    @field_validator("awareness", "interest", "trust", "perceived_value", "price_acceptance", "purchase_intent", "recommendation_intent")
    @classmethod
    def valid_score(cls, value: float) -> float:
        return max(0.0, min(1.0, value))

    @property
    def sentiment(self) -> Literal["positive", "neutral", "negative"]:
        score = (self.interest + self.trust + self.perceived_value + self.purchase_intent) / 4
        return "positive" if score >= 0.58 else "negative" if score < 0.36 else "neutral"


class Agent(BaseModel):
    id: str
    name: str
    age: int = Field(ge=16, le=90)
    gender: str
    location: str
    region: str
    urbanicity: str
    occupation: str
    education: str
    languages: list[str]
    household: str
    income_band: str
    disposable_income: float = Field(ge=0)
    technology_familiarity: float = Field(ge=0, le=1)
    internet_usage: float = Field(ge=0, le=1)
    interests: list[str]
    goals: list[str]
    values: list[str]
    beliefs: list[str]
    personality: Personality
    state: DynamicState
    privacy_sensitivity: float = Field(ge=0, le=1)
    price_sensitivity: float = Field(ge=0, le=1)
    brand_sensitivity: float = Field(ge=0, le=1)
    status_seeking: float = Field(ge=0, le=1)
    habit_strength: float = Field(ge=0, le=1)
    trust_tendency: float = Field(ge=0, le=1)
    contradictions: list[str] = Field(default_factory=list, max_length=3)
    previous_experiences: list[str] = Field(default_factory=list)
    memories: list[Memory] = Field(default_factory=list)
    opinion: ProductOpinion = Field(default_factory=ProductOpinion)

    def remember(self, memory: Memory, limit: int = 40) -> None:
        self.memories.append(memory)
        self.memories.sort(key=lambda item: (item.importance, item.day), reverse=True)
        del self.memories[limit:]

    def relevant_memories(self, day: int, limit: int = 5) -> list[Memory]:
        return sorted(self.memories, key=lambda m: m.relevance(day), reverse=True)[:limit]
