from __future__ import annotations

import asyncio
from collections import Counter
from functools import lru_cache
from statistics import mean

from manas.analytics.segments import analyze_segments
from manas.analytics.sentiment import classify_sentiment
from manas.behavior.engine import BehaviorEngine
from manas.behavior.motivations import motivations
from manas.behavior.perception import perceive
from manas.calibration.models import BenchmarkResult
from manas.cli.presenters import reaction_narrative
from manas.population.generator import PopulationGenerator
from manas.scenarios import parse_scenario
from manas.simulation.engine import SimulationEngine
from manas.simulation.models import ProductScenario, SimulationConfig, SimulationEvent
from manas.society.influence import influence_shift
from manas.utils.random import seeded


@lru_cache(maxsize=1)
def _realism_fixture():
    scenario = parse_scenario("AI fitness coach for Indian college students at INR 399/month")
    result = asyncio.run(SimulationEngine().run(
        scenario, SimulationConfig(population_size=100, days=10, seed=42)
    ))
    return scenario, result


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
    scenario = parse_scenario("AI fitness coach for college students at INR 399/month")
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
    agent.disposable_income = 100
    agent.state.financial_pressure = .9
    agent.personality.frugality = .9
    scenario = parse_scenario("AI fitness coach for college students at INR 399/month")
    event = SimulationEvent(id="conflict-test", day=1, event_type="product_seen", target_agent_ids=[agent.id])
    perception = perceive(agent, scenario, event)
    motives = motivations(agent, scenario, event, perception)
    directions = {m.direction for m in motives if m.strength >= .5}
    decision = BehaviorEngine().evaluate(agent, scenario, event, seeded(37, "conflict"))
    investigates = sum(decision.probabilities.get(a, 0) for a in {"search_reviews", "wait_for_discount", "save_for_later", "compare_alternative"})
    buys = decision.probabilities.get("buy_now", 0) + decision.probabilities.get("subscribe", 0)
    return BenchmarkResult(name="contradiction handling", passed=directions == {"toward", "away"} and investigates > buys,
                           evidence=f"conflict preserved; investigate/defer {investigates:.1%} vs immediate purchase {buys:.1%}")


def _target_audience_relevance() -> BenchmarkResult:
    scenario, result = _realism_fixture()
    event = SimulationEvent(id="target", day=1, event_type="product_seen", target_agent_ids=[])
    students = [perceive(agent, scenario, event).perceived_problem_relevance for agent in result.agents if agent.occupation == "student"]
    unrelated = [perceive(agent, scenario, event).perceived_problem_relevance for agent in result.agents if agent.occupation in {"farmer", "retired"}]
    difference = mean(students) - mean(unrelated)
    return BenchmarkResult(name="target audience relevance", passed=difference >= .12,
                           evidence=f"student relevance exceeded unrelated roles by {difference:.1%}")


def _non_target_conversion() -> BenchmarkResult:
    scenario, result = _realism_fixture()
    event = SimulationEvent(id="non-target", day=1, event_type="product_seen", target_agent_ids=[])
    decisions = _decision_probabilities([agent for agent in result.agents if agent.occupation != "student"], scenario, event)
    purchase = {"buy_now", "subscribe", "try_once", "try_free"}
    potential = [sum(decision.probabilities.get(action, 0) for action in purchase) for decision in decisions]
    return BenchmarkResult(name="non-target users can still convert", passed=max(potential, default=0) >= .08,
                           evidence=f"strongest non-target purchase/try consideration was {max(potential, default=0):.1%}")


