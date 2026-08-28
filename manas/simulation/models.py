from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Action = Literal["buy", "try_free", "research", "ask_friend", "ignore", "reject"]


class ProductScenario(BaseModel):
    name: str
    description: str
    problem_solved: str = ""
    target_audience: str = "general consumers"
    price: float = Field(default=0, ge=0)
    pricing_model: str = "one-time"
    features: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    category: str = "general"
    secondary_categories: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    behavior_change_required: float = Field(default=0.3, ge=0, le=1)
    privacy_exposure: float = Field(default=0.1, ge=0, le=1)
    novelty: float = Field(default=0.4, ge=0, le=1)
    raw_input: str = ""


class SimulationEvent(BaseModel):
    id: str
    day: int = Field(ge=0)
    event_type: str
    target_agent_ids: list[str]
    source_agent_id: str | None = None
    intensity: float = Field(default=0.5, ge=0, le=1)
    sentiment: float = Field(default=0, ge=-1, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    agent_id: str
    day: int
    action: Action
    probabilities: dict[str, float]
    factors: dict[str, float]
    explanation: list[str]


class SimulationConfig(BaseModel):
    population_size: int = Field(default=100, ge=1, le=10_000)
    days: int = Field(default=30, ge=1, le=365)
    seed: int = 42
    population_pack: str = "india_v1"
    debug: bool = False


class SimulationSummary(BaseModel):
    run_id: str
    seed: int
    population_size: int
    days: int
    interactions: int
    opinion_changes: int
    actions: dict[str, int]
    sentiment: dict[str, float]
    average_purchase_intent: float
    insights: list[str]
    disclaimer: str = "Results represent a synthetic population under selected assumptions, not real-world survey statistics."


class DayReport(BaseModel):
    """Structured presentation event emitted after one simulated day."""

    day: int
    total_days: int
    reactions: int
    events: int
    awareness: int
    opinion_changes: int
    actions: dict[str, int]
