from __future__ import annotations

import asyncio
from collections import Counter

from manas.behavior.engine import BehaviorEngine
from manas.behavior.motivations import motivations
from manas.behavior.perception import perceive
from manas.calibration.models import BenchmarkResult
from manas.population.generator import PopulationGenerator
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import ProductScenario, SimulationConfig, SimulationEvent
from manas.society.influence import influence_shift
from manas.utils.random import seeded


def _decision_probabilities(agents, scenario, event):
    decisions = []
    behavior = BehaviorEngine()
    for index, agent in enumerate(agents):
        decisions.append(behavior.evaluate(agent, scenario, event, seeded(811, index)))
    return decisions


def _affordability_sensitivity() -> BenchmarkResult:
    agents = PopulationGenerator(17).generate(100)
    sensitive = [agent for agent in agents if agent.price_sensitivity >= .6]
    event = SimulationEvent(id="price-test", day=1, event_type="product_seen", target_agent_ids=[a.id for a in sensitive])
    base = dict(name="AI fitness coach", description="Personalized workout support", category="fitness", pricing_model="monthly")
    high = _decision_probabilities(sensitive, ProductScenario(**base, price=799), event)
    low = _decision_probabilities(sensitive, ProductScenario(**base, price=99), event)
    def resistance(items):
        return sum(sum(d.probabilities.get(a, 0) for a in {"wait_for_discount", "save_for_later", "compare_alternative"}) for d in items) / len(items)
    high_score, low_score = resistance(high), resistance(low)
    return BenchmarkResult(name="affordability sensitivity", passed=high_score > low_score,
                           evidence=f"price-sensitive deferral probability {high_score:.1%} at INR 799 vs {low_score:.1%} at INR 99")


def _relevance_over_wealth() -> BenchmarkResult:
    agents = PopulationGenerator(23).generate(120)
    wealthy = [agent.model_copy(update={"disposable_income": 100_000}) for agent in agents[:40]]
    scenario = ProductScenario(name="Specialist beekeeping log", description="Track remote apiaries", category="beekeeping", price=199)
    event = SimulationEvent(id="relevance-test", day=1, event_type="product_seen", target_agent_ids=[a.id for a in wealthy])
    decisions = _decision_probabilities(wealthy, scenario, event)
    dismiss = sum(d.probabilities.get("ignore", 0) + d.probabilities.get("reject", 0) for d in decisions) / len(decisions)
    purchase = sum(d.probabilities.get("buy_now", 0) + d.probabilities.get("subscribe", 0) for d in decisions) / len(decisions)
    return BenchmarkResult(name="relevance dominates irrelevant wealth", passed=dismiss > purchase * 2,
                           evidence=f"irrelevant dismissal {dismiss:.1%} vs purchase consideration {purchase:.1%}")


def _trusted_peer_influence() -> BenchmarkResult:
    listener = PopulationGenerator(29).generate(1)[0]
    listener.personality.social_conformity = .75
    listener.trust_tendency = .7
    high, _ = influence_shift(listener, {"trust": .9, "strength": .9, "influence": .8}, .8, .8, .8)
    low, _ = influence_shift(listener, {"trust": .15, "strength": .3, "influence": .3}, .8, .8, .8)
    return BenchmarkResult(name="trusted-peer influence", passed=high > low > 0,
                           evidence=f"trusted shift {high:.3f} vs weak-tie shift {low:.3f}")


def _seed_variation() -> BenchmarkResult:
    scenario = ProductScenario(name="AI fitness coach", description="Personalized fitness", category="fitness", price=399, pricing_model="monthly")
    config = dict(population_size=35, days=6)
    left = asyncio.run(SimulationEngine().run(scenario, SimulationConfig(**config, seed=31)))
    right = asyncio.run(SimulationEngine().run(scenario, SimulationConfig(**config, seed=32)))
    left_actions = Counter(d.action for d in left.decisions)
    right_actions = Counter(d.action for d in right.decisions)
    plausible = bool(left.decisions and right.decisions) and all(sum(values.values()) > 0 for values in (left_actions, right_actions))
    return BenchmarkResult(name="seed variation", passed=plausible and left_actions != right_actions,
                           evidence=f"action mixes differ across seeds ({len(left_actions)} vs {len(right_actions)} paths)")


def _contradiction_handling() -> BenchmarkResult:
    agent = PopulationGenerator(37).generate(1)[0]
    agent.interests = [*agent.interests, "fitness"]
    agent.goals = [*agent.goals, "fitness"]
    agent.disposable_income = 500
    agent.state.financial_pressure = .9
    agent.personality.frugality = .9
    scenario = ProductScenario(name="AI fitness coach", description="Personalized fitness", category="fitness", price=399, pricing_model="monthly")
    event = SimulationEvent(id="conflict-test", day=1, event_type="product_seen", target_agent_ids=[agent.id])
    perception = perceive(agent, scenario, event)
    motives = motivations(agent, scenario, event, perception)
    directions = {m.direction for m in motives if m.strength >= .5}
    decision = BehaviorEngine().evaluate(agent, scenario, event, seeded(37, "conflict"))
    investigates = sum(decision.probabilities.get(a, 0) for a in {"search_reviews", "wait_for_discount", "save_for_later", "compare_alternative"})
    buys = decision.probabilities.get("buy_now", 0) + decision.probabilities.get("subscribe", 0)
    return BenchmarkResult(name="contradiction handling", passed=directions == {"toward", "away"} and investigates > buys,
                           evidence=f"conflict preserved; investigate/defer {investigates:.1%} vs immediate purchase {buys:.1%}")


def run_benchmarks() -> list[BenchmarkResult]:
    """Run invariant checks, not claims of empirical market calibration."""

    checks = (
        _affordability_sensitivity,
        _relevance_over_wealth,
        _trusted_peer_influence,
        _seed_variation,
        _contradiction_handling,
    )
    return [check() for check in checks]
