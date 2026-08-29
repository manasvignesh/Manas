from __future__ import annotations

from collections import Counter
from math import ceil

from pydantic import BaseModel

from manas.analytics.segments import analyze_segments
from manas.behavior.calibration import DEFAULT_CALIBRATION
from manas.behavior.engine import BehaviorEngine
from manas.scenarios.targeting import target_match
from manas.simulation.engine import SimulationResult
from manas.simulation.models import SimulationEvent
from manas.utils.random import seeded


class DiagnosticCheck(BaseModel):
    name: str
    status: str
    evidence: str


def diagnose_result(result: SimulationResult) -> list[DiagnosticCheck]:
    agents = result.agents
    vectors = {tuple(round(value, 2) for value in agent.personality.model_dump().values()) for agent in agents}
    diversity = len(vectors) / max(len(agents), 1)
    matches = [target_match(agent, result.scenario) for agent in agents]
    resistant = [decision for decision in result.decisions if decision.action in {
        "reject", "ignore", "wait_for_discount", "save_for_later", "criticize", "compare_alternative"
    }]
    sources = Counter(item["source"] for decision in resistant for item in decision.motivations if item["direction"] == "away")
    dominant_source, dominant_count = sources.most_common(1)[0] if sources else ("none", 0)
    dominant_share = dominant_count / max(len(resistant), 1)
    negative = result.summary.sentiment.get("negative", 0)
    topics = Counter(item.topic for item in (result.information or []))
    dominant_topic, topic_count = topics.most_common(1)[0] if topics else ("none", 0)
    topic_share = topic_count / max(sum(topics.values()), 1)

    event = SimulationEvent(id="diagnostic-price", day=1, event_type="product_seen",
                            target_agent_ids=[agent.id for agent in agents])
    cheaper = result.scenario.model_copy(update={"price": result.scenario.price * .5})
    behavior = BehaviorEngine()
    shifts = []
    for index, agent in enumerate(agents):
        before = behavior.evaluate(agent, result.scenario, event, seeded(result.config.seed, f"diagnose:{index}"))
        after = behavior.evaluate(agent, cheaper, event, seeded(result.config.seed, f"diagnose:{index}"))
        actions = set(before.probabilities) | set(after.probabilities)
        shift = sum(abs(before.probabilities.get(action, 0) - after.probabilities.get(action, 0)) for action in actions) / 2
        shifts.append((agent.price_sensitivity, shift))
    sensitive = [shift for sensitivity, shift in shifts if sensitivity >= .6]
    insensitive = [shift for sensitivity, shift in shifts if sensitivity <= .4]
    sensitive_average = sum(sensitive) / max(len(sensitive), 1)
    insensitive_average = sum(insensitive) / max(len(insensitive), 1)

    minimum = max(DEFAULT_CALIBRATION.minimum_segment_size,
                  ceil(len(agents) * DEFAULT_CALIBRATION.minimum_segment_fraction))
    segments = analyze_segments(agents, result.scenario)
    segment_ok = bool(segments) and all(segment.size >= minimum for segment in segments)
    return [
        DiagnosticCheck(name="Population diversity", status="PASS" if diversity >= .9 else "WARNING",
                        evidence=f"{diversity:.0%} unique rounded personality profiles."),
        DiagnosticCheck(name="Target-match distribution", status="PASS" if max(matches, default=0) - min(matches, default=0) >= .25 else "WARNING",
                        evidence=f"Target-match range {min(matches, default=0):.0%} to {max(matches, default=0):.0%}."),
        DiagnosticCheck(name="Dominant modifier check", status="WARNING" if dominant_share > .55 else "PASS",
                        evidence=f"{dominant_source.title()} influenced {dominant_share:.0%} of resistant paths."),
        DiagnosticCheck(name="Sentiment balance", status="WARNING" if negative > .75 else "PASS",
                        evidence=f"{negative:.0%} negative sentiment."),
        DiagnosticCheck(name="Topic dominance", status="WARNING" if topic_share > .60 and sum(topics.values()) >= 5 else "PASS",
                        evidence=f"{dominant_topic.title()} accounted for {topic_share:.0%} of {sum(topics.values())} social messages."),
        DiagnosticCheck(name="Price sensitivity test", status="PASS" if sensitive_average > insensitive_average else "WARNING",
                        evidence=f"Sensitive decision shift {sensitive_average:.1%}; insensitive shift {insensitive_average:.1%}."),
        DiagnosticCheck(name="Segment sample sizes", status="PASS" if segment_ok else "WARNING",
                        evidence=f"All reported segments contain at least {minimum} people."),
    ]
