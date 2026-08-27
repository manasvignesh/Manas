from __future__ import annotations

from typing import Any

from crowdforge.agents.models import Agent
from crowdforge.reasoning.base import PossibleReaction, ReasoningResult
from crowdforge.simulation.models import SimulationEvent


class MockReasoningEngine:
    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        decision = context.get("decision")
        if not decision:
            return ReasoningResult()
        ranked = sorted(decision.probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
        return ReasoningResult(possible_reactions=[PossibleReaction(action=a, weight=w) for a, w in ranked],
                               reason="Structured behavioral factors produced several plausible reactions.")

