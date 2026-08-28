from __future__ import annotations

import logging
from typing import Any

from manas.agents.models import Agent
from manas.reasoning.base import NoOpReasoningEngine, ReasoningEngine, ReasoningResult
from manas.simulation.models import SimulationEvent


logger = logging.getLogger(__name__)


class ReasoningRouter:
    """Selectively requests expression help and always falls back safely."""

    def __init__(self, enhanced: ReasoningEngine, fallback: ReasoningEngine | None = None) -> None:
        self.enhanced = enhanced
        self.fallback = fallback or NoOpReasoningEngine()

    def should_enhance(self, context: dict[str, Any]) -> bool:
        decision = context.get("decision")
        if not decision:
            return False
        ranked = sorted(decision.probabilities.values(), reverse=True)
        close = len(ranked) > 1 and ranked[0] - ranked[1] < .08
        motives = decision.motivations
        conflict = (
            any(m["direction"] == "toward" and m["strength"] > .65 for m in motives)
            and any(m["direction"] == "away" and m["strength"] > .65 for m in motives)
        )
        return (
            close
            or conflict
            or decision.behavioral_mode in {"impulse", "defensive"}
            or context.get("high_influence", False)
        )

    async def reason(self, agent: Agent, event: SimulationEvent, context: dict[str, Any]) -> ReasoningResult:
        if not self.should_enhance(context):
            return await self.fallback.reason(agent, event, context)
        try:
            return await self.enhanced.reason(agent, event, context)
        except Exception as error:
            logger.warning("Local reasoning failed (%s); native decision retained", type(error).__name__)
            logger.debug("Local reasoning failure details", exc_info=True)
            return await self.fallback.reason(agent, event, context)
