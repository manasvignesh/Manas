import asyncio
from statistics import mean

from manas.behavior.engine import BehaviorEngine
from manas.behavior.perception import perceive
from manas.scenarios import parse_scenario
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import SimulationConfig, SimulationEvent
from manas.society.influence import influence_shift
from manas.utils.random import seeded


def golden_scenario(price=399):
    return parse_scenario(f"AI fitness coach for Indian college students at ₹{price}/month")


def run_golden(price=399):
    return asyncio.run(
        SimulationEngine().run(
            golden_scenario(price),
            SimulationConfig(population_size=100, days=14, seed=42),
        )
    )


def test_golden_society_has_multiple_paths_memory_cascades_and_grounded_insights():
    result = run_golden()
    actions = set(result.summary.actions)
    assert len({agent.id for agent in result.agents}) == 100
    assert {"reject", "search_reviews", "wait_for_discount", "ignore"} <= actions
    assert actions & {"buy_now", "subscribe", "try_once", "try_free"}
    assert all(decision.action in decision.consideration_set for decision in result.decisions)
    assert result.cascades
    assert any(memory.day > 1 for agent in result.agents for memory in agent.memories)
    assert result.summary.findings["strongest_pull"]
    assert result.summary.findings["biggest_resistance"]
    assert result.summary.real_world_tests


def test_price_replay_changes_sensitive_people_more_and_spares_low_relevance():
    agents = run_golden().agents
    event = SimulationEvent(id="replay", day=1, event_type="product_seen", target_agent_ids=[a.id for a in agents])
    engine = BehaviorEngine()
    sensitive = []
    insensitive = []
    relevance_changes = []
    for index, agent in enumerate(agents):
        def price_shift(person):
            high = engine.evaluate(person, golden_scenario(399), event, seeded(900, index))
            low = engine.evaluate(person, golden_scenario(199), event, seeded(900, index))
            actions = set(high.probabilities) | set(low.probabilities)
            distribution_shift = sum(
                abs(low.probabilities.get(action, 0) - high.probabilities.get(action, 0))
                for action in actions
            ) / 2
            return distribution_shift, high.factors["relevance"]
        sensitive_shift, relevance = price_shift(agent.model_copy(update={"price_sensitivity": .85}))
        insensitive_shift, _ = price_shift(agent.model_copy(update={"price_sensitivity": .2}))
        if relevance >= .4:
            sensitive.append(sensitive_shift)
            insensitive.append(insensitive_shift)
        natural_shift, natural_relevance = price_shift(agent)
        relevance_changes.append((natural_shift, natural_relevance))
    low_relevance = [shift for shift, relevance in relevance_changes if relevance < .25]
    relevant = [shift for shift, relevance in relevance_changes if relevance >= .55]
    assert mean(sensitive) > mean(insensitive)
    assert mean(low_relevance) < mean(relevant)


def test_privacy_event_creates_varied_risk_research_and_peer_effects():
    agents = run_golden().agents
    scenario = golden_scenario()
    event = SimulationEvent(
        id="privacy",
        day=8,
        event_type="privacy_concern",
        target_agent_ids=[a.id for a in agents],
        source_agent_id=agents[0].id,
        intensity=.85,
        sentiment=-.65,
        metadata={"topic": "privacy", "claim": "The coach may retain sensitive health data."},
    )
    evaluations = []
    shifts = []
    for index, agent in enumerate(agents):
        perception = perceive(agent, scenario, event)
        decision = BehaviorEngine().evaluate(agent, scenario, event, seeded(1200, index))
        evaluations.append((agent.privacy_sensitivity, perception.perceived_risk, decision.action))
        edge = {"trust": .15 + (index % 6) * .14, "strength": .5, "influence": .6}
        shifts.append(influence_shift(agent, edge, .75, -.7, .85)[0])
    high = [risk for sensitivity, risk, _ in evaluations if sensitivity >= .65]
    low = [risk for sensitivity, risk, _ in evaluations if sensitivity <= .35]
    actions = {action for _, _, action in evaluations}
    assert mean(high) > mean(low)
    assert actions & {"search_reviews", "ask_friend", "watch_demo", "compare_alternative"}
    assert any(action != "reject" for _, _, action in evaluations)
    assert len({round(shift, 3) for shift in shifts}) > 3
    assert any(abs(shift) < .01 for shift in shifts)
