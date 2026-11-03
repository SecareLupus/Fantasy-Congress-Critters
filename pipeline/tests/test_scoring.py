from copy import deepcopy
from datetime import date

import pytest

from pipeline.cli import DEFAULT_RULESET
from pipeline.scoring import (
    BillInputs,
    Cosponsor,
    EventRow,
    Position,
    Ruleset,
    VoteRow,
    apply_caps,
    apply_chamber_factor,
    bill_weight,
    coalition_ranks,
    congress_sessions,
    cosponsor_category,
    floor_participation,
    is_ceremonial,
    score_bill,
    score_positions,
    score_votes,
    stage_cutoffs,
)

SESSIONS = congress_sessions(118)
D = date


@pytest.fixture
def ruleset():
    """The default ruleset with the productivity scale removed, so points read plainly."""
    rs = Ruleset.load(DEFAULT_RULESET)
    raw = deepcopy(rs.raw)
    raw["productivity"]["scale"] = 1.0
    return Ruleset(rs.version, raw)


def event(event_type, day, chamber="House", committee=None, critter=None, amendment=None):
    return EventRow(event_type, day, chamber, committee, critter, amendment)


def cosponsor(who, day, original=False, withdrawn=None):
    return Cosponsor(who, day, original, withdrawn)


def bill(events, cosponsors=(), sponsor="SPONSOR", by_request=False, bill_type="hr"):
    return BillInputs("118-hr-1", bill_type, sponsor, by_request, "House", list(cosponsors), list(events))


def never(*_):
    return False


def by_category(items):
    out = {}
    for i in items:
        out.setdefault(i.category, {})[i.bioguide_id] = i
    return out


# --- authorship ---------------------------------------------------------------------

def test_stage_cutoffs_skip_missing_stages():
    events = [event("REPORTED", D(2023, 5, 1)), event("FLOOR_CONSIDERATION", D(2023, 6, 1)),
              event("COMMITTEE_HEARING_HELD", D(2023, 2, 1), chamber="Senate")]
    # No House hearing or markup: the Early window runs until the report.
    assert stage_cutoffs(events, "House") == [D(2023, 5, 1), D(2023, 5, 1), D(2023, 6, 1)]


def test_cosponsor_categories_follow_bill_progress():
    cutoffs = [D(2023, 3, 1), D(2023, 5, 1), D(2023, 6, 1)]
    assert [cosponsor_category(cosponsor("X", day, original), cutoffs) for day, original in [
        (D(2023, 1, 9), True), (D(2023, 2, 1), False), (D(2023, 3, 1), False),
        (D(2023, 5, 15), False), (D(2023, 7, 1), False), (D(2023, 9, 1), True),
    ]] == ["early", "early", "mid", "late", "procedural", "early"]


def test_same_day_cosponsors_share_a_rank():
    ranks = coalition_ranks([cosponsor("A", D(2023, 1, 9)), cosponsor("B", D(2023, 1, 9)),
                             cosponsor("C", D(2023, 2, 1))])
    assert ranks == {"A": 2, "B": 2, "C": 4}


def test_introduction_scores_the_author_and_by_request_scores_procedural(ruleset):
    intro = [event("BILL_INTRODUCED", D(2023, 1, 9), critter="SPONSOR")]
    [authored] = score_bill(bill(intro), ruleset, SESSIONS, never)
    [requested] = score_bill(bill(intro, by_request=True), ruleset, SESSIONS, never)
    assert authored.points == 2.0 * 5.0
    assert requested.points == pytest.approx(2.0 * 0.2)


def test_cosponsor_points_use_category_and_dilution(ruleset):
    events = [event("COSPONSOR_ADDED", D(2023, 1, 9), critter="A"),
              event("COSPONSOR_ADDED", D(2023, 2, 1), critter="B")]
    items = score_bill(bill(events, [cosponsor("A", D(2023, 1, 9), True), cosponsor("B", D(2023, 2, 1))]),
                       ruleset, SESSIONS, never)
    points = {i.bioguide_id: i.points for i in items}
    assert points["A"] == pytest.approx(1.0 * 2.5 / 2 ** 0.5)  # early, rank 2
    assert points["B"] == pytest.approx(1.0 * 2.5 / 3 ** 0.5)  # early (no stages yet), rank 3


