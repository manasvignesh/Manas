from __future__ import annotations

from manas.agents.models import Agent
from manas.simulation.models import Decision
from manas.society.models import InformationItem
from manas.utils.random import clamp


def information_from_decision(identifier: str, agent: Agent, decision: Decision) -> InformationItem:
    concerns = decision.perception.get("concerns", [])
    if decision.action in {"wait_for_discount", "save_for_later"}:
        topic, stance, claim = "price", "mixed", "It looks useful, but the current price is difficult to justify."
    elif "privacy" in " ".join(concerns).casefold():
        topic, stance, claim = "privacy", "negative", "The product may ask for more personal data than feels comfortable."
    elif decision.action in {"buy_now", "subscribe", "recommend", "share"}:
        topic, stance, claim = "results", "positive", "The expected benefit looks strong enough to try."
    elif decision.action in {"reject", "criticize"}:
        topic, stance, claim = "value", "negative", "The product does not seem better than familiar alternatives."
    else:
        topic, stance, claim = "uncertainty", "mixed", "It might help, but more evidence is needed first."
    return InformationItem(id=identifier, topic=topic, stance=stance, claim=claim, source_type="peer",
        credibility=clamp((agent.opinion.trust + agent.trust_tendency) / 2),
        emotional_intensity=clamp(abs(agent.opinion.interest - .5) + .35), origin_agent_id=agent.id,
        reached_agent_ids=[agent.id])


def interpreted_claim(item: InformationItem, listener: Agent) -> str:
    if item.topic == "price" and listener.price_sensitivity > .65:
        return "People like the idea, but say the price may be too high for regular use."
    if item.topic == "privacy" and listener.privacy_sensitivity > .65:
        return "There may be a serious privacy trade-off behind the product's convenience."
    if item.topic == "results" and listener.personality.skepticism > .65:
        return "Someone expects good results, although that has not been proven yet."
    return item.claim
