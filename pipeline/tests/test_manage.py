"""Game masters on the website: making leagues, private join links, changing settings
before a league starts, removing players, and invites. Runs against the local database
and deletes what it makes; skipped without Postgres or the standard preset."""

import psycopg
import pytest
from fastapi.testclient import TestClient

from pipeline import auth, db
from pipeline.api import app

PASSWORD = "a long password"


@pytest.fixture
def players():
    """Signed-in clients: ann and ben are players, gm is a GameMaker."""
    try:
        with db.connect() as conn:
            if "standard" not in db.presets(conn):
                pytest.skip("no standard preset")
            codes = {role: auth.new_invite_code() for role in ("player", "gamemaker")}
            for role, code in codes.items():
                db.create_invite(conn, code, role, 2, None, "test", "pytest")
    except psycopg.OperationalError:
        pytest.skip("Postgres isn't running")
    clients = {}
    for name, role in (("ann", "player"), ("ben", "player"), ("gm", "gamemaker")):
        c = TestClient(app)
        c.__enter__()
        r = c.post("/api/signup", json={"invite_code": codes[role], "username": f"pytest-{name}", "password": PASSWORD})
        assert r.status_code == 200, r.text
        clients[name] = c
    yield clients
    for c in clients.values():
        c.__exit__(None, None, None)
    with db.connect() as conn:
        mine = "SELECT account_id FROM accounts WHERE username LIKE 'pytest-%'"
        conn.execute(f"DELETE FROM leagues WHERE owner_account_id IN ({mine})")
        conn.execute(f"DELETE FROM accounts WHERE account_id IN ({mine})")
        conn.execute("DELETE FROM invites WHERE created_by IN ('pytest', 'pytest-gm')")
        conn.commit()


def _new(client, **fields):
    settings = client.get("/api/league-options").json()["presets"]["standard"]["settings"]
    body = {"name": "pytest league", "league_type": "standard_private", "timing": "session", "congress": 130,
            "session": 1, "preset": "standard", "settings": settings} | fields
    return client.post("/api/leagues", json=body)


def test_anyone_makes_a_private_league_only_gamemakers_make_official_ones(players):
    assert "GameMakers" in _new(players["ann"], league_type="session").json()["detail"]
    assert _new(players["gm"], league_type="session").status_code == 200
    r = _new(players["ann"])
    assert r.status_code == 200
    league = players["ann"].get(f"/api/leagues/{r.json()['league_id']}").json()
    assert league["visibility"] == "private" and league["manageable"] and league["join_code"]
    assert league["start_date"] == "2047-01-03" and league["created_by"] == "pytest-ann"


def test_bad_dates_and_settings_are_refused_with_the_reason(players):
    assert "needs a session" in _new(players["ann"], session=None).json()["detail"]
    settings = players["ann"].get("/api/league-options").json()["presets"]["standard"]["settings"]
    bad = settings | {"roster_rules": {"roster_limit": 8, "chamber_slots": {"house": 6, "senate": 1}}}
    assert "can't fill a roster of 8" in _new(players["ann"], settings=bad).json()["detail"]


def test_a_private_league_is_joined_with_its_link_and_unlisted_otherwise(players):
    ann, ben = players["ann"], players["ben"]
    lid = _new(ann).json()["league_id"]
    code = ann.get(f"/api/leagues/{lid}").json()["join_code"]
    seen = ben.get(f"/api/leagues/{lid}").json()
    assert seen["join_code"] is None and not seen["manageable"]
    assert lid not in [x["league_id"] for x in ben.get("/api/leagues").json()]
    assert "private" in ben.post(f"/api/leagues/{lid}/join", json={}).json()["detail"]
    assert ben.post(f"/api/leagues/{lid}/join", json={"code": code}).status_code == 200
    assert lid in [x["league_id"] for x in ben.get("/api/leagues").json()]
    # A new code shuts the old link.
    new = ann.post(f"/api/leagues/{lid}/join-code", json={}).json()["join_code"]
    assert new != code
    assert "private" in players["gm"].post(f"/api/leagues/{lid}/join", json={"code": code}).json()["detail"]


def test_only_the_game_master_changes_settings_or_removes_players(players):
    ann, ben = players["ann"], players["ben"]
    lid = _new(ann).json()["league_id"]
    league = ann.get(f"/api/leagues/{lid}").json()
    roster_id = ben.post(f"/api/leagues/{lid}/join", json={"code": league["join_code"]}).json()["roster_id"]
    settings = league["settings"] | {"budget_rules": {"annual_budget": 40000}}
    assert "game master" in ben.post(f"/api/leagues/{lid}/settings", json={"settings": settings}).json()["detail"]
    assert "game master" in players["gm"].post(f"/api/leagues/{lid}/settings", json={"settings": settings}).json()["detail"]
    assert ann.post(f"/api/leagues/{lid}/settings", json={"name": "renamed", "settings": settings}).status_code == 200
    after = ann.get(f"/api/leagues/{lid}").json()
    assert after["name"] == "renamed" and after["settings"]["budget_rules"]["annual_budget"] == 40000
    assert "game master" in ben.post(f"/api/leagues/{lid}/rosters/{roster_id}/remove", json={}).json()["detail"]
    assert ann.post(f"/api/leagues/{lid}/rosters/{roster_id}/remove", json={}).status_code == 200
    assert ann.get(f"/api/leagues/{lid}").json()["players"] == 0


def test_a_started_league_is_frozen(players):
    with db.connect() as conn:
        started = conn.execute("SELECT league_id FROM leagues WHERE start_date <= current_date LIMIT 1").fetchone()
    if not started:
        pytest.skip("no league has started")
    r = players["gm"].post(f"/api/leagues/{started[0]}/settings", json={"settings": {}})
    assert r.status_code == 400


def test_only_gamemakers_make_invites(players):
    assert "GameMakers" in players["ann"].post("/api/invites", json={}).json()["detail"]
    codes = players["gm"].post("/api/invites", json={"count": 2, "uses": 3, "note": "pytest"}).json()["codes"]
    listed = {i["code"]: i for i in players["gm"].get("/api/invites").json()}
    assert all(listed[c]["max_uses"] == 3 and listed[c]["created_by"] == "pytest-gm" for c in codes)
