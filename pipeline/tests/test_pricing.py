from copy import deepcopy

import pytest

from pipeline.cli import DEFAULT_RULESET
from pipeline.download import pricing_cycle
from pipeline.pricing import HeldSeat, Member, carried_seats, charged, fees, market_multiplier, percentiles, price_session, session_cost
from pipeline.scoring import Ruleset

CFG = Ruleset.load(DEFAULT_RULESET).raw["pricing"]


def member(bid, chamber="rep", seat=70.0, part=1.0, rate=150.0, receipts=1e6, up=True):
    return Member(bid, chamber, seat, part, rate, receipts, up)


def test_percentiles_mid_rank_with_ties():
    pct = percentiles({"a": 1, "b": 2, "c": 2, "d": 9})
    assert pct == {"a": 0.125, "b": 0.5, "c": 0.5, "d": 0.875}


def test_multiplier_spans_donations_band_and_clamps():
    assert market_multiplier(0.5, False, CFG) == pytest.approx(1.0)
    assert market_multiplier(1.0, False, CFG) == pytest.approx(1 + CFG["donations_band"])
    assert market_multiplier(0.0, True, CFG) == pytest.approx((1 - CFG["donations_band"]) * (1 + CFG["reelection_premium"]))
    wide = dict(CFG, donations_band=0.9)
    assert market_multiplier(1.0, True, wide) == CFG["multiplier_max"]
    assert market_multiplier(0.0, False, wide) == CFG["multiplier_min"]


def test_session_cost_rounds_to_step():
    cfg = dict(CFG, price_per_point=14, round_to=10)
    assert session_cost(357.0, 1.0, cfg) == 5000  # 4,998 rounds to 5,000
    assert session_cost(357.0, 1.1, cfg) == 5500


def test_signing_fee_and_weekly_fees_add_up_to_the_session_cost():
    signing, weekly = fees(5200, CFG)
    assert signing == 5200 * CFG["signing_fee_share"]
    assert signing + weekly * CFG["weeks"] == pytest.approx(5200)


def test_dropping_or_leaving_stops_weekly_charges_but_keeps_the_signing_fee():
    p = price_session([member("a")], CFG)[0]
    assert charged(p, 0) == p.signing_fee
    assert charged(p, CFG["weeks"]) == pytest.approx(p.session_cost)
    assert charged(p, 10) < charged(p, 20)


def test_projection_shrinks_productivity_toward_the_chamber_median():
    members = [member("lo", rate=100), member("mid", rate=200), member("hi", rate=400)]
    by_id = {p.bioguide_id: p for p in price_session(members, CFG)}
    k = CFG["productivity_shrink"]
    assert by_id["mid"].projected_productivity == pytest.approx(200)
    assert by_id["hi"].projected_productivity == pytest.approx(200 + k * 200)
    assert by_id["lo"].projected_productivity == pytest.approx(200 - k * 100)


def test_missing_history_falls_back_to_chamber_medians():
    members = [member("a", part=0.9, rate=100), member("b", part=0.95, rate=300),
               member("new", part=None, rate=None, seat=100)]
    new = next(p for p in price_session(members, CFG) if p.bioguide_id == "new")
    assert new.projected_productivity == pytest.approx(200)  # median of 100, 200 (shrunk), 300
    assert new.projected_power == pytest.approx(100 * 0.925)


def test_power_uses_seats_held_on_day_one_times_last_participation():
    p = price_session([member("a", seat=140.0, part=0.9)], CFG)[0]
    assert p.projected_power == pytest.approx(126.0)


