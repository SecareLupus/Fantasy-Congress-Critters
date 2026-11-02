from datetime import date
from pathlib import Path

import pytest

from pipeline.billstatus import parse_bill
from pipeline.normalize import normalize_bill

FIXTURE = Path(__file__).parent / "fixtures" / "billstatus-sample.xml"


@pytest.fixture
def bill():
    return parse_bill(FIXTURE.read_bytes())


@pytest.fixture
def events(bill):
    return normalize_bill(bill)


def of_type(events, event_type):
    return [e for e in events if e.event_type == event_type]


def test_parse_basics(bill):
    assert bill.bill_id == "118-hr-100"
    assert bill.sponsor_id == "A000001"
    assert not bill.sponsor_by_request
    assert [c.is_original for c in bill.cosponsors] == [True, False]
    assert bill.cosponsors[1].withdrawn_date == date(2023, 5, 1)


def test_actions_numbered_oldest_first(bill):
    assert bill.actions[0].action_date == date(2023, 3, 1)
    assert bill.actions[-1].text.startswith("Became Public Law")
    assert [a.seq for a in bill.actions] == list(range(len(bill.actions)))


def test_subcommittee_activities_keep_parent(bill):
    sub = [a for a in bill.committee_activities if a.committee_code == "hsii10"]
    assert {a.parent_committee_code for a in sub} == {"hsii00"}
    assert {a.chamber for a in sub} == {"House"}


def test_introduction_and_cosponsorship(events):
    [intro] = of_type(events, "BILL_INTRODUCED")
    assert (intro.critter_id, intro.chamber) == ("A000001", "House")
    added = of_type(events, "COSPONSOR_ADDED")
    assert [(e.critter_id, e.detail) for e in added] == [("B000002", "original"), ("C000003", None)]
    [withdrawn] = of_type(events, "COSPONSOR_WITHDRAWN")
    assert withdrawn.critter_id == "C000003"


def test_committee_activities(events):
    assert {e.committee_code for e in of_type(events, "COMMITTEE_REFERRAL")} == {"hsii00", "hsii10"}
    [hearing] = [e for e in of_type(events, "COMMITTEE_HEARING_HELD") if e.chamber == "House"]
    assert hearing.committee_code == "hsii10"
    assert of_type(events, "COMMITTEE_MARKUP")[0].event_date == date(2023, 5, 10)
    assert len(of_type(events, "REPORTED")) == 1


def test_ordered_reported_from_text_in_both_chambers(events):
    ordered = of_type(events, "ORDERED_REPORTED")
    assert {(e.chamber, e.committee_code) for e in ordered} == {("House", "hsii00"), ("Senate", "sseg00")}


def test_hearing_held_before_the_bill_existed_is_ignored(events):
    assert all(e.chamber != "Senate" for e in of_type(events, "COMMITTEE_HEARING_HELD"))


def test_action_codes_are_read_per_source(events):
    # E30000 means "Vetoed" from the House floor feed but "Signed" from the Library of Congress;
    # only Library of Congress codes drive presidential events.
    assert of_type(events, "VETOED") == []
    assert len(of_type(events, "BECAME_LAW")) == 1
    assert {e.chamber for e in of_type(events, "PASSED_CHAMBER")} == {"House", "Senate"}
    assert len(of_type(events, "PLACED_ON_CALENDAR")) == 1


def test_cloture_not_invoked_is_not_an_invocation(events):
    assert len(of_type(events, "CLOTURE_FILED")) == 1
    assert of_type(events, "CLOTURE_INVOKED") == []


def test_events_are_unique(events):
    keys = [e.key for e in events]
    assert len(keys) == len(set(keys))
