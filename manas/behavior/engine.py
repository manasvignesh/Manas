from __future__ import annotations

import random

from manas.agents.models import Agent
from manas.behavior.consideration import build_consideration_set
from manas.behavior.motivations import motivations
from manas.behavior.perception import perceive
from manas.simulation.models import Action, Decision, ProductScenario, SimulationEvent
from manas.utils.random import clamp


ACTIONS: tuple[Action, ...] = (
    "buy_now", "subscribe", "try_once", "try_free", "save_for_later", "wait_for_discount",
    "ask_friend", "ask_family", "search_reviews", "compare_alternative", "watch_demo", "share",
    "recommend", "criticize", "ignore", "reject", "uninstall", "cancel", "return_later",
)


def _multiply(weights: dict[str, float], names: set[str], value: float) -> None:
    for name in names & weights.keys():
        weights[name] *= value


class BehaviorEngine:
    """Conditional behavioral mechanisms over a person-specific consideration set."""

    def evaluate(self, agent: Agent, scenario: ProductScenario, event: SimulationEvent, rng: random.Random) -> Decision:
        perception = perceive(agent, scenario, event)
        motives = motivations(agent, scenario, event, perception)
        consideration = build_consideration_set(agent, scenario, event, perception, motives)
        weights = {action: rng.uniform(.78, 1.22) for action in consideration.actions}
        money_away = max((m.strength for m in motives if m.source == "money" and m.direction == "away"), default=0)
        toward = max((m.strength for m in motives if m.direction == "toward"), default=0)
        away = max((m.strength for m in motives if m.direction == "away"), default=0)
        modes = self._modes(agent, event, perception, money_away)
        mode = rng.choices([item[0] for item in modes], weights=[item[1] for item in modes], k=1)[0]

        # Relevance is a gate: disposable income cannot manufacture a need.
        if perception.perceived_problem_relevance < .2:
            _multiply(weights, {"ignore"}, 7)
            _multiply(weights, {"reject"}, 2.5)
            _multiply(weights, {"buy_now", "subscribe", "try_once"}, .08)
        elif perception.perceived_problem_relevance > .68:
            _multiply(weights, {"try_once", "try_free", "buy_now", "subscribe", "search_reviews"}, 2.1)
            _multiply(weights, {"ignore"}, .25)

        # The interest/affordability conflict branches rather than averaging out.
        if perception.perceived_problem_relevance > .55 and money_away > .48:
            _multiply(weights, {"wait_for_discount", "save_for_later", "try_free", "compare_alternative"}, 3.2)
            _multiply(weights, {"buy_now", "subscribe"}, .32)
            if mode == "impulse":
                _multiply(weights, {"buy_now", "subscribe"}, 5.5)
        elif money_away < .2 and perception.perceived_value > .55:
            _multiply(weights, {"buy_now", "subscribe", "try_once"}, 2.8)

        # Privacy plus trusted social proof commonly creates investigation, not binary rejection.
        if perception.perceived_risk > .55 and event.source_agent_id and event.sentiment > 0:
            _multiply(weights, {"search_reviews", "ask_friend", "watch_demo"}, 4)
            _multiply(weights, {"reject"}, 1.3)
        elif perception.perceived_risk > .7:
            _multiply(weights, {"reject", "search_reviews", "criticize"}, 2.7)

        self._apply_mode(mode, weights, agent)
        if toward > .65 and away > .65:
            _multiply(weights, {"search_reviews", "ask_friend", "ask_family", "return_later"}, 2.4)

        total = sum(weights.values()) or 1
        probabilities = {action: weight / total for action, weight in weights.items()}
        action = rng.choices(list(probabilities), weights=list(probabilities.values()), k=1)[0]
        reasons = self._explain(action, perception.interpretation, motives, consideration.reasons.get(action, ""), mode)
        factors = {
            "relevance": perception.perceived_problem_relevance, "value": perception.perceived_value,
            "risk": perception.perceived_risk, "effort": perception.perceived_effort,
            "money_conflict": money_away, "toward_conflict": toward, "away_conflict": away,
        }
        return Decision(agent_id=agent.id, day=event.day, action=action, probabilities=probabilities, factors=factors,
            explanation=reasons, perception=perception.model_dump(mode="json"),
            motivations=[item.model_dump(mode="json") for item in motives], consideration_set=consideration.actions,
            behavioral_mode=mode)

    def _modes(self, agent: Agent, event: SimulationEvent, perception, money_away: float) -> list[tuple[str, float]]:
        modes = [("ordinary", .35)]
        if agent.personality.impulsiveness > .52 and perception.perceived_problem_relevance > .4:
            modes.append(("impulse", agent.personality.impulsiveness * (1 + perception.perceived_novelty)))
        if agent.personality.skepticism > .5 or money_away > .4:
            modes.append(("careful evaluation", agent.personality.skepticism + agent.personality.frugality))
        if event.source_agent_id:
            modes.append(("social proof", agent.personality.social_conformity + event.intensity))
        if perception.perceived_problem_relevance > .58:
            modes.append(("goal-driven", perception.perceived_problem_relevance + agent.state.urgency))
        if perception.perceived_risk > .55:
            modes.append(("defensive", perception.perceived_risk + agent.state.stress))
        if perception.perceived_novelty > .58:
            modes.append(("curiosity", perception.perceived_novelty + agent.personality.curiosity))
        if perception.perceived_status_value > .45:
            modes.append(("status", perception.perceived_status_value + agent.status_seeking))
        return modes

    def _apply_mode(self, mode: str, weights: dict[str, float], agent: Agent) -> None:
        if mode == "impulse": _multiply(weights, {"buy_now", "subscribe", "try_once", "share"}, 3.5)
        elif mode == "careful evaluation": _multiply(weights, {"search_reviews", "compare_alternative", "wait_for_discount"}, 3.4)
        elif mode == "social proof": _multiply(weights, {"ask_friend", "try_once", "subscribe", "share"}, 2.8)
        elif mode == "goal-driven": _multiply(weights, {"buy_now", "subscribe", "try_once", "save_for_later"}, 2.6)
        elif mode == "defensive": _multiply(weights, {"search_reviews", "reject", "ignore", "criticize"}, 3)
        elif mode == "curiosity": _multiply(weights, {"watch_demo", "try_free", "search_reviews", "try_once"}, 3)
        elif mode == "status": _multiply(weights, {"buy_now", "subscribe", "share"}, 2.6)

    def _explain(self, action: str, interpretation: str, motives, action_reason: str, mode: str) -> list[str]:
        toward = sorted((m for m in motives if m.direction == "toward"), key=lambda m: m.strength, reverse=True)
        away = sorted((m for m in motives if m.direction == "away"), key=lambda m: m.strength, reverse=True)
        reasons = [interpretation]
        if toward: reasons.append(toward[0].reason)
        if away: reasons.append(away[0].reason)
        if action_reason: reasons.append(action_reason)
        return list(dict.fromkeys(reasons))[:4]
