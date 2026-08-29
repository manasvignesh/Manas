from collections import Counter

from tests.test_cascades import golden_result


def test_insights_are_grounded_in_decisions_and_social_events():
    result = golden_result()
    findings = result.summary.findings
    assert set(findings) >= {"who_wants_this", "who_does_not", "strongest_pull", "biggest_resistance", "unexpected", "social_effect"}
    assert str(len(result.social_interactions)) in findings["social_effect"] or "credibility" in findings["social_effect"]
    away = Counter(item["source"] for decision in result.decisions if decision.action in {"reject", "ignore", "wait_for_discount", "save_for_later", "criticize"} for item in decision.motivations if item["direction"] == "away")
    if away:
        assert "appeared in" not in findings["biggest_resistance"]
        assert len(findings["biggest_resistance"].split()) >= 8
    assert result.summary.real_world_tests
    assert any("privacy" in item.casefold() for item in result.summary.real_world_tests)


def test_normal_explanations_contain_human_reasons_not_factor_scores():
    result = golden_result()
    explanations = [reason for decision in result.decisions for reason in decision.explanation]
    assert explanations
    assert not any("(0." in reason or "(1.00" in reason for reason in explanations)
    assert any("current" in reason.casefold() or "evidence" in reason.casefold() for reason in explanations)
