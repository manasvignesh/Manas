from manas.behavior.consideration import build_consideration_set
from manas.behavior.motivations import motivations
from manas.behavior.perception import perceive
from manas.population.generator import PopulationGenerator
from manas.scenarios import parse_scenario
from manas.simulation.models import SimulationEvent


def test_agents_have_diverse_active_contexts_and_category_history():
    agents = PopulationGenerator(42).generate(100)
    contexts = [tuple(context.situation for context in agent.life_contexts) for agent in agents]
    personality_vectors = {tuple(round(value, 3) for value in agent.personality.model_dump().values()) for agent in agents}
    assert all(agent.life_contexts for agent in agents)
    assert all(len(agent.category_experiences) >= 3 for agent in agents)
    assert len(set(contexts)) >= 20
    assert len(personality_vectors) >= 95
    assert len({tuple(agent.goals) for agent in agents}) >= 25
    assert len({tuple(agent.interests) for agent in agents}) >= 70


def test_same_product_is_perceived_differently():
    agents = PopulationGenerator(19).generate(60)
    scenario = parse_scenario("AI fitness coach for students at ₹399/month")
    event = SimulationEvent(id="e", day=1, event_type="product_seen", target_agent_ids=[])
    perceptions = [perceive(agent, scenario, event) for agent in agents]
    assert len({item.interpretation for item in perceptions}) >= 3
    assert max(item.perceived_problem_relevance for item in perceptions) - min(item.perceived_problem_relevance for item in perceptions) > .4
    assert any("another recurring subscription" in item.concerns for item in perceptions)


def test_motivations_conflict_and_consideration_is_contextual():
    agents = PopulationGenerator(7).generate(100)
    scenario = parse_scenario("AI fitness coach at ₹399/month")
    event = SimulationEvent(id="e", day=2, event_type="friend_recommendation", target_agent_ids=[], source_agent_id="friend", sentiment=.7, intensity=.8)
    found_conflict = False
    action_sets = set()
    for agent in agents:
        perception = perceive(agent, scenario, event)
        motives = motivations(agent, scenario, event, perception)
        directions = {item.direction for item in motives}
        found_conflict |= directions == {"toward", "away"}
        actions = build_consideration_set(agent, scenario, event, perception, motives).actions
        action_sets.add(tuple(actions))
    assert found_conflict
    assert len(action_sets) >= 3
    assert any("wait_for_discount" in actions for actions in action_sets)
    assert any("ask_friend" in actions for actions in action_sets)
