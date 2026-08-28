from tests.test_simulation import run


def test_social_information_is_structured_and_persistable():
    result = run(seed=42)
    assert result.information
    assert result.social_interactions
    ids = {item.id for item in result.information}
    agent_ids = {agent.id for agent in result.agents}
    assert all(item.information_id in ids for item in result.social_interactions)
    assert all(item.speaker_id in agent_ids and item.listener_id in agent_ids for item in result.social_interactions)
    assert all(item.relationship_type for item in result.social_interactions)
    assert all(item.listener_reaction for item in result.social_interactions)
    assert any(len(item.reached_agent_ids) > 1 for item in result.information)


def test_social_memories_keep_claim_topic_and_source():
    result = run(seed=42)
    social = [memory for agent in result.agents for memory in agent.memories if memory.source_agent_id]
    assert social
    assert all(memory.category != "general" for memory in social)
    assert all(memory.topics for memory in social)
