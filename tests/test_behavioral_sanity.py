from collections import Counter

from manas.behavior.engine import BehaviorEngine
from manas.population.generator import PopulationGenerator
from manas.scenarios import parse_scenario
from manas.simulation.models import SimulationEvent
from manas.utils.random import seeded


PAYING = {"buy_now", "subscribe"}


def choices(agent, scenario, event, count=120):
    engine = BehaviorEngine()
    return Counter(engine.evaluate(agent, scenario, event, seeded(index, "sanity")).action for index in range(count))


def test_wealth_does_not_create_relevance():
    agent = PopulationGenerator(3).generate(1)[0]
    agent.disposable_income = 200_000
    agent.interests = ["music", "travel"]
    agent.goals = ["support family", "reduce stress"]
    agent.life_contexts = []
    scenario = parse_scenario("specialized cricket umpire training software at ₹99")
    event = SimulationEvent(id="e", day=1, event_type="product_seen", target_agent_ids=[agent.id])
    counts = choices(agent, scenario, event)
    assert sum(counts[action] for action in PAYING) < 12
    assert counts["ignore"] > 40


def test_low_income_goal_driven_impulsive_agent_can_still_subscribe():
    agent = PopulationGenerator(8).generate(1)[0]
    agent.disposable_income = 800
    agent.interests = ["fitness"]
    agent.goals = ["improve health"]
    agent.personality.impulsiveness = .96
    agent.state.motivation = .95
    scenario = parse_scenario("AI fitness coach at ₹399/month")
    event = SimulationEvent(id="e", day=1, event_type="friend_recommendation", target_agent_ids=[agent.id], source_agent_id="friend", sentiment=.8, intensity=.9)
    counts = choices(agent, scenario, event, 250)
    assert counts["subscribe"] > 0
    assert counts["wait_for_discount"] + counts["save_for_later"] > counts["subscribe"]


def test_privacy_concern_with_peer_proof_creates_research_not_uniform_rejection():
    agent = PopulationGenerator(12).generate(1)[0]
    agent.privacy_sensitivity = .98
    agent.personality.skepticism = .85
    agent.interests = ["fitness", "technology"]
    scenario = parse_scenario("AI fitness coach using health data at ₹399/month")
    event = SimulationEvent(id="e", day=2, event_type="friend_recommendation", target_agent_ids=[agent.id], source_agent_id="friend", sentiment=.8, intensity=.9)
    counts = choices(agent, scenario, event)
    assert counts["search_reviews"] > counts["reject"]
    assert len(counts) >= 3


def test_peer_recommendation_influences_some_not_everyone():
    agents = PopulationGenerator(22).generate(80)
    scenario = parse_scenario("AI fitness coach at ₹399/month")
    changed = 0
    unchanged = 0
    for index, agent in enumerate(agents):
        plain = SimulationEvent(id="p", day=2, event_type="product_seen", target_agent_ids=[agent.id])
        peer = SimulationEvent(id="s", day=2, event_type="friend_recommendation", target_agent_ids=[agent.id], source_agent_id="friend", sentiment=.8, intensity=.9)
        first = BehaviorEngine().evaluate(agent, scenario, plain, seeded(index, "peer"))
        second = BehaviorEngine().evaluate(agent, scenario, peer, seeded(index, "peer"))
        if first.action == second.action: unchanged += 1
        else: changed += 1
    assert changed > 5
    assert unchanged > 5
