import pytest

from manas.scenarios import parse_scenario, sanitize_idea


def test_parser_structures_fitness_subscription():
    scenario = parse_scenario("AI fitness coach for Indian college students for ₹399/month")
    assert scenario.category == "fitness"
    assert "education" in scenario.secondary_categories
    assert scenario.technologies == ["AI", "software"]
    assert scenario.target_audience == "college students"
    assert scenario.price == 399
    assert scenario.pricing_model == "monthly"
    assert scenario.privacy_exposure >= .5
    assert scenario.behavior_change_required >= .7
    assert "free workout content" in scenario.competitors


def test_explicit_values_override_parsed_values():
    scenario = parse_scenario("free AI study app", price=199, pricing_model="annual", target_audience="teachers")
    assert scenario.price == 199
    assert scenario.pricing_model == "annual"
    assert scenario.target_audience == "teachers"


def test_shell_command_is_never_stored_as_idea():
    command = 'manas simulate --idea "AI fitness coach" --population 100 --days 14'
    assert sanitize_idea(command) == "AI fitness coach"
    assert parse_scenario(command).name == "AI fitness coach"
    with pytest.raises(ValueError):
        parse_scenario("manas simulate --population 100 --days 14")
