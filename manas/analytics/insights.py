from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

from manas.agents.models import Agent
from manas.simulation.models import Decision, ProductScenario, SimulationSummary
from manas.society.models import SocialInteraction


POSITIVE_ACTIONS = {"buy_now", "subscribe", "try_once", "try_free", "recommend"}
RESISTANT_ACTIONS = {"reject", "ignore", "wait_for_discount", "save_for_later", "criticize"}


def _top_source(decisions: list[Decision], actions: set[str], direction: str) -> tuple[str, int]:
    sources = Counter(item["source"] for decision in decisions if decision.action in actions for item in decision.motivations if item["direction"] == direction)
    return sources.most_common(1)[0] if sources else ("personal relevance" if direction == "toward" else "uncertainty", 0)


def analyze(run_id: str, seed: int, days: int, agents: list[Agent], decisions: list[Decision], graph: nx.Graph,
            opinion_changes: int, scenario: ProductScenario | None = None,
            social_interactions: list[SocialInteraction] | None = None) -> SimulationSummary:
    sentiments = Counter(agent.opinion.sentiment for agent in agents)
    actions = Counter(decision.action for decision in decisions)
    by_segment: dict[str, list[float]] = defaultdict(list)
    for agent in agents:
        by_segment[agent.occupation].append(agent.opinion.purchase_intent)
    ranked = sorted(((sum(values) / len(values), key) for key, values in by_segment.items()), reverse=True)
    pull, pull_count = _top_source(decisions, POSITIVE_ACTIONS, "toward")
    resistance, resistance_count = _top_source(decisions, RESISTANT_ACTIONS, "away")
    agent_by_id = {agent.id: agent for agent in agents}
    low_income_positive = [d for d in decisions if d.action in POSITIVE_ACTIONS and agent_by_id[d.agent_id].income_band in {"low", "lower-middle"}]
    high_cred = [abs(item.opinion_shift) for item in (social_interactions or []) if item.credibility >= .45]
    low_cred = [abs(item.opinion_shift) for item in (social_interactions or []) if item.credibility < .45]
    if low_income_positive:
        surprise = f"{len({d.agent_id for d in low_income_positive})} lower-income people still moved toward trying or paying when the idea connected to an immediate goal."
    else:
        surprise = "Affordability and relevance generally moved together; no strong lower-income exception emerged in this run."
    if high_cred and low_cred:
        social = f"Higher-credibility peer messages shifted opinions about {sum(high_cred)/len(high_cred):.1%} on average versus {sum(low_cred)/len(low_cred):.1%} for weaker ties."
    else:
        social = f"{len(social_interactions or [])} peer transmissions were recorded; their effects varied with trust and prior belief."
    findings = {
        "who_wants_this": f"{ranked[0][1].title()} agents were most receptive in this society ({ranked[0][0]:.0%} average intent).",
        "who_does_not": f"{ranked[-1][1].title()} agents were least receptive ({ranked[-1][0]:.0%} average intent).",
        "strongest_pull": f"{pull.replace('_', ' ').title()} appeared in {pull_count} positive consideration paths.",
        "biggest_resistance": f"{resistance.replace('_', ' ').title()} appeared in {resistance_count} resistant consideration paths.",
        "unexpected": surprise,
        "social_effect": social,
    }
    recommendations = []
    if resistance == "money" or (scenario and scenario.price > 0):
        recommendations.append("Test whether a free trial, student tier, or non-recurring option changes the decision.")
    if scenario and scenario.privacy_exposure >= .5:
        recommendations.append("Test privacy messaging and which personal data people are actually comfortable sharing.")
    if scenario and scenario.competitors:
        recommendations.append(f"Test whether the benefit feels meaningfully better than {scenario.competitors[0]}.")
    recommendations.append("Interview people from both the most receptive and least receptive groups; simulation output is not evidence of demand.")
    centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 1 else {agents[0].id: 0}
    top_agent = agent_by_id[max(centrality, key=centrality.get)]
    insights = [findings["who_wants_this"], findings["who_does_not"], findings["biggest_resistance"], f"Highest-influence network position: {top_agent.name} ({top_agent.location})."]
    total = len(agents)
    return SimulationSummary(run_id=run_id, seed=seed, population_size=total, days=days,
        interactions=len(social_interactions or []), opinion_changes=opinion_changes, actions=dict(actions),
        sentiment={key: sentiments[key] / total for key in ("positive", "neutral", "negative")},
        average_purchase_intent=sum(a.opinion.purchase_intent for a in agents) / total, insights=insights,
        findings=findings, real_world_tests=recommendations)
