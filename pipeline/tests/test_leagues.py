import tomllib
from datetime import date
from pathlib import Path

import pytest

from pipeline.leagues import (
    can_change,
    complete,
    get_path,
    league_dates,
    parse_overrides,
    resolve,
    validate,
)

STANDARD = Path(__file__).resolve().parents[1] / "presets" / "standard.toml"


@pytest.fixture
def standard():
    with open(STANDARD, "rb") as f:
        return complete(tomllib.load(f)["settings"])


def test_the_standard_preset_is_valid(standard):
    assert validate(standard) == []
    assert get_path(standard, "roster_rules.chamber_slots") is None


def test_overrides_change_only_the_league_not_the_preset(standard):
    league = resolve(standard, parse_overrides(["budget_rules.annual_budget=40000",
                                                'roster_rules.chamber_slots={"house": 6, "senate": 3}']))
    assert validate(league) == []
    assert league["budget_rules"]["annual_budget"] == 40000
    assert standard["budget_rules"]["annual_budget"] != 40000
    assert league["roster_rules"]["chamber_slots"] == {"house": 6, "senate": 3}


def test_override_values_parse_as_json_or_strings():
    assert parse_overrides(["a=3", "b=null", "c=head_to_head", 'd={"x": 1}']) == [
        ("a", 3), ("b", None), ("c", "head_to_head"), ("d", {"x": 1})]
    with pytest.raises(ValueError):
        parse_overrides(["no_equals_sign"])


@pytest.mark.parametrize("override, message", [
    ("budget_rules.annual_budge=1", "unknown setting budget_rules.annual_budge"),
    ("budget_rules.annual_budget=0", "budget_rules.annual_budget must be at least 1"),
    ("budget_rules.annual_budget=12.5", "budget_rules.annual_budget must be"),
    ("roster_rules.roster_limit=true", "roster_rules.roster_limit must be"),
    ("win_condition=draft", "win_condition must be one of cumulative, head_to_head"),
    ("drop_cost.points_penalty=-5", "drop_cost.points_penalty must be at least 0"),
    ("win_condition=null", "win_condition can't be null"),
    ('roster_rules.chamber_slots={"house": 2, "senate": 2}', "chamber slots (2 + 2) can't fill a roster of 8"),
    ('roster_rules.chamber_slots={"house": 9, "senate": 2}', "can't exceed the roster limit (8)"),
    ('roster_rules.chamber_slots={"house": 8}', "needs exactly house and senate"),
])
def test_invalid_settings_are_rejected_with_a_reason(standard, override, message):
    errors = validate(resolve(standard, parse_overrides([override])))
    assert any(message in e for e in errors), errors


def test_missing_settings_are_reported(standard):
    del standard["drop_cost"]
    assert "drop_cost.extra_fee is missing" in validate(standard)


@pytest.mark.parametrize("kind, kwargs, expected", [
    ("session", {"congress": 119, "session": 2}, (date(2026, 1, 3), date(2027, 1, 3))),
    ("annual", {"year": 2026}, (date(2026, 1, 1), date(2027, 1, 1))),
    ("representative", {"congress": 119}, (date(2025, 1, 3), date(2027, 1, 3))),
    ("presidential", {"year": 2025}, (date(2025, 1, 20), date(2029, 1, 20))),
    ("senatorial", {"year": 2027}, (date(2027, 1, 3), date(2033, 1, 3))),
    ("flexible_private", {"start": date(2027, 2, 1), "end": date(2027, 6, 1)}, (date(2027, 2, 1), date(2027, 6, 1))),
])
def test_league_dates_follow_the_real_calendar(kind, kwargs, expected):
    assert league_dates(kind, **kwargs) == expected


@pytest.mark.parametrize("kind, kwargs", [
    ("session", {"congress": 119}),
    ("presidential", {"year": 2026}),
    ("senatorial", {"year": 2026}),
    ("flexible_private", {"start": date(2027, 6, 1), "end": date(2027, 2, 1)}),
    ("weekly", {}),
])
def test_bad_league_timings_are_rejected(kind, kwargs):
    with pytest.raises(ValueError):
        league_dates(kind, **kwargs)


def test_a_league_freezes_when_it_starts():
    assert can_change(date(2027, 1, 3), today=date(2027, 1, 2))
    assert not can_change(date(2027, 1, 3), today=date(2027, 1, 3))
