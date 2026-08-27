from manas.storage import Database, SimulationRepository
from tests.test_simulation import run


def test_storage_round_trip(tmp_path):
    result = run()
    repo = SimulationRepository(Database(tmp_path / "test.db"))
    repo.save(result)
    loaded = repo.load(result.run_id)
    assert loaded.summary == result.summary
    assert len(loaded.agents) == len(result.agents)
    assert loaded.graph.graph.number_of_edges() == result.graph.graph.number_of_edges()
