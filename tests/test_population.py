from manas.population.generator import PopulationGenerator


def test_population_is_diverse_and_reproducible():
    first = PopulationGenerator(42).generate(100)
    second = PopulationGenerator(42).generate(100)
    assert [a.model_dump() for a in first] == [a.model_dump() for a in second]
    assert len({a.location for a in first}) >= 10
    assert len({a.occupation for a in first}) >= 5
    assert all(0 <= len(a.contradictions) <= 3 for a in first)
    assert all(a.disposable_income >= 0 for a in first)
