from datetime import date

from pipeline.rosters import (
    Seat,
    build_memberships,
    clip_to_terms,
    committee_code,
    parse_snapshot,
    role,
)

START, END = date(2023, 1, 3), date(2025, 1, 3)


def seat(code="hsag00", who="A000001", role_="member", title=None, side="majority"):
    return Seat(code, who, side, role_, title)


def test_committee_codes_match_billstatus():
    assert committee_code("HSAG") == "hsag00"
    assert committee_code("HSAG15") == "hsag15"


def test_titles_normalize_to_roles():
    assert [role(t) for t in (None, "Chairman", "Chairwoman", "Ranking Member", "Ex Officio", "Vice Chair")] == [
        "member", "chair", "chair", "ranking_member", "ex_officio", "vice_chair"
    ]


def test_parse_snapshot():
    data = {"HSAG": [{"name": "A", "party": "majority", "rank": 1, "title": "Chairman", "bioguide": "A000001"}],
            "HSAG15": [{"name": "B", "party": "minority", "rank": 1, "bioguide": "B000002"}]}
    assert parse_snapshot(data) == {
        seat("hsag00", "A000001", "chair", "Chairman"),
        seat("hsag15", "B000002", "member", side="minority"),
    }


def test_first_snapshot_seats_start_with_the_congress_and_open_seats_end_with_it():
    [m] = build_memberships([(date(2023, 2, 17), {seat()}), (date(2023, 5, 1), {seat()})], START, END)
    assert (m.start_date, m.end_date, m.first_seen, m.last_seen) == (START, END, date(2023, 2, 17), date(2023, 5, 1))


def test_role_change_takes_effect_at_the_snapshot_that_shows_it():
    member, chair = seat(), seat(role_="chair", title="Chair")
    snapshots = [(date(2023, 2, 17), {member}), (date(2024, 5, 1), {chair})]
    by_role = {m.seat.role: m for m in build_memberships(snapshots, START, END)}
    assert (by_role["member"].start_date, by_role["member"].end_date) == (START, date(2024, 5, 1))
    assert (by_role["chair"].start_date, by_role["chair"].end_date) == (date(2024, 5, 1), END)


def test_consecutive_terms_do_not_split_a_seat():
    [m] = build_memberships([(date(2023, 2, 17), {seat()})], START, END)
    terms = [(date(2021, 1, 3), date(2023, 1, 3)), (date(2023, 1, 3), date(2025, 1, 3))]
    [piece] = clip_to_terms(m, terms)
    assert (piece.start_date, piece.end_date) == (START, END)


def test_seat_ends_the_day_after_the_term_ends():
    [m] = build_memberships([(date(2023, 2, 17), {seat()}), (date(2023, 11, 14), set())], START, END)
    [piece] = clip_to_terms(m, [(date(2023, 1, 3), date(2023, 9, 29))])
    assert piece.end_date == date(2023, 9, 30)


def test_member_who_joined_between_snapshots_holds_the_seat_from_day_one():
    snapshots = [(date(2023, 11, 14), set()), (date(2024, 3, 6), {seat()})]
    [m] = build_memberships(snapshots, START, END)
    [piece] = clip_to_terms(m, [(date(2023, 11, 21), date(2025, 1, 3))])
    assert piece.start_date == date(2023, 11, 21)


def test_member_seated_before_the_last_empty_snapshot_waits_for_the_snapshot():
    snapshots = [(date(2023, 11, 14), set()), (date(2024, 3, 6), {seat()})]
    [m] = build_memberships(snapshots, START, END)
    [piece] = clip_to_terms(m, [(date(2023, 11, 7), date(2025, 1, 3))])
    assert piece.start_date == date(2024, 3, 6)
