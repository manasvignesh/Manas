from __future__ import annotations

import math
from dataclasses import dataclass

from manas.agents.models import Agent
from manas.behavior.calibration import DEFAULT_CALIBRATION
from manas.scenarios.targeting import target_match
from manas.simulation.models import ProductScenario


@dataclass(frozen=True)
class SegmentResult:
    dimension: str
    label: str
    size: int
    average_intent: float
    difference: float
    score: float


def analyze_segments(agents: list[Agent], scenario: ProductScenario) -> list[SegmentResult]:
    total = len(agents)
    minimum = max(DEFAULT_CALIBRATION.minimum_segment_size,
                  math.ceil(total * DEFAULT_CALIBRATION.minimum_segment_fraction))
    overall = sum(agent.opinion.purchase_intent for agent in agents) / max(total, 1)
    groups: dict[tuple[str, str], set[str]] = {}

    def add(dimension: str, label: str, agent: Agent) -> None:
        groups.setdefault((dimension, label), set()).add(agent.id)

    for agent in agents:
        add("occupation", agent.occupation.title(), agent)
        add("education", agent.education.title(), agent)
        add("income", f"{agent.income_band.title()} income", agent)
        age_band = "17-24" if agent.age < 25 else "25-34" if agent.age < 35 else "35-49" if agent.age < 50 else "50+"
        add("age", f"Age {age_band}", agent)
        add("location", agent.location, agent)
        if agent.technology_familiarity >= .65:
            add("technology", "Tech-comfortable people", agent)
        elif agent.technology_familiarity <= .35:
            add("technology", "Less tech-comfortable people", agent)
        match = target_match(agent, scenario)
        if match >= .65:
            add("target match", "High target-match people", agent)
        elif match <= .3:
            add("target match", "Low target-match people", agent)
        for interest in agent.interests:
            add("interest", f"People interested in {interest}", agent)
        for goal in agent.goals:
            add("goal", f"People trying to {goal}", agent)
        for context in agent.life_contexts:
            add("life stage", f"People experiencing {context.situation}", agent)
        category_connected = scenario.category in agent.interests or any(
            scenario.category in context.themes for context in agent.life_contexts
        )
        if agent.occupation == "student" and category_connected:
            add("combined", f"Students with an active {scenario.category} connection", agent)
        if agent.occupation == "student" and agent.technology_familiarity >= .6:
            add("combined", "Tech-comfortable students", agent)

    by_id = {agent.id: agent for agent in agents}
    results = []
    for (dimension, label), member_ids in groups.items():
        if len(member_ids) < minimum or len(member_ids) == total:
            continue
        average = sum(by_id[identifier].opinion.purchase_intent for identifier in member_ids) / len(member_ids)
        difference = average - overall
        score = abs(difference) * (len(member_ids) / total) ** .35
        results.append(SegmentResult(dimension, label, len(member_ids), average, difference, score))
    return sorted(results, key=lambda item: item.score, reverse=True)


def strongest_segments(agents: list[Agent], scenario: ProductScenario) -> tuple[SegmentResult, SegmentResult]:
    segments = analyze_segments(agents, scenario)
    if not segments:
        average = sum(agent.opinion.purchase_intent for agent in agents) / max(len(agents), 1)
        whole = SegmentResult("population", "The simulated population", len(agents), average, 0, 0)
        return whole, whole
    positive_pool = [item for item in segments if item.difference >= 0] or segments
    negative_pool = [item for item in segments if item.difference < 0] or segments
    positive = max(positive_pool, key=lambda item: item.score)
    negative = max(negative_pool, key=lambda item: item.score)
    return positive, negative
