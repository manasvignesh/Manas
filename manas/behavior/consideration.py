from manas.agents.models import Agent
from manas.behavior.models import ConsiderationSet, Motivation, Perception
from manas.simulation.models import ProductScenario, SimulationEvent


def build_consideration_set(agent: Agent, scenario: ProductScenario, event: SimulationEvent, perception: Perception, motives: list[Motivation]) -> ConsiderationSet:
    actions, reasons = ["ignore"], {"ignore": "The idea may not deserve more attention right now."}
    if perception.perceived_problem_relevance > .25 or perception.perceived_novelty > .55:
        actions += ["search_reviews", "compare_alternative"]
        reasons.update(search_reviews="Uncertainty can be reduced with outside evidence.", compare_alternative="Existing options provide a useful benchmark.")
    if event.source_agent_id:
        actions.append("ask_friend"); reasons["ask_friend"] = "The social source can provide more context."
    elif agent.household in {"joint family", "nuclear family", "couple"} and scenario.price > agent.disposable_income * .08:
        actions.append("ask_family"); reasons["ask_family"] = "The purchase may affect a shared budget."
    if scenario.price <= 0:
        actions += ["try_free", "try_once"]
        reasons.update(try_free="There is little financial downside to trying it.", try_once="A single attempt can reveal whether it helps.")
    else:
        actions += ["wait_for_discount", "save_for_later"]
        reasons.update(wait_for_discount="A better price could change the trade-off.", save_for_later="Interest exists, but the timing is difficult.")
        if perception.perceived_value > .48 or (agent.personality.impulsiveness > .78 and perception.perceived_problem_relevance > .5):
            action = "subscribe" if scenario.pricing_model in {"monthly", "annual", "subscription"} else "buy_now"
            actions.append(action); reasons[action] = "The expected benefit may justify paying now."
    if perception.perceived_risk > .65 or perception.perceived_problem_relevance < .16:
        actions.append("reject"); reasons["reject"] = "The concerns outweigh the perceived relevance."
    if event.event_type in {"feature_update", "positive_review", "influencer_mention"}:
        actions.append("watch_demo"); reasons["watch_demo"] = "Seeing the product in use could settle uncertainty."
    return ConsiderationSet(actions=list(dict.fromkeys(actions)), reasons=reasons)
