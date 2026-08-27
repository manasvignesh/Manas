from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from crowdforge.agents.models import Agent
from crowdforge.simulation.models import SimulationEvent


class PossibleReaction(BaseModel):
    action: str
    weight: float = Field(ge=0, le=1)


class ReasoningResult(BaseModel):
    possible_reactions: list[PossibleReaction] = Field(default_factory=list)
    reason: str = ""


class ReasoningEngine(Protocol):
    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult: ...


class NoOpReasoningEngine:
    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        return ReasoningResult()

