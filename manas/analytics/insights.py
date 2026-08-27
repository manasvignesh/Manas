from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

from manas.agents.models import Agent
from manas.simulation.models import Decision, SimulationSummary


def analyze(run_id: str, seed: int, days: int, agents: list[Agent], decisions: list[Decision], graph: nx.Graph, opinion_changes: int) -> SimulationSummary:
    sentiments = Counter(agent.opinion.sentiment for agent in agents)
    actions = Counter(decision.action for decision in decisions)
    by_segment: dict[str, list[float]] = defaultdict(list)
    for agent in agents:
        by_segment[agent.occupation].append(agent.opinion.purchase_intent)
    ranked = sorted(((sum(values) / len(values), key) for key, values in by_segment.items()), reverse=True)
    price_resistance = sum(1 for a in agents if a.opinion.price_acceptance < .35) / len(agents)
    privacy_resistance = sum(1 for a in agents if a.privacy_sensitivity > .7 and a.opinion.trust < .4) / len(agents)
    centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 1 else {agents[0].id: 0}
    top_id = max(centrality, key=centrality.get)
    top_agent = next(a for a in agents if a.id == top_id)
    insights = [
        f"Most receptive occupation: {ranked[0][1]} ({ranked[0][0]:.0%} average purchase intent).",
        f"Least receptive occupation: {ranked[-1][1]} ({ranked[-1][0]:.0%} average purchase intent).",
        f"Price resistance appears in {price_resistance:.0%} of this synthetic population.",
        f"Privacy-sensitive skepticism appears in {privacy_resistance:.0%} of agents.",
        f"Highest-influence network position: {top_agent.name} ({top_agent.location}).",
    ]
    total = len(agents)
    return SimulationSummary(
        run_id=run_id, seed=seed, population_size=total, days=days,
        interactions=sum(1 for d in decisions if d.action == "ask_friend"), opinion_changes=opinion_changes,
        actions=dict(actions), sentiment={key: sentiments[key] / total for key in ("positive", "neutral", "negative")},
        average_purchase_intent=sum(a.opinion.purchase_intent for a in agents) / total, insights=insights,
    )
