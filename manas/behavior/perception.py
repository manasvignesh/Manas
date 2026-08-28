from manas.agents.models import Agent
from manas.behavior.models import Perception
from manas.simulation.models import ProductScenario, SimulationEvent
from manas.utils.random import clamp


def perceive(agent: Agent, scenario: ProductScenario, event: SimulationEvent) -> Perception:
    interests = {item.casefold() for item in agent.interests + agent.goals}
    themes = {theme for context in agent.life_contexts for theme in context.themes}
    category_match = scenario.category in interests or any(scenario.category in item for item in interests)
    context_match = scenario.category in themes or bool(themes & set(scenario.benefits))
    experience = agent.category_experiences.get(scenario.category)
    relevance = clamp(.12 + (.38 if category_match else 0) + (.32 if context_match else 0) + agent.state.motivation * .14)
    if scenario.price <= 0:
        affordability = 1
    else:
        recurring_cost = 4 if scenario.pricing_model in {"monthly", "subscription"} else 1
        burden = scenario.price * recurring_cost / max(agent.disposable_income, 1)
        sensitivity = .35 + agent.price_sensitivity * 1.3
        affordability = 1 - (burden * sensitivity) / (1 + burden * sensitivity)
    value = clamp(relevance * (.45 + affordability * .35) + (experience.satisfaction * .2 if experience else .08))
    novelty = clamp(scenario.novelty * .65 + agent.personality.novelty_seeking * .35)
    privacy_event = (
        event.event_type == "privacy_concern"
        or event.metadata.get("topic") == "privacy"
        or "privacy" in str(event.metadata.get("claim", "")).casefold()
    )
    event_risk = event.intensity * agent.privacy_sensitivity * .4 if privacy_event else 0
    risk = clamp(
        scenario.privacy_exposure * agent.privacy_sensitivity * .55
        + ((1 - experience.satisfaction) * .35 if experience else .15)
        + agent.personality.skepticism * .2
        + event_risk
    )
    effort = clamp(scenario.behavior_change_required * (.7 + agent.habit_strength * .3) + agent.state.fatigue * .15)
    status = clamp(agent.status_seeking * (.55 if scenario.novelty > .55 else .25))
    concerns = list(scenario.concerns)
    if effort > .62: concerns.append("effort and consistency")
    if experience and experience.satisfaction < .35: concerns.append(f"past disappointment with {scenario.category} products")
    if scenario.pricing_model in {"monthly", "subscription"} and (agent.personality.frugality > .55 or any("subscriptions" in c.themes for c in agent.life_contexts)):
        concerns.append("another recurring subscription")
    if relevance > .68 and value > .5: interpretation = "This could genuinely help with something that matters right now."
    elif risk > .62: interpretation = "The promise is interesting, but the risks feel hard to ignore."
    elif novelty > .68 and relevance < .5: interpretation = "An interesting new tool, though not obviously necessary."
    elif scenario.price > 0 and affordability < .35: interpretation = "Potentially useful, but difficult to justify at this price."
    else: interpretation = "Another option competing with familiar ways of doing this."
    return Perception(perceived_problem_relevance=relevance, perceived_value=value, perceived_novelty=novelty,
        perceived_risk=risk, perceived_status_value=status, perceived_effort=effort, interpretation=interpretation,
        salient_features=list(dict.fromkeys([*scenario.benefits, *scenario.technologies]))[:4], concerns=list(dict.fromkeys(concerns)))