def _price_response() -> tuple[BenchmarkResult, BenchmarkResult]:
    scenario, result = _realism_fixture()
    cheaper = scenario.model_copy(update={"price": 199})
    event = SimulationEvent(id="price-replay", day=1, event_type="product_seen", target_agent_ids=[])
    shifts = []
    for index, agent in enumerate(result.agents):
        before = BehaviorEngine().evaluate(agent, scenario, event, seeded(1400, index))
        after = BehaviorEngine().evaluate(agent, cheaper, event, seeded(1400, index))
        actions = set(before.probabilities) | set(after.probabilities)
        shift = sum(abs(before.probabilities.get(action, 0) - after.probabilities.get(action, 0)) for action in actions) / 2
        shifts.append((agent, shift, before.factors["relevance"]))
    sensitive = [shift for agent, shift, relevance in shifts if agent.price_sensitivity >= .6 and relevance >= .4]
    insensitive = [shift for agent, shift, relevance in shifts if agent.price_sensitivity <= .4 and relevance >= .4]
    sensitive_average = mean(sensitive)
    insensitive_average = mean(insensitive)
    return (
        BenchmarkResult(name="price-sensitive response", passed=sensitive_average > insensitive_average + .01,
                        evidence=f"relevant sensitive shift {sensitive_average:.1%} vs {insensitive_average:.1%}"),
        BenchmarkResult(name="price-insensitive stability", passed=insensitive_average < .12,
                        evidence=f"relevant price-insensitive decision shift stayed at {insensitive_average:.1%}"),
    )


def _sentiment_action_coherence() -> BenchmarkResult:
    _, result = _realism_fixture()
    by_agent = {agent.id: [] for agent in result.agents}
    for decision in result.decisions:
        by_agent[decision.agent_id].append(decision)
    research = [agent for agent in result.agents if by_agent[agent.id] and by_agent[agent.id][-1].action in {
        "search_reviews", "wait_for_discount", "save_for_later", "ask_friend", "compare_alternative"
    }]
    coherent = all(classify_sentiment(agent, by_agent[agent.id]) != "negative" for agent in research)
    negative = result.summary.sentiment["negative"]
    return BenchmarkResult(name="sentiment-action coherence", passed=coherent and negative < .75,
                           evidence=f"research/wait actions stayed non-negative; population negative share {negative:.0%}")


def _habit_dominance_guard() -> BenchmarkResult:
    _, result = _realism_fixture()
    resistant = [decision for decision in result.decisions if decision.action in {
        "reject", "ignore", "wait_for_discount", "save_for_later", "compare_alternative"
    }]
    sources = Counter(item["source"] for decision in resistant for item in decision.motivations if item["direction"] == "away")
    generic = sources["habit"]
    largest = max((count / max(len(resistant), 1) for source, count in sources.items()
                   if source in {"habit", "existing alternative", "consistency friction", "subscription fatigue"}), default=0)
    return BenchmarkResult(name="habit dominance guard", passed=generic == 0 and largest < .55,
                           evidence=f"generic habit count {generic}; largest specific routine mechanism {largest:.0%}")


def _topic_diversity() -> BenchmarkResult:
    _, result = _realism_fixture()
    topics = Counter(item.topic for item in (result.information or []))
    dominant = max(topics.values(), default=0) / max(sum(topics.values()), 1)
    return BenchmarkResult(name="topic diversity", passed=len(topics) >= 2 and dominant < .75,
                           evidence=f"{len(topics)} topics; largest accounted for {dominant:.0%} of messages")


def _segment_minimum_sample() -> BenchmarkResult:
    scenario, result = _realism_fixture()
    segments = analyze_segments(result.agents, scenario)
    smallest = min((segment.size for segment in segments), default=0)
    return BenchmarkResult(name="segment minimum sample", passed=smallest >= 5,
                           evidence=f"smallest eligible reported segment contains {smallest} people")


def _explanation_diversity() -> BenchmarkResult:
    scenario, result = _realism_fixture()
    agents = {agent.id: agent for agent in result.agents}
    narratives = [reaction_narrative(agents[decision.agent_id], decision, scenario) for decision in result.decisions[:30]]
    ratio = len(set(narratives)) / max(len(narratives), 1)
    return BenchmarkResult(name="agent explanation diversity", passed=ratio >= .8,
                           evidence=f"{ratio:.0%} of sampled reaction narratives were distinct")


def run_benchmarks() -> list[BenchmarkResult]:
    """Run invariant checks, not claims of empirical market calibration."""

    checks = (
        _affordability_sensitivity,
        _relevance_over_wealth,
        _trusted_peer_influence,
        _seed_variation,
        _contradiction_handling,
        _target_audience_relevance,
        _non_target_conversion,
    )
    results = [check() for check in checks]
    results.extend(_price_response())
    results.extend([
        _sentiment_action_coherence(),
        _habit_dominance_guard(),
        _topic_diversity(),
        _segment_minimum_sample(),
        _explanation_diversity(),
    ])
    return results
