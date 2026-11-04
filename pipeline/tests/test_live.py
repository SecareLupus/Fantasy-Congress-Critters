from datetime import date, datetime, timedelta

from pipeline.live import SOURCES, congress_on, settle_plan
from pipeline.scoring import Session, week_bounds

SESSION = Session(2, date(2026, 1, 3), date(2027, 1, 3))
BOUNDS = week_bounds(SESSION, 52)


def synced(day: date, **overrides) -> dict:
    return {s: overrides.get(s, datetime(day.year, day.month, day.day, 6)) for s in SOURCES}


def none_missing(end: date) -> list[str]:
    return []


def test_the_congress_in_session_turns_over_on_january_3():
    assert congress_on(date(2027, 1, 2)) == 119
    assert congress_on(date(2027, 1, 3)) == 120
    assert congress_on(date(2026, 11, 3)) == 119


def test_weeks_settle_in_order_once_over_for_three_days():
    day = BOUNDS[2][1] + timedelta(days=3)  # week 3 ended three days ago
    weeks, waiting = settle_plan(BOUNDS, set(), day, synced(day), none_missing)
    assert (weeks, waiting) == ([1, 2, 3], None)
    weeks, _ = settle_plan(BOUNDS, {1, 2}, day - timedelta(days=1), synced(day), none_missing)
    assert weeks == []


def test_a_week_waits_for_every_source_to_sync_after_it():
    day = BOUNDS[0][1] + timedelta(days=3)
    stale = synced(day, senate_votes=datetime(day.year, day.month, day.day - 1, 23))
    weeks, waiting = settle_plan(BOUNDS, set(), day, stale, none_missing)
    assert weeks == [] and "senate_votes" in waiting
    weeks, _ = settle_plan(BOUNDS, set(), day, synced(day, rosters=None), none_missing,
                           sources=tuple(s for s in SOURCES if s != "rosters"))
    assert weeks == [1]


def test_a_week_waits_for_roll_calls_bill_actions_cite():
    day = BOUNDS[1][1] + timedelta(days=3)
    missing = lambda end: ["Senate 12"] if end > BOUNDS[0][1] else []  # noqa: E731
    weeks, waiting = settle_plan(BOUNDS, set(), day, synced(day), missing)
    assert weeks == [1] and waiting.startswith("week 2 waits for 1 roll calls")
