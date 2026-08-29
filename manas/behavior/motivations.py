from manas.agents.models import Agent
from manas.behavior.calibration import DEFAULT_CALIBRATION
from manas.behavior.models import Motivation, Perception
from manas.simulation.models import ProductScenario, SimulationEvent
from manas.utils.random import clamp


def motivations(agent: Agent, scenario: ProductScenario, event: SimulationEvent, perception: Perception) -> list[Motivation]:
    result = []
    if perception.perceived_problem_relevance > .35:
        result.append(Motivation(source="current goals", direction="toward", strength=perception.perceived_problem_relevance, reason="It connects to something this person is actively trying to change."))
    if perception.perceived_novelty > .55 and agent.personality.curiosity > .5:
        result.append(Motivation(source="curiosity", direction="toward", strength=clamp(perception.perceived_novelty * agent.personality.curiosity + .15), reason="The unfamiliar approach makes it worth investigating."))
    if perception.perceived_risk > .38:
        result.append(Motivation(source="risk", direction="away", strength=perception.perceived_risk, reason="Privacy, trust, or a past disappointment creates hesitation."))
    experience = agent.category_experiences.get(scenario.category)
    subscription_fatigue = scenario.pricing_model in {"monthly", "annual", "subscription"} and (
        any("subscription" in context.situation for context in agent.life_contexts)
        or any("subscription" in item.casefold() for item in agent.previous_experiences)
    )
    if subscription_fatigue:
        result.append(Motivation(source="subscription fatigue", direction="away", strength=.62,
            reason="A recent subscription experience makes another recurring commitment feel risky."))
    if experience and experience.products_used > 0 and experience.familiarity > .45:
        strength = clamp(experience.familiarity * DEFAULT_CALIBRATION.habit_strength)
        result.append(Motivation(source="existing alternative", direction="away", strength=strength,
            reason=f"An existing {scenario.category} routine already covers part of this need."))
    consistency_friction = (
        scenario.behavior_change_required > .6
        and agent.habit_strength > .62
        and (perception.perceived_problem_relevance > .35 or agent.state.fatigue > .45)
    )
    if consistency_friction:
        strength = clamp(perception.perceived_effort * agent.habit_strength * DEFAULT_CALIBRATION.habit_strength)
        result.append(Motivation(source="consistency friction", direction="away", strength=strength,
            reason="Keeping up another routine may be harder than starting it."))
    if scenario.price > 0:
        recurring_cost = 4 if scenario.pricing_model in {"monthly", "subscription"} else 1
        raw_burden = scenario.price * recurring_cost / max(agent.disposable_income, 1)
        price_level = scenario.price / (scenario.price + 300)
        burden = clamp(
            raw_burden / (1 + raw_burden)
            + agent.price_sensitivity * price_level * DEFAULT_CALIBRATION.price_sensitivity_strength
        )
        price_salient = burden > .70 or agent.price_sensitivity > .55 or agent.state.financial_pressure > .65
        if burden > .30 and price_salient:
            result.append(Motivation(source="money", direction="away", strength=clamp(burden * .75 + agent.state.financial_pressure * .35), reason="The cost competes with more immediate financial priorities."))
    if event.source_agent_id:
        result.append(Motivation(source="social proof", direction="toward" if event.sentiment >= 0 else "away", strength=clamp(event.intensity * agent.personality.social_conformity), reason="A person in the social circle made the idea harder to ignore."))
    return result
