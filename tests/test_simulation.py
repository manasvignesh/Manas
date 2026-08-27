import asyncio

from manas.simulation.engine import SimulationEngine
from manas.simulation.models import ProductScenario, SimulationConfig


def run(seed=42):
    return asyncio.run(SimulationEngine().run(ProductScenario(name="AI fitness coach", description="Personalized fitness", price=399, pricing_model="monthly", category="fitness"), SimulationConfig(population_size=35, days=10, seed=seed)))


def fingerprint(result):
    return [(a.id, a.opinion.model_dump()) for a in result.agents], [d.model_dump() for d in result.decisions]


def test_simulation_is_seed_reproducible_and_integral():
    left, right = run(), run()
    assert fingerprint(left) == fingerprint(right)
    ids = {a.id for a in left.agents}
    assert all(target in ids for e in left.events for target in e.target_agent_ids)
    assert all(e.source_agent_id is None or e.source_agent_id in ids for e in left.events)
    assert all(0 <= value <= 1 for a in left.agents for value in a.opinion.model_dump().values())
    memory_events = {e.event_type for e in left.events}
    assert all(m.event_type in memory_events or m.event_type.startswith("peer_") or m.event_type == "friend_recommendation" for a in left.agents for m in a.memories)


def test_different_seed_changes_outcome():
    assert fingerprint(run(1)) != fingerprint(run(2))
