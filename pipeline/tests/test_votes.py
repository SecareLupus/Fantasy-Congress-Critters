from datetime import date, time
from pathlib import Path

import pytest

from pipeline.votes import legis_bill_id, parse_house_vote, parse_voteview_senate, position_category

FIXTURE = Path(__file__).parent / "fixtures" / "house-vote-sample.xml"


@pytest.fixture
def roll_call():
    return parse_house_vote(FIXTURE.read_bytes())


def test_parse_house_metadata(roll_call):
    assert roll_call.vote_id == "118-h1-39"
    assert (roll_call.vote_date, roll_call.vote_time) == (date(2023, 1, 26), time(17, 32))
    assert roll_call.bill_id == "118-hr-21"
    assert roll_call.amendment_num == "4"
    assert roll_call.result == "Failed"
    assert roll_call.description is None


def test_member_positions_are_normalized(roll_call):
    assert [(m.bioguide_id, m.position) for m in roll_call.members] == [
        ("A000370", "yea"),
        ("A000055", "nay"),
        ("A000371", "not_voting"),
        ("A000372", "present"),
        ("N000147", "yea"),
    ]
    assert roll_call.members[0].raw_position == "Aye"


def test_delegate_state_placeholder_is_dropped(roll_call):
    assert roll_call.members[-1].state is None
    assert roll_call.members[0].state == "NC"


def test_speaker_election_votes_are_other():
    assert position_category("Jeffries") == "other"


@pytest.mark.parametrize(
    "legis_num, bill_id",
    [
        ("H R 21", "118-hr-21"),
        ("H RES 5", "118-hres-5"),
        ("H J RES 7", "118-hjres-7"),
        ("H CON RES 9", "118-hconres-9"),
        ("S 870", "118-s-870"),
        ("S J RES 11", "118-sjres-11"),
        ("HJRES98", "118-hjres-98"),
        ("SCONRES5", "118-sconres-5"),
        ("PN1", None),
        ("TREATYDOC2", None),
        ("QUORUM", None),
        ("ADJOURN", None),
        (None, None),
    ],
)
def test_legis_num_to_bill_id(legis_num, bill_id):
    assert legis_bill_id(118, legis_num) == bill_id


@pytest.fixture
def senate():
    d = Path(__file__).parent / "fixtures" / "voteview"
    return parse_voteview_senate(
        d / "S118_rollcalls.csv", d / "S118_votes.csv", d / "S118_members.csv"
    )


def test_senate_roll_calls_use_the_clerk_number_per_session(senate):
    assert [rc.vote_id for rc in senate] == ["118-s1-1", "118-s2-1"]
    assert senate[1].vote_date == date(2024, 1, 11)


def test_senate_bill_refs_skip_nominations(senate):
    assert (senate[0].legis_num, senate[0].bill_id) == ("PN1", None)
    assert senate[1].bill_id == "118-hjres-98"


def test_senate_positions_map_to_bioguide_and_skip_the_president(senate):
    assert [(m.bioguide_id, m.position, m.party) for m in senate[0].members] == [
        ("T000278", "nay", "R"),
        ("S000033", "yea", "I"),
        ("P000145", "not_voting", "D"),
    ]


def test_paired_positions_were_not_cast(senate):
    [paired] = [m for m in senate[1].members if m.bioguide_id == "S000033"]
    assert (paired.position, paired.raw_position) == ("not_voting", "Paired Yea")