def test_simple_resolutions_are_weighted_down(ruleset):
    intro = [event("BILL_INTRODUCED", D(2023, 1, 9), critter="SPONSOR")]
    [item] = score_bill(bill(intro, bill_type="sres"), ruleset, SESSIONS, never)
    assert item.points == pytest.approx(2.0 * 5.0 * 0.2)


def named(title="", subjects=(), bill_type="hr"):
    b = bill([], bill_type=bill_type)
    b.title, b.subjects = title, list(subjects)
    return b


def test_ceremonial_bills_by_title_or_narrow_tribute_tag(ruleset):
    assert is_ceremonial(named("To designate the facility of the United States Postal Service at 1 Main St"), ruleset)
    assert is_ceremonial(named("To name the Department of Veterans Affairs clinic in Gallup as the X Clinic"), ruleset)
    assert is_ceremonial(named("James R. Dominguez Memorial Act", ["Congressional tributes", "Veterans"]), ruleset)
    # A big bill tagged for one naming section is not ceremonial.
    assert not is_ceremonial(named("National Defense Authorization Act",
                                   ["Congressional tributes"] + [f"s{n}" for n in range(20)]), ruleset)
    assert not is_ceremonial(named("Secure the Border Act", ["Immigration"]), ruleset)


def test_ceremonial_weight_replaces_a_higher_bill_type_weight(ruleset):
    postal = "To designate the facility of the United States Postal Service at 1 Main St"
    assert bill_weight(named(postal), ruleset) == 0.2
    assert bill_weight(named(postal, bill_type="hconres"), ruleset) == 0.2
    assert bill_weight(named("Congratulating a team", bill_type="sres"), ruleset) == 0.2
    assert bill_weight(named("Secure the Border Act"), ruleset) == 1.0


# --- who scores ---------------------------------------------------------------------

def test_passage_credits_backers_at_the_time_with_dilution(ruleset):
    cosponsors = [cosponsor("EARLY", D(2023, 1, 9), True),
                  cosponsor("GONE", D(2023, 1, 9), True, withdrawn=D(2023, 3, 1)),
                  cosponsor("AFTER", D(2023, 8, 1))]
    items = score_bill(bill([event("PASSED_CHAMBER", D(2023, 6, 1))], cosponsors), ruleset, SESSIONS, never)
    passed = {i.bioguide_id: i.points for i in items}
    assert set(passed) == {"SPONSOR", "EARLY"}
    assert passed["SPONSOR"] == 20.0 * 5.0
    assert passed["EARLY"] == pytest.approx(20.0 * 2.5 / 2 ** 0.5)


def test_law_uses_the_heavy_dilution_curve(ruleset):
    items = score_bill(bill([event("BECAME_LAW", D(2023, 9, 1), chamber=None)],
                            [cosponsor("A", D(2023, 1, 9), True)]), ruleset, SESSIONS, never)
    law = {i.bioguide_id: i.points for i in items}
    assert law["A"] == pytest.approx(50.0 * 2.5 / 2)


def test_committee_events_score_only_backers_on_the_committee(ruleset):
    seats = {("A", "hsii00")}

    def on_committee(who, code, day):
        return (who, code[:4] + "00") in seats

    events = [event("COMMITTEE_MARKUP", D(2023, 5, 1), committee="hsii10")]
    items = score_bill(bill(events, [cosponsor("A", D(2023, 1, 9), True), cosponsor("B", D(2023, 1, 9), True)]),
                       ruleset, SESSIONS, on_committee)
    assert [(i.bioguide_id, i.points) for i in items] == [("A", 6.0)]


