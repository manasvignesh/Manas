from __future__ import annotations

from manas.agents.models import Agent
from manas.simulation.models import ProductScenario, SimulationEvent
from manas.utils.random import clamp


def interest(agent: Agent, scenario: ProductScenario) -> float:
    text = f"{scenario.name} {scenario.description} {scenario.problem_solved} {scenario.category} {' '.join(scenario.features)}".lower()
    matches = sum(1 for item in agent.interests + agent.goals if any(word in text for word in item.lower().split()))
    return clamp(.15 + matches * .18 + agent.state.current_interest * .35 + agent.personality.curiosity * .2)


def financial(agent: Agent, scenario: ProductScenario) -> float:
    if scenario.price <= 0:
        return .9
    affordability = agent.disposable_income / max(scenario.price * (4 if scenario.pricing_model in {"monthly", "subscription"} else 1), 1)
    return clamp(affordability / 4 - agent.price_sensitivity * .48 - agent.state.financial_pressure * .3 + .42)


def trust(agent: Agent, event: SimulationEvent) -> float:
    valence = {"positive_review": .18, "friend_recommendation": .23, "peer_purchase": .16, "negative_review": -.25, "friend_criticism": -.22, "peer_rejection": -.16}.get(event.event_type, 0)
    return clamp(agent.opinion.trust * .5 + agent.trust_tendency * .3 + valence * event.intensity + .1)


def social(agent: Agent, event: SimulationEvent) -> float:
    direct = .65 if event.source_agent_id else .2
    return clamp(agent.state.peer_pressure * .35 + agent.personality.social_conformity * direct * event.intensity)


def memory(agent: Agent, day: int) -> float:
    memories = agent.relevant_memories(day)
    if not memories:
        return 0
    return clamp(sum(m.emotional_weight * m.relevance(day) for m in memories) / max(1, len(memories)), -1, 1)


def contradiction(agent: Agent) -> float:
    if not agent.contradictions:
        return 0
    directions = []
    for text in agent.contradictions:
        lower = text.lower()
        if "impulse" in lower or "fitness products" in lower or "free trials" in lower or "novel apps" in lower:
            directions.append(agent.personality.impulsiveness * .25)
        if "privacy" in lower:
            directions.append((.5 - agent.privacy_sensitivity) * .2)
    return clamp(sum(directions), -.3, .3)


def all_modifiers(agent: Agent, scenario: ProductScenario, event: SimulationEvent) -> dict[str, float]:
    return {
        "interest": interest(agent, scenario), "financial": financial(agent, scenario),
        "trust": trust(agent, event), "social": social(agent, event), "memory": memory(agent, event.day),
        "goal": clamp(agent.state.motivation * .55 + interest(agent, scenario) * .45),
        "emotion": agent.state.mood - .5, "contradiction": contradiction(agent),
        "urgency": agent.state.urgency, "novelty": agent.personality.novelty_seeking,
        "risk": agent.personality.risk_tolerance,
    }
