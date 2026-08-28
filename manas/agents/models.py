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
    attention: float = Field(default=0.5, ge=0, le=1)
    curiosity: float = Field(default=0.5, ge=0, le=1)
    stress: float = Field(default=0.3, ge=0, le=1)
    skepticism: float = Field(default=0.5, ge=0, le=1)
    social_pressure: float = Field(default=0, ge=0, le=1)
    fatigue: float = Field(default=0.1, ge=0, le=1)
    satisfaction: float = Field(default=0, ge=0, le=1)
    regret: float = Field(default=0, ge=0, le=1)


class LifeContext(BaseModel):
    situation: str
    description: str
    themes: list[str]
    urgency: float = Field(ge=0, le=1)
    financial_effect: float = Field(ge=-1, le=1)
    remaining_days: int = Field(default=30, ge=0)


class CategoryExperience(BaseModel):
    category: str
    products_used: int = Field(default=0, ge=0)
    paid_before: bool = False
    satisfaction: float = Field(default=0.5, ge=0, le=1)
    familiarity: float = Field(default=0.2, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class Memory(BaseModel):
    id: str
    day: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    content: str
    importance: float = Field(ge=0, le=1)
    emotional_weight: float = Field(ge=-1, le=1)
    source_agent_id: str | None = None
    category: str = "general"
    topics: list[str] = Field(default_factory=list)

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
    life_contexts: list[LifeContext] = Field(default_factory=list)
    category_experiences: dict[str, CategoryExperience] = Field(default_factory=dict)
    memories: list[Memory] = Field(default_factory=list)
    opinion: ProductOpinion = Field(default_factory=ProductOpinion)

    def remember(self, memory: Memory, limit: int = 40) -> None:
        self.memories.append(memory)
        self.memories.sort(key=lambda item: (item.importance, item.day), reverse=True)
        del self.memories[limit:]

    def relevant_memories(self, day: int, limit: int = 5, topics: set[str] | None = None) -> list[Memory]:
        def score(memory: Memory) -> float:
            overlap = len(topics & set(memory.topics + [memory.category])) if topics else 0
            return memory.relevance(day) * (1 + .65 * overlap)
        return sorted(self.memories, key=score, reverse=True)[:limit]