def test_repeated_actions_score_once_per_chamber(ruleset):
    events = [event("PLACED_ON_CALENDAR", D(2023, 5, 1)), event("PLACED_ON_CALENDAR", D(2023, 5, 9)),
              event("PASSED_CHAMBER", D(2023, 6, 1)), event("PASSED_CHAMBER", D(2023, 9, 1), chamber="Senate")]
    items = score_bill(bill(events), ruleset, SESSIONS, never)
    assert sorted((i.category, i.item_date) for i in items) == [
        ("PASSED_CHAMBER", D(2023, 6, 1)), ("PASSED_CHAMBER", D(2023, 9, 1)),
        ("PLACED_ON_CALENDAR", D(2023, 5, 1)),
    ]


def test_amendment_events_credit_the_amendment_sponsor_as_author(ruleset):
    events = [event("AMENDMENT_ADOPTED", D(2023, 7, 13), critter="AMENDER", amendment="118-hamdt-235"),
              event("AMENDMENT_ADOPTED", D(2023, 7, 12), critter=None, amendment="118-hamdt-12")]
    items = score_bill(bill(events), ruleset, SESSIONS, never)
    assert [(i.bioguide_id, i.points, i.amendment_id) for i in items] == [("AMENDER", 20.0, "118-hamdt-235")]


def test_caps_keep_only_the_first_items_of_a_session(ruleset):
    ruleset.raw["caps"]["BILL_INTRODUCED"] = 2
    items = []
    for n, day in enumerate([D(2023, 3, 1), D(2023, 1, 9), D(2023, 2, 1), D(2024, 2, 1)]):
        b = BillInputs(f"118-hr-{n}", "hr", "X", False, "House", [],
                       [event("BILL_INTRODUCED", day, critter="X")])
        items += score_bill(b, ruleset, SESSIONS, never)
    apply_caps(items, ruleset)
    scored = sorted((i.item_date, i.points > 0) for i in items)
    assert scored == [(D(2023, 1, 9), True), (D(2023, 2, 1), True), (D(2023, 3, 1), False), (D(2024, 2, 1), True)]


# --- votes --------------------------------------------------------------------------

def vote(position, question="On Passage", result="Passed", who="X", day=D(2023, 5, 1), vote_id="118-s1-1"):
    return VoteRow(vote_id, day, question, result, None, who, position)


def test_votes_score_when_cast_by_a_seated_member(ruleset):
    votes = [vote("yea"), vote("present"), vote("not_voting"), vote("nay", who="DEPARTED")]
    items = score_votes(votes, ruleset, SESSIONS, lambda who, day: who != "DEPARTED")
    assert [i.category for i in items] == ["VOTE_CAST", "VOTE_CAST"]


def test_perfect_attendance_is_worth_the_same_in_both_chambers(ruleset):
    rules = ruleset.raw["votes"]
    [house] = score_votes([vote("yea", vote_id="118-h1-1")], ruleset, SESSIONS, lambda *_: True)
    [senate] = score_votes([vote("yea", vote_id="118-s1-1")], ruleset, SESSIONS, lambda *_: True)
    assert house.points * rules["expected_roll_calls"]["rep"] == pytest.approx(rules["full_attendance"])
    assert senate.points * rules["expected_roll_calls"]["sen"] == pytest.approx(rules["full_attendance"])


def test_delegate_votes_are_valued_against_committee_of_the_whole_roll_calls(ruleset):
    rules = ruleset.raw["votes"]
    [delegate] = score_votes([vote("yea", who="NORTON", vote_id="118-h1-1")], ruleset, SESSIONS,
                             lambda *_: True, delegates=frozenset({"NORTON"}))
    assert delegate.points * rules["expected_roll_calls"]["delegate"] == pytest.approx(rules["full_attendance"])


def test_yea_on_a_confirmed_nomination_scores_extra(ruleset):
    votes = [vote("yea", "On the Nomination", "Nomination Confirmed"),
             vote("nay", "On the Nomination", "Nomination Confirmed", who="Y")]
    items = score_votes(votes, ruleset, SESSIONS, lambda *_: True)
    assert sorted((i.bioguide_id, i.category) for i in items) == [
        ("X", "CONFIRMATION_SUCCESS"), ("X", "VOTE_CAST"), ("Y", "VOTE_CAST")]


