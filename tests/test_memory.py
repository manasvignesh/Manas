from crowdforge.agents.models import Memory


def test_memory_decays_and_importance_lasts_longer():
    important = Memory(id="a", day=1, event_type="review", content="Strong review", importance=.9, emotional_weight=.5)
    trivial = Memory(id="b", day=1, event_type="ad", content="Saw ad", importance=.2, emotional_weight=.1)
    assert important.relevance(10) > trivial.relevance(10)
    assert important.relevance(20) < important.relevance(2)

