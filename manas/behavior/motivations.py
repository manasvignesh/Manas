from manas.agents.models import Agent
from manas.behavior.models import Motivation, Perception
from manas.simulation.models import ProductScenario, SimulationEvent
from manas.utils.random import clamp


def motivations(agent: Agent, scenario: ProductScenario, event: SimulationEvent, perception: Perception) -> list[Motivation]:
    result = []
    if perception.perceived_problem_relevance > .35:
        result.append(Motivation(source="current goals", direction="toward", strength=perception.perceived_problem_relevance, reason="It connects to something this person is actively trying to change."))
    if perception.perceived_novelty > .55 and agent.personality.curiosity > .5:
        result.append(Motivation(source="curiosity", direction="toward", strength=clamp(perception.perceived_novelty * agent.personality.curiosity + .15), reason="The unfamiliar approach makes it worth investigating."))
    if perception.perceived_risk > .3:
        result.append(Motivation(source="risk", direction="away", strength=perception.perceived_risk, reason="Privacy, trust, or a past disappointment creates hesitation."))
    if perception.perceived_effort > .5:
        result.append(Motivation(source="habit", direction="away", strength=perception.perceived_effort * agent.habit_strength, reason="Using it consistently would disrupt an established routine."))
    if scenario.price > 0:
        burden = clamp(scenario.price * (4 if scenario.pricing_model in {"monthly", "subscription"} else 1) / max(agent.disposable_income, 1))
        if burden > .15:
            result.append(Motivation(source="money", direction="away", strength=clamp(burden * .75 + agent.state.financial_pressure * .35), reason="The cost competes with more immediate financial priorities."))
    if event.source_agent_id:
        result.append(Motivation(source="social proof", direction="toward" if event.sentiment >= 0 else "away", strength=clamp(event.intensity * agent.personality.social_conformity), reason="A person in the social circle made the idea harder to ignore."))
    return result