def test_senate_productivity_factor_spares_votes_and_power(ruleset):
    from pipeline.scoring import ScoreItem
    items = [ScoreItem("SEN", 1, "productivity", "PASSED_CHAMBER", D(2023, 5, 1), 10.0, bill_id="118-s-1"),
             ScoreItem("SEN", 1, "productivity", "VOTE_CAST", D(2023, 5, 1), 1.0, vote_id="118-s1-1"),
             ScoreItem("SEN", 1, "power", "COMMITTEE_SEAT", D(2023, 5, 1), 50.0),
             ScoreItem("REP", 1, "productivity", "PASSED_CHAMBER", D(2023, 5, 1), 10.0, bill_id="118-hr-1")]
    apply_chamber_factor(items, ruleset, lambda who, day: "sen" if who == "SEN" else "rep")
    factor = ruleset.raw["productivity"]["chamber_factor"]["sen"]
    assert [i.points for i in items] == [pytest.approx(10.0 * factor), 1.0, 50.0, 10.0]


# --- power --------------------------------------------------------------------------

def seat(code, role="member", start=D(2023, 1, 3), end=D(2025, 1, 3), who="X", kind="committee"):
    return Position(who, kind, code, role, start, end)


def full(*_):
    return 1.0


def test_committee_seats_use_tier_and_role(ruleset):
    items = score_positions([seat("hsap00", "chair"), seat("hsag00"), seat("hsso00", "ranking_member")],
                            ruleset, SESSIONS[:1], full)
    assert sorted(i.points for i in items) == [30.0, 40.0, 300.0]


def test_subcommittee_seats_add_a_bonus_on_the_parent_tier(ruleset):
    items = score_positions([seat("hsap01", "chair"), seat("hsap02")], ruleset, SESSIONS[:1], full)
    assert sorted(i.points for i in items) == [pytest.approx(10.0), 50.0]
    assert {i.category for i in items} == {"SUBCOMMITTEE_SEAT"}


def test_unmapped_committees_and_ex_officio_seats_score_nothing(ruleset):
    assert score_positions([seat("hsxx00"), seat("hsap00", "ex_officio")], ruleset, SESSIONS, full) == []


def test_ad_hoc_and_leadership_values(ruleset):
    items = score_positions([seat("hszt00", "chair"),
                             seat("Speaker of the House", None, kind="leadership"),
                             seat("Some New Post", None, kind="leadership")], ruleset, SESSIONS[:1], full)
    assert sorted((i.category, i.points) for i in items) == [
        ("AD_HOC_SEAT", 30.0), ("LEADERSHIP", 40.0), ("LEADERSHIP", 400.0)]


def test_senate_positions_use_the_chamber_factor(ruleset):
    house, senate = seat("hsap00"), seat("ssap00")
    senate.chamber, house.chamber = "sen", "rep"
    items = score_positions([house, senate], ruleset, SESSIONS[:1], full)
    assert sorted(i.points for i in items) == [100 * ruleset.raw["positions"]["chamber_factor"]["sen"], 100.0]


def test_positions_prorate_by_session_and_multiply_participation(ruleset):
    pos = seat("hsap00", start=D(2023, 7, 3), end=D(2024, 7, 3))
    items = score_positions([pos], ruleset, SESSIONS, lambda who, a, b: 0.5)
    by_session = {i.session: i for i in items}
    assert by_session[1].points == pytest.approx(100 * 184 / 365 * 0.5)
    assert by_session[2].points == pytest.approx(100 * 182 / 366 * 0.5)


def test_floor_participation_skips_exempt_periods():
    votes = [vote("yea", day=D(2023, 2, 1)), vote("not_voting", day=D(2023, 3, 1)),
             vote("not_voting", day=D(2023, 11, 1)), vote("not_voting", day=D(2023, 12, 1))]
    rate = floor_participation(votes, {"X": [(D(2023, 10, 25), D(2025, 1, 3))]})
    assert rate("X", D(2023, 1, 3), D(2024, 1, 3)) == 0.5
    assert rate("X", D(2023, 11, 1), D(2024, 1, 3)) == 1.0  # no votes outside the exempt post
    assert rate("NOBODY", D(2023, 1, 3), D(2024, 1, 3)) == 1.0
