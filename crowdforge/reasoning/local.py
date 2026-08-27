from __future__ import annotations

from typing import Any, Protocol

from crowdforge.agents.models import Agent
from crowdforge.reasoning.base import ReasoningResult
from crowdforge.simulation.models import SimulationEvent


class StructuredReasoningProvider(Protocol):
    async def complete_json(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class LocalReasoningEngine:
    """Optional provider-neutral adapter; CrowdForge never downloads a model implicitly."""

    def __init__(self, provider: StructuredReasoningProvider) -> None:
        self.provider = provider

    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        payload = {"agent": agent.model_dump(mode="json", exclude={"memories"}), "event": event.model_dump(mode="json"), "context": context}
        return ReasoningResult.model_validate(await self.provider.complete_json(payload))

