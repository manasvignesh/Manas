from manas.behavior.engine import BehaviorEngine
from manas.population.generator import PopulationGenerator
from manas.simulation.models import ProductScenario, SimulationEvent
from manas.utils.random import seeded


def test_decision_is_distribution_and_explainable():
    agent = PopulationGenerator(2).generate(1)[0]
    scenario = ProductScenario(name="Fitness app", description="workout coaching", price=399, pricing_model="monthly", category="fitness")
    event = SimulationEvent(id="e", day=1, event_type="friend_recommendation", target_agent_ids=[agent.id], intensity=.8, sentiment=.7)
    decision = BehaviorEngine().evaluate(agent, scenario, event, seeded(2, "test"))
    assert abs(sum(decision.probabilities.values()) - 1) < 1e-9
    assert set(decision.probabilities) == set(decision.consideration_set)
    assert decision.action in decision.consideration_set
    assert decision.behavioral_mode
    assert decision.perception
    assert decision.explanation
