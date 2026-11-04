from datetime import date

from pipeline.rosters import (
    Seat,
    Senator,
    backfill_starts,
    build_memberships,
    clip_to_terms,
    committee_code,
    house_congress,
    house_seats,
    parse_snapshot,
    role,
    senate_seats,
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


def test_late_listed_committee_seats_start_when_filled():
    named = date(2024, 7, 29)
    early, late = seat("hszt00", "A000001"), seat("hszt00", "B000002")
    snapshots = [(date(2023, 2, 17), {seat()}), (date(2024, 11, 14), {seat()}),
                 (date(2024, 12, 17), {seat(), early}), (date(2024, 12, 20), {seat(), early, late})]
    memberships = build_memberships(snapshots, START, END)
    backfill_starts(memberships, {"hszt00": named})
    starts = {m.seat.bioguide_id: m.start_date for m in memberships if m.seat.committee_code == "hszt00"}
    assert starts == {"A000001": named, "B000002": date(2024, 12, 20)}
    [other] = [m for m in memberships if m.seat.committee_code == "hsag00"]
    assert other.start_date == START
    [piece] = clip_to_terms(next(m for m in memberships if m.seat == early), [(START, date(2025, 1, 3))])
    assert piece.start_date == named


MEMBER_DATA = b"""<MemberData><title-info><congress-num>119</congress-num><majority>R</majority></title-info>
<members>
<member><member-info><bioguideID>T000467</bioguideID><official-name>Glenn Thompson</official-name>
  <party>R</party><caucus>R</caucus></member-info>
  <committee-assignments><committee comcode="AG00" rank="1" leadership="Chair"/>
  <subcommittee subcomcode="AG15" rank="3"/><committee rank="2"/></committee-assignments></member>
<member><member-info><bioguideID>C001119</bioguideID><official-name>Angie Craig</official-name>
  <party>D</party><caucus>D</caucus></member-info>
  <committee-assignments><committee comcode="AG00" rank="1"/><committee comcode="EC00" rank="2"/></committee-assignments></member>
<member><member-info><bioguideID>K000401</bioguideID><official-name>Kevin Kiley</official-name>
  <party>I</party><caucus>R</caucus></member-info>
  <committee-assignments><committee comcode="AG00" rank="9"/></committee-assignments></member>
<member><member-info><bioguideID /></member-info><committee-assignments /></member>
</members></MemberData>"""


def test_house_member_data_becomes_a_snapshot():
    snapshot = house_seats(MEMBER_DATA, {"AG": "HSAG", "EC": "JSEC"})
    assert house_congress(MEMBER_DATA) == 119
    seats = parse_snapshot(snapshot)
    assert seats == {
        seat("hsag00", "T000467", "chair", "Chair"),
        seat("hsag15", "T000467"),
        # The minority's first member is its ranking member.
        seat("hsag00", "C001119", "ranking_member", "Ranking Member", "minority"),
        seat("jsec00", "C001119", side="minority"),
        # An independent sits with the caucus.
        seat("hsag00", "K000401"),
    }
    assert snapshot["JSEC"][0]["chamber"] == "house"


SENATE_XML = """<committee_membership><committees><majority_party>R</majority_party>
<committee_code>SSAF00</committee_code><members>
<member><name><first>John</first><last>Boozman</last></name><state>AR</state><party>R</party><position>Chairman</position></member>
<member><name><first>Ben Ray</first><last>Lujan</last></name><state>NM</state><party>D</party><position>Ranking</position></member>
<member><name><first>Darline</first><last>Graham</last></name><state>SC</state><party>R</party><position>Member</position></member>
<member><name><first>Angus</first><last>King</last></name><state>ME</state><party>I</party><position>Member</position></member>
<member><name><first>New</first><last>Person</last></name><state>OH</state><party>R</party><position>Member</position></member>
</members>
<subcommittee><committee_code>SSAF13</committee_code><members>
<member><name><first>John</first><last>Boozman</last></name><state>AR</state><party>R</party><position>Member</position></member>
</members></subcommittee></committees></committee_membership>""".encode()

SENATORS = [Senator("B001236", "AR", "Boozman", "R"), Senator("L000570", "NM", "Luján", "D"),
            Senator("G000608", "SC", "Graham Nordone", "R"), Senator("S001184", "SC", "Scott", "R"),
            Senator("K000383", "ME", "King", "D")]


def test_senate_lists_match_senators_by_state_and_surname():
    snapshot, unmatched = senate_seats(SENATE_XML, SENATORS)
    assert parse_snapshot(snapshot) == {
        seat("ssaf00", "B001236", "chair", "Chairman"),
        seat("ssaf00", "L000570", "ranking_member", "Ranking Member", "minority"),  # accents folded
        seat("ssaf00", "G000608"),  # the first of two surnames
        seat("ssaf00", "K000383", side="minority"),  # caucus, not party
        seat("ssaf13", "B001236"),
    }
    assert unmatched == ["SSAF New Person (OH)"]


def test_a_senator_whose_term_just_ended_keeps_the_seats_the_senate_still_lists():
    # An appointee's term in congress-legislators ends on election day; they serve on.
    former = SENATORS + [Senator("H001104", "OH", "Person", "R")]
    snapshot, unmatched = senate_seats(SENATE_XML, SENATORS, former)
    assert seat("ssaf00", "H001104") in parse_snapshot(snapshot)
    assert unmatched == []