def test_donations_rank_within_chamber_and_election_status():
    members = [member("rich_up", receipts=9e6, up=True), member("poor_up", receipts=1e5, up=True),
               member("rich_not", receipts=5e5, up=False), member("poor_not", receipts=1e4, up=False),
               member("sen", chamber="sen", receipts=1.0, up=False)]
    m = {p.bioguide_id: p.multiplier for p in price_session(members, CFG)}
    band, prem = CFG["donations_band"], CFG["reelection_premium"]
    # $500K tops the members not up for election, so it ranks like the $9M fundraiser
    assert m["rich_not"] == pytest.approx(1 + band * 0.5)
    assert m["rich_up"] == pytest.approx((1 + band * 0.5) * (1 + prem))
    assert m["poor_up"] == pytest.approx((1 - band * 0.5) * (1 + prem))
    assert m["sen"] == pytest.approx(1.0)  # alone in its group: the median


def test_members_without_receipts_rank_at_the_median():
    members = [member("a", receipts=1e5), member("b", receipts=9e6), member("appointed", receipts=None)]
    m = {p.bioguide_id: p.multiplier for p in price_session(members, CFG)}
    assert m["appointed"] == pytest.approx(1 + CFG["reelection_premium"])
    assert m["a"] < m["appointed"] < m["b"]


def test_pricing_cycle_is_the_last_one_complete_at_session_start():
    assert pricing_cycle(118, 1) == 2022  # Jan 2023
    assert pricing_cycle(118, 2) == 2022  # Jan 2024: the 2024 cycle is half done
    assert pricing_cycle(119, 1) == 2024


def test_ruleset_prices_the_median_critter_near_5000():
    cfg = deepcopy(CFG)
    assert session_cost(357, 1.0, cfg) == pytest.approx(5000, abs=cfg["round_to"])


POSITIONS = Ruleset.load(DEFAULT_RULESET).raw["positions"]


def test_returning_members_carry_their_seats_and_newcomers_get_the_freshman_median():
    held = [HeldSeat("VET", "rep", "COMMITTEE_SEAT", "member", 70.0),
            HeldSeat("VET", "rep", "SUBCOMMITTEE_SEAT", "member", 7.0),
            HeldSeat("FROSH1", "rep", "COMMITTEE_SEAT", "member", 40.0),
            HeldSeat("FROSH2", "rep", "COMMITTEE_SEAT", "member", 100.0),
            HeldSeat("MOVER", "rep", "COMMITTEE_SEAT", "chair", 300.0)]
    before = {"VET": "rep", "FROSH1": "rep", "FROSH2": "rep", "MOVER": "rep", "NOSEATS": "rep"}
    now = {"VET": "rep", "NOSEATS": "rep", "NEW": "rep", "MOVER": "sen"}
    out = carried_seats(held, set(), {"FROSH1", "FROSH2"}, POSITIONS, now, before)
    assert out["VET"] == pytest.approx(77.0)
    assert out["NOSEATS"] == 0.0  # returning without committee seats
    assert out["NEW"] == pytest.approx(70.0)  # median of last Congress's House freshmen
    assert out["MOVER"] == 0.0  # new to the Senate: no Senate freshmen on record here


def test_a_majority_change_swaps_chairs_and_ranking_members():
    held = [HeldSeat("CHAIR", "sen", "COMMITTEE_SEAT", "chair", 129.0),
            HeldSeat("RANK", "sen", "COMMITTEE_SEAT", "ranking_member", 86.0),
            HeldSeat("SUBCHAIR", "sen", "SUBCOMMITTEE_SEAT", "chair", 21.5),
            HeldSeat("HOUSE", "rep", "COMMITTEE_SEAT", "chair", 300.0)]
    seated = {b: c for b, c in [("CHAIR", "sen"), ("RANK", "sen"), ("SUBCHAIR", "sen"), ("HOUSE", "rep")]}
    out = carried_seats(held, {"sen"}, set(), POSITIONS, seated, seated)
    assert out["CHAIR"] == pytest.approx(86.0)
    assert out["RANK"] == pytest.approx(129.0)
    assert out["SUBCHAIR"] == pytest.approx(21.5 / 0.5 * 0.25)
    assert out["HOUSE"] == pytest.approx(300.0)  # the House majority held
