import networkx as nx

from manas.population.generator import PopulationGenerator
from manas.society.graph import SocietyGraph


def test_social_graph_is_valid_connected_and_clustered():
    agents = PopulationGenerator(7).generate(60)
    graph = SocietyGraph(7).build(agents)
    assert nx.is_connected(graph)
    assert all(a != b for a, b in graph.edges)
    assert set(graph.nodes) == {a.id for a in agents}
    assert all(0 <= data["trust"] <= 1 for *_, data in graph.edges(data=True))
    assert nx.average_clustering(graph) > 0
