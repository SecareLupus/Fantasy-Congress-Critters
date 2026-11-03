from datetime import date, timedelta

import pytest

from pipeline.ledger import Calendar, Refused, budget, drop, penalties, points, purchase
from pipeline.scoring import Session, ScoreItem, WeeklyParticipation, weekly_points

SESSION = Session(2, date(2024, 1, 3), date(2025, 1, 3))
CAL = Calendar.build(SESSION, 52, date(2024, 1, 3), date(2025, 1, 3))
SETTINGS = {
    "budget_rules": {"annual_budget": 50000},
    "roster_rules": {"roster_limit": 3, "chamber_slots": None},
    "win_condition": "cumulative",
    "drop_cost": {"extra_fee": 0, "points_penalty": 0},
}
# Session Cost $5,200: $1,300 signing, then $75 a week.
PRICE = {"chamber": "rep", "session_cost": 5200, "signing_fee": 1300.0, "weekly_fee": 75.0}


def buy(held, day, bioguide="A", settings=SETTINGS, left_office=None, **price):
    h = purchase(held, CAL, settings, day, bioguide_id=bioguide, left_office=left_office, **{**PRICE, **price})
    held.append(h)
    return h


def test_a_purchase_before_the_session_reserves_every_week():
    held = []
    h = buy(held, date(2024, 1, 2))
    assert (h.first_week, h.last_week) == (1, 52)
    before = budget(held, CAL, 50000, date(2024, 1, 2))
    assert (before.spent, before.reserved) == (1300, 52 * 75)
    first_day = budget(held, CAL, 50000, date(2024, 1, 3))
    assert (first_day.spent, first_day.reserved) == (1300 + 75, 51 * 75)
    assert first_day.available == 50000 - 5200


def test_a_purchase_during_a_week_is_held_from_the_next():
    held = []
    h = buy(held, CAL.start(10) + timedelta(days=3))
    assert (h.first_week, h.last_week) == (11, 52)
    assert budget(held, CAL, 50000, h.made_on).reserved == 42 * 75


def test_purchases_are_refused_with_a_reason():
    held = []
    with pytest.raises(Refused, match="more than the \\$50,000.00 available"):
        buy(held, date(2024, 1, 2), session_cost=60000, signing_fee=15000.0, weekly_fee=865.38)
    buy(held, date(2024, 1, 2), "A")
    with pytest.raises(Refused, match="already on the roster"):
        buy(held, date(2024, 2, 1), "A")
    buy(held, date(2024, 1, 2), "B")
    buy(held, date(2024, 1, 2), "C")
    with pytest.raises(Refused, match="roster is full"):
        buy(held, date(2024, 1, 2), "D")
    with pytest.raises(Refused, match="no league weeks"):
        buy([], CAL.start(52) + timedelta(days=1))
    with pytest.raises(Refused, match="leaves office"):
        buy([], date(2024, 3, 1), left_office=date(2024, 3, 4))


def test_chamber_slots_limit_each_chamber():
    settings = {**SETTINGS, "roster_rules": {"roster_limit": 3, "chamber_slots": {"house": 2, "senate": 1}}}
    held = []
    buy(held, date(2024, 1, 2), "S1", settings, chamber="sen")
    with pytest.raises(Refused, match="senate slots are full"):
        buy(held, date(2024, 1, 2), "S2", settings, chamber="sen")
    buy(held, date(2024, 1, 2), "H1", settings)


def test_a_drop_keeps_the_week_paid_for_and_returns_the_rest():
    held = []
    buy(held, date(2024, 1, 2))
    day = CAL.start(20) + timedelta(days=2)
    h = drop(held, CAL, SETTINGS, day, "A")
    assert h.drop_week == 21
    held[0] = h
    after = budget(held, CAL, 50000, day)
    assert (after.spent, after.reserved) == (1300 + 20 * 75, 0)
    assert h.held_weeks(CAL, date(2025, 1, 3)) == list(range(1, 21))
    # Rebuying costs a new signing fee.
    again = buy(held, day)
    assert again.first_week == 21
    assert budget(held, CAL, 50000, day).spent == 2 * 1300 + 20 * 75


