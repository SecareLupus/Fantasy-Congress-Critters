"""The web API against the local database. Skipped when Postgres isn't running or has no
league to read."""

from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient

from pipeline import auth, db, play
from pipeline.api import _pick, app, throttle


@pytest.fixture(scope="module")
def client():
    try:
        with db.connect() as conn:
            found = conn.execute("SELECT to_regclass('leagues') IS NOT NULL AND EXISTS (SELECT 1 FROM leagues)").fetchone()[0]
    except psycopg.OperationalError:
        pytest.skip("Postgres isn't running")
    if not found:
        pytest.skip("no leagues in the database")
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def league(client):
    return client.get("/api/leagues").json()[0]


def test_standings_match_the_command_line(client, league):
    on = league["end_date"]
    body = client.get(f"/api/leagues/{league['league_id']}", params={"on": on}).json()
    with db.connect() as conn:
        lg = play.league(conn, league["league_id"])
        table = play.standings(conn, lg, play.league_years(conn, lg), date.fromisoformat(on))
    assert [(s["player"], s["total"]) for s in body["standings"]] == [(s.player, s.total) for s in table]


def test_a_roster_adds_up_to_its_standing(client, league):
    on = league["end_date"]
    body = client.get(f"/api/leagues/{league['league_id']}", params={"on": on}).json()
    for s in body["standings"]:
        roster = client.get(f"/api/leagues/{league['league_id']}/rosters/{s['roster_id']}", params={"on": on}).json()
        assert roster["total"] == pytest.approx(s["total"])
        for y in roster["years"]:
            assert sum(c["power"] + c["productivity"] for c in y["critters"]) == pytest.approx(y["power"] + y["productivity"])


def test_the_market_lists_priced_critters_with_what_they_cost_now(client, league):
    body = client.get(f"/api/leagues/{league['league_id']}/market", params={"on": league["start_date"]}).json()
    if body["closed"]:
        pytest.skip(body["closed"])
    assert body["critters"]
    for c in body["critters"]:
        assert c["cost_now"] == pytest.approx(c["signing_fee"] + c["weekly_fee"] * body["weeks_left"])


def test_a_critter_shows_no_points_for_weeks_to_come(client, league):
    market = client.get(f"/api/leagues/{league['league_id']}/market", params={"on": league["start_date"]}).json()
    if not market["critters"]:
        pytest.skip("no priced critters")
    bioguide = market["critters"][0]["bioguide_id"]
    body = client.get(f"/api/critters/{bioguide}", params={"league": league["league_id"], "on": league["start_date"]}).json()
    assert all(w["power"] is None for w in body["weekly"] if w["state"] == "upcoming")
    assert body["power"] + body["productivity"] == pytest.approx(
        sum(w["power"] + w["productivity"] for w in body["weekly"] if w["state"] != "upcoming"))


def test_missing_things_are_404s_with_a_reason(client):
    assert client.get("/api/leagues/999999").json() == {"detail": "no league 999999"}
    assert client.get("/api/critters/NOPE").status_code == 404


def test_pick_defaults_to_the_year_under_way():
    markets = [play.Market(y, 119, s, None, None, None) for y, s in
               zip((2025, 2026), play.scoring.congress_sessions(119))]
    assert _pick(markets, None, date(2024, 6, 1)).year == 2025
    assert _pick(markets, None, date(2026, 3, 1)).year == 2026
    assert _pick(markets, None, date(2030, 1, 1)).year == 2026
    with pytest.raises(play.NotFound):
        _pick(markets, 2027, date(2026, 3, 1))


@pytest.fixture
def invite(client):
    """A one-use invite, and afterward the invite and any account it made are deleted."""
    code = auth.new_invite_code()
    with db.connect() as conn:
        db.create_invite(conn, code, "player", 1, None, "test", "pytest")
    yield code
    with db.connect() as conn:
        conn.execute("DELETE FROM accounts WHERE invite_code IN (SELECT code FROM invites WHERE created_by = 'pytest')")
        conn.execute("DELETE FROM invites WHERE created_by = 'pytest'")
        conn.commit()
    throttle.failures.clear()


def test_an_invite_makes_one_account_that_can_sign_out_and_in(client, invite):
    name = "pytest-" + invite[:4].lower()
    made = client.post("/api/signup", json={"invite_code": invite.lower().replace("-", " "),
                                            "username": name, "password": "a long password"})
    assert made.status_code == 200 and made.json()["username"] == name
    assert client.get("/api/me").json()["username"] == name
    again = client.post("/api/signup", json={"invite_code": invite, "username": name + "x", "password": "a long password"})
    assert "used up" in again.json()["detail"]
    client.post("/api/signout", json={})
    assert client.get("/api/me").json() is None
    assert client.post("/api/signin", json={"username": name, "password": "wrong password"}).status_code == 400
    assert client.post("/api/signin", json={"username": name.upper(), "password": "a long password"}).status_code == 200
    client.post("/api/signout", json={})


def test_a_taken_username_doesnt_spend_the_invite(client, invite):
    other, name = auth.new_invite_code(), "pytest-taken"
    with db.connect() as conn:
        db.create_invite(conn, other, "player", 1, None, "test", "pytest")
        db.create_account(conn, other, name, auth.hash_password("a long password"))
    r = client.post("/api/signup", json={"invite_code": invite, "username": name.upper(), "password": "a long password"})
    assert "taken" in r.json()["detail"]
    with db.connect() as conn:
        assert conn.execute("SELECT uses FROM invites WHERE code = %s", (invite,)).fetchone()[0] == 0


def test_changes_need_json_and_a_session(client):
    assert client.post("/api/signin", content="username=a&password=b",
                       headers={"Content-Type": "application/x-www-form-urlencoded"}).status_code == 415
    assert client.post("/api/leagues/1/join", json={}).status_code == 401
