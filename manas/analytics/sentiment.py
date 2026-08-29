from __future__ import annotations

from manas.agents.models import Agent
from manas.simulation.models import Decision


POSITIVE_ACTIONS = {"buy_now", "subscribe", "try_once", "try_free", "recommend", "share"}
NEGATIVE_ACTIONS = {"reject", "criticize", "uninstall", "cancel"}
CURIOUS_ACTIONS = {"search_reviews", "compare_alternative", "watch_demo", "ask_friend", "ask_family", "save_for_later", "wait_for_discount", "return_later"}


def classify_sentiment(agent: Agent, decisions: list[Decision]) -> str:
    latest = decisions[-1].action if decisions else None
    opinion = agent.opinion
    favorable = (opinion.interest + opinion.perceived_value + opinion.trust) / 3
    if latest in NEGATIVE_ACTIONS and favorable < .42:
        return "negative"
    if latest in POSITIVE_ACTIONS and favorable >= .34:
        return "positive"
    if latest in CURIOUS_ACTIONS:
        return "positive" if favorable >= .58 else "neutral"
    if latest == "ignore":
        return "negative" if favorable < .20 and opinion.trust < .2 else "neutral"
    if favorable >= .58 and opinion.purchase_intent >= .18:
        return "positive"
    if favorable < .2 and opinion.trust < .16:
        return "negative"
    return "neutral"
