from pathlib import Path

import pytest

from app.scenarios.loader import ScenarioLoadError, get_scenario, list_scenarios, load_scenarios
from app.scenarios.schema import Scenario

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_load_scenarios_valid_directory():
    scenarios = load_scenarios(FIXTURES_DIR / "valid")
    assert len(scenarios) == 2
    assert {s.id for s in scenarios} == {"restaurant-test", "cafe-test"}
    assert all(isinstance(s, Scenario) for s in scenarios)


def test_get_scenario_and_list_scenarios_after_load():
    load_scenarios(FIXTURES_DIR / "valid")
    restaurant = get_scenario("restaurant-test")
    assert restaurant is not None
    assert restaurant.title == "Ordering at a Restaurant (test fixture)"
    assert len(list_scenarios()) == 2
    assert get_scenario("does-not-exist") is None


def test_unknown_extra_field_is_ignored():
    load_scenarios(FIXTURES_DIR / "valid")
    cafe = get_scenario("cafe-test")
    assert cafe is not None
    assert not hasattr(cafe, "extra_field")


def test_load_scenarios_invalid_file_raises_with_filename():
    with pytest.raises(ScenarioLoadError) as exc_info:
        load_scenarios(FIXTURES_DIR / "invalid")
    assert "missing_field.yaml" in str(exc_info.value)


def test_load_scenarios_empty_directory_returns_empty_list():
    scenarios = load_scenarios(FIXTURES_DIR / "empty")
    assert scenarios == []
    assert list_scenarios() == []


def test_load_scenarios_missing_directory_returns_empty_list():
    scenarios = load_scenarios(FIXTURES_DIR / "does-not-exist")
    assert scenarios == []


def test_duplicate_scenario_ids_last_file_wins():
    scenarios = load_scenarios(FIXTURES_DIR / "duplicates")
    assert len(scenarios) == 1
    assert scenarios[0].title == "Second Definition"
