from __future__ import annotations

import networkx as nx

from crowdforge.agents.models import Agent
from crowdforge.utils.random import clamp, seeded


class SocietyGraph:
    """Clustered social network using homophily plus cross-group weak ties."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = seeded(seed, "social-graph")
        self.graph = nx.Graph()

    def build(self, agents: list[Agent]) -> nx.Graph:
        self.graph.clear()
        for agent in agents:
            community = f"{agent.location}:{agent.occupation}"
            self.graph.add_node(agent.id, community=community, region=agent.region)
        target_degree = min(8, max(2, len(agents) // 12))
        candidates: list[tuple[float, str, str]] = []
        for i, first in enumerate(agents):
            for second in agents[i + 1:]:
                similarity = self._similarity(first, second)
                noise = self.rng.random() * .35
                candidates.append((similarity + noise, first.id, second.id))
        candidates.sort(reverse=True)
        max_edges = max(len(agents) - 1, len(agents) * target_degree // 2)
        for score, first_id, second_id in candidates:
            if self.graph.number_of_edges() >= max_edges:
                break
            if self.graph.degree(first_id) >= target_degree + 3 or self.graph.degree(second_id) >= target_degree + 3:
                continue
            if score > .57 or self.rng.random() < .012:
                self._connect(first_id, second_id, score)
        # Connect components with weak acquaintances.
        components = [list(group) for group in nx.connected_components(self.graph)]
        for left, right in zip(components, components[1:]):
            self._connect(self.rng.choice(left), self.rng.choice(right), .25)
        return self.graph

    def _similarity(self, a: Agent, b: Agent) -> float:
        score = 0.0
        score += .25 if a.location == b.location else .08 if a.region == b.region else 0
        score += .18 if a.occupation == b.occupation else 0
        score += .12 if abs(a.age - b.age) <= 5 else .04 if abs(a.age - b.age) <= 12 else 0
        score += .18 * (len(set(a.interests) & set(b.interests)) / max(1, len(set(a.interests) | set(b.interests))))
        score += .1 if a.languages[0] == b.languages[0] else 0
        return score

    def _connect(self, first_id: str, second_id: str, affinity: float) -> None:
        if first_id == second_id or self.graph.has_edge(first_id, second_id):
            return
        strength = clamp(.28 + affinity * .7 + self.rng.uniform(-.12, .12))
        if affinity > .62:
            relationship = self.rng.choice(["friend", "coworker", "classmate", "family"])
        elif affinity > .42:
            relationship = self.rng.choice(["friend", "community", "coworker", "classmate"])
        else:
            relationship = "acquaintance"
        self.graph.add_edge(first_id, second_id, relationship_type=relationship,
                            trust=clamp(strength + self.rng.uniform(-.15, .15)), strength=strength,
                            interaction_frequency=clamp(strength * self.rng.uniform(.55, 1.1)),
                            influence=clamp(strength * self.rng.uniform(.6, 1.05)))

    def neighbors(self, agent_id: str) -> list[str]:
        return list(self.graph.neighbors(agent_id))

    def edge(self, first_id: str, second_id: str) -> dict:
        return dict(self.graph.edges[first_id, second_id])

    def communities(self) -> list[set[str]]:
        return list(nx.community.greedy_modularity_communities(self.graph, weight="strength"))

