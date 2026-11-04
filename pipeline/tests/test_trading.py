"""Buying and dropping from the website, against the local database: a temporary league
on a session that is still open and priced, deleted afterward. Skipped without one."""

import threading
import tomllib
from datetime import date
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from pipeline import auth, db, leagues, play, scoring
from pipeline.api import app

STANDARD = Path(__file__).resolve().parents[1] / "presets" / "standard.toml"
PASSWORD = "a long password"


def _open_priced_session(conn):
    """(ruleset, session) of the latest priced run whose session hasn't ended."""
    for congress, session, ruleset, _ in conn.execute("""
            SELECT DISTINCT r.congress, p.session, r.ruleset, max(r.run_id) OVER (PARTITION BY r.congress, p.session)
            FROM score_runs r JOIN critter_prices p USING (run_id) ORDER BY 4 DESC""").fetchall():
        s = scoring.congress_sessions(congress)[session - 1]
        if date.today() < s.end:
            return ruleset, s
    return None


@pytest.fixture
def league():
    try:
        conn = db.connect()
    except psycopg.OperationalError:
        pytest.skip("Postgres isn't running")
    with conn:
        found = _open_priced_session(conn)
        if found is None:
            pytest.skip("no priced session is open")
        ruleset, session = found
        with open(STANDARD, "rb") as f:
            settings = leagues.complete(tomllib.load(f)["settings"])
        league_id = db.create_league(
            conn, name="pytest trading", league_type="session", visibility="official",
            start_date=session.start, end_date=session.end, ruleset_version="pytest", ruleset=ruleset,
            preset=None, settings=settings, created_by="pytest", creator_role="gamemaker")
        code = auth.new_invite_code()
        db.create_invite(conn, code, "player", 2, None, "test", "pytest")
    yield {"league_id": league_id, "code": code}
    with db.connect() as conn:
        conn.execute("DELETE FROM leagues WHERE league_id = %s", (league_id,))
        conn.execute("DELETE FROM accounts WHERE invite_code = %s", (code,))
        conn.execute("DELETE FROM invites WHERE code = %s", (code,))
        conn.commit()


def _player(league, name):
    c = TestClient(app)
    c.__enter__()
    assert c.post("/api/signup", json={"invite_code": league["code"], "username": name, "password": PASSWORD}).status_code == 200
    return c


def test_a_player_buys_and_drops_from_the_site(league):
    lid = league["league_id"]
    c = _player(league, "pytest-trader")
    try:
        assert "join pytest trading first" in c.post(f"/api/leagues/{lid}/buy", json={"bioguide_id": "X"}).json()["detail"]
        assert c.post(f"/api/leagues/{lid}/join", json={}).status_code == 200
        market = c.get(f"/api/leagues/{lid}/market").json()
        assert market["mine"]["held"] == [] and market["mine"]["available"] == market["mine"]["budget"]
        cheap = min(market["critters"], key=lambda x: x["cost_now"])
        r = c.post(f"/api/leagues/{lid}/buy", json={"bioguide_id": cheap["bioguide_id"].lower()})
        assert r.status_code == 200, r.text
        assert r.json()["available"] == pytest.approx(market["mine"]["budget"] - cheap["cost_now"])
        again = c.post(f"/api/leagues/{lid}/buy", json={"bioguide_id": cheap["bioguide_id"]}).json()
        assert "already on the roster" in again["detail"]
        roster_id = c.get(f"/api/leagues/{lid}/market").json()["mine"]["roster_id"]
        held = c.get(f"/api/leagues/{lid}/rosters/{roster_id}").json()
        assert held["mine"] and held["years"][-1]["critters"][0]["drop_returns"] is not None
        dropped = c.post(f"/api/leagues/{lid}/drop", json={"bioguide_id": cheap["bioguide_id"]})
        assert dropped.status_code == 200, dropped.text
        returned = held["years"][-1]["critters"][0]["drop_returns"]
        assert dropped.json()["available"] == pytest.approx(r.json()["available"] + returned)
        # Someone else sees the roster, but not as theirs.
        assert TestClient(app).get(f"/api/leagues/{lid}/rosters/{roster_id}").json()["mine"] is False
    finally:
        c.__exit__(None, None, None)


def test_two_buys_at_once_cant_both_spend_the_balance(league):
    lid = league["league_id"]
    with db.connect() as conn:
        lg = play.league(conn, lid)
        m = play.market(conn, lg, play.year_on(lg, date.today()))
        weeks = len([w for w in m.cal.weeks if w >= m.cal.next_week(date.today())])
        seated = db.seated_on(conn, max(date.today(), m.session.start))
        prices = sorted((p for p in db.market_prices(conn, m.price_run, m.session.number) if p["bioguide_id"] in seated),
                        key=lambda p: p["session_cost"])[:2]
        cost = max(p["signing_fee"] + p["weekly_fee"] * weeks for p in prices)
        # Room for one of the two, not both.
        settings = lg["settings"] | {"budget_rules": {"annual_budget": int(cost * 1.5)}}
        conn.execute("UPDATE leagues SET settings = %s WHERE league_id = %s", (Jsonb(settings), lid))
        conn.commit()
        roster_id = db.join_league(conn, lid, "pytest-racer", date.today())
    roster = {"roster_id": roster_id, "player": "pytest-racer", "joined_on": date.today()}
    results, start = [], threading.Barrier(2)

    def buy(bioguide):
        with db.connect() as conn:
            lg = play.league(conn, lid)
            m = play.market(conn, lg, play.year_on(lg, date.today()))
            start.wait()
            try:
                play.buy(conn, lg, roster, m, bioguide, date.today())
                results.append("bought")
            except play.Problem as e:
                results.append(str(e))

    threads = [threading.Thread(target=buy, args=(p["bioguide_id"],)) for p in prices]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results)[0] == "bought" and "available" in sorted(results)[1], results
