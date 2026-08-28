import asyncio

from manas.scenarios import parse_scenario
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import SimulationConfig


def golden_result():
    return asyncio.run(SimulationEngine().run(
        parse_scenario("AI fitness coach for college students at ₹399/month"),
        SimulationConfig(population_size=100, days=14, seed=42),
    ))


def test_opinion_cascade_emerges_from_actual_transmissions():
    result = golden_result()
    assert result.cascades
    interaction_info = {item.information_id for item in result.social_interactions}
    assert all(cascade.information_id in interaction_info for cascade in result.cascades)
    assert all(cascade.reached >= 4 for cascade in result.cascades)
    assert any(len(cascade.communities) >= 2 for cascade in result.cascades)
    assert any("spread" in insight for insight in result.summary.insights)


def test_social_groups_have_meaningful_names_and_evidence():
    result = golden_result()
    assert result.communities
    assert any("student circle" in group.name for group in result.communities)
    assert all(group.size >= 3 for group in result.communities)
    assert all(group.most_discussed for group in result.communities)
    assert all(group.key_agent_id for group in result.communities)
