from manas.agents.models import Memory


def test_memory_decays_and_importance_lasts_longer():
    important = Memory(id="a", day=1, event_type="review", content="Strong review", importance=.9, emotional_weight=.5)
    trivial = Memory(id="b", day=1, event_type="ad", content="Saw ad", importance=.2, emotional_weight=.1)
    assert important.relevance(10) > trivial.relevance(10)
    assert important.relevance(20) < important.relevance(2)


def test_topic_relevance_changes_retrieval():
    from manas.population.generator import PopulationGenerator
    agent = PopulationGenerator(1).generate(1)[0]
    price = Memory(id="price", day=1, event_type="price_change", content="Price fell", importance=.5, emotional_weight=.1, category="price", topics=["discount"])
    privacy = Memory(id="privacy", day=2, event_type="negative_review", content="Privacy concern", importance=.7, emotional_weight=-.5, category="privacy", topics=["data"])
    agent.memories = [price, privacy]
    assert agent.relevant_memories(4, 1, {"discount"})[0].id == "price"
    assert agent.relevant_memories(4, 1, {"privacy"})[0].id == "privacy"