def test_a_drop_charges_the_leagues_drop_cost():
    settings = {**SETTINGS, "drop_cost": {"extra_fee": 500, "points_penalty": 25}}
    held = []
    buy(held, date(2024, 1, 2), settings=settings)
    held[0] = drop(held, CAL, settings, date(2024, 1, 2), "A")
    assert held[0].held_weeks(CAL, date(2024, 1, 2)) == []
    assert budget(held, CAL, 50000, date(2024, 1, 2)).spent == 1300 + 500
    assert penalties(held, date(2024, 1, 2)) == 25
    poor = {**settings, "budget_rules": {"annual_budget": 5300}}
    held = []
    buy(held, date(2024, 1, 2), settings=poor)
    with pytest.raises(Refused, match="drop fee"):
        drop(held, CAL, poor, CAL.start(52), "A")


def test_a_critter_who_leaves_office_frees_the_slot_and_the_reservation():
    left = CAL.start(30) + timedelta(days=4)
    held = []
    buy(held, date(2024, 1, 2), left_office=left)
    # Before it happens, the reservation stands.
    assert budget(held, CAL, 50000, left - timedelta(days=1)).reserved == 22 * 75
    after = budget(held, CAL, 50000, left)
    assert (after.spent, after.reserved) == (1300 + 30 * 75, 0)
    assert not held[0].active(left)
    with pytest.raises(Refused, match="not on the roster"):
        drop(held, CAL, SETTINGS, left, "A")


def test_points_count_held_weeks_once_they_end():
    weekly = {("A", w): (1.0, 2.0) for w in range(1, 53)}
    held = []
    h = buy(held, CAL.start(10) + timedelta(days=1))
    assert points(h, CAL, weekly, CAL.start(11)) == (0, 0)
    assert points(h, CAL, weekly, CAL.end(13)) == (3.0, 6.0)
    assert points(h, CAL, weekly, SESSION.end) == (42.0, 84.0)


def test_a_league_counts_only_weeks_that_start_inside_it():
    session = Session(1, date(2025, 1, 3), date(2026, 1, 3))
    cal = Calendar.build(session, 52, date(2025, 1, 20), date(2029, 1, 20))
    assert cal.weeks[0] == 4 and cal.weeks[-1] == 52
    assert cal.next_week(date(2025, 1, 1)) == 4


def test_weekly_points_add_up_to_the_items():
    rates = [1.0] * 52
    rates[1] = 0.5
    participation = WeeklyParticipation({("A", 2): rates}, [SESSION], 52)
    days = 20
    seat_rate = (7 * 1.0 + 7 * 0.5 + 6 * 1.0) / days
    items = [
        # A seat held days 0-19 of the session, worth 366 a session.
        ScoreItem("A", 2, "power", "COMMITTEE_SEAT", SESSION.start, 366 * days / 366 * seat_rate,
                  detail={"value": 366.0, "days": days, "session_days": 366}),
        ScoreItem("A", 2, "productivity", "VOTE_CAST", CAL.start(2), 4.0, detail={"week": 2}),
        ScoreItem("A", 2, "productivity", "BILL_INTRODUCED", CAL.start(3) + timedelta(days=6), 5.0),
    ]
    weekly = weekly_points(items, [SESSION], participation, 52)
    assert weekly[("A", 2, 1)] == pytest.approx([7.0, 0])
    assert weekly[("A", 2, 2)] == pytest.approx([3.5, 4.0])
    assert weekly[("A", 2, 3)] == pytest.approx([6.0, 5.0])
    assert sum(p for p, _ in weekly.values()) == pytest.approx(items[0].points)
