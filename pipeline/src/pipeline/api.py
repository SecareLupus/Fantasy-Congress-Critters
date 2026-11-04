"""The web API behind the site (Design-Pages §13): leagues and their standings, rosters,
the market, critters, and how fresh the data is; accounts (auth.py) and joining a league.
Trading comes next.

Every view takes `on`, the date to show the game as of (default: today), so a past
season can be browsed as it stood; joining always happens today. Run it with
`critters serve`; in production it also serves the built site from web/dist.

Requests that change anything must send JSON. Browsers can't send JSON across sites
without asking first, which, with the SameSite session cookie, keeps other sites from
acting for a signed-in player.
"""

import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from . import auth, db, leagues, ledger, play, scoring
from .build import DEFAULT_RULESET
from .config import DATABASE_URL, REPO_ROOT

SITE = REPO_ROOT / "web" / "dist"
COOKIE = "critters_session"
# Set CRITTERS_SECURE_COOKIE=1 when the site is served over HTTPS.
SECURE_COOKIE = os.environ.get("CRITTERS_SECURE_COOKIE") == "1"
throttle = auth.Throttle()


@asynccontextmanager
async def lifespan(app: FastAPI):
    with ConnectionPool(DATABASE_URL, min_size=1, max_size=10) as pool:
        with pool.connection() as conn:
            db.init_schema(conn)
        app.state.pool = pool
        yield


app = FastAPI(title="Fantasy Congress Critters", lifespan=lifespan)


def connection(request: Request):
    with request.app.state.pool.connection() as conn:
        yield conn


@app.exception_handler(play.Problem)
def problem(request: Request, e: play.Problem) -> JSONResponse:
    code = 404 if isinstance(e, play.NotFound) else 401 if isinstance(e, auth.NotSignedIn) else 400
    return JSONResponse({"detail": str(e)}, status_code=code)


def json_only(request: Request) -> None:
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise HTTPException(415, "send JSON")


def signed_in(request: Request, conn=Depends(connection)) -> dict | None:
    token = request.cookies.get(COOKIE)
    return db.session_account(conn, auth.token_hash(token)) if token else None


def account(me: dict | None = Depends(signed_in)) -> dict:
    if me is None:
        raise auth.NotSignedIn("sign in first")
    return me


def _start_session(conn, response: Response, account_id: int) -> None:
    token = auth.new_token()
    db.create_session(conn, auth.token_hash(token), account_id, auth.SESSION_DAYS)
    response.set_cookie(COOKIE, token, max_age=auth.SESSION_DAYS * 86400, httponly=True, samesite="lax",
                        secure=SECURE_COOKIE, path="/")


def _me(conn, me: dict) -> dict:
    return {"account_id": me["account_id"], "username": me["username"], "role": me["role"],
            "rosters": db.account_rosters(conn, me["account_id"])}


class SignUp(BaseModel):
    invite_code: str
    username: str
    password: str


class SignIn(BaseModel):
    username: str
    password: str


@app.post("/api/signup", dependencies=[Depends(json_only)])
def signup(body: SignUp, request: Request, response: Response, conn=Depends(connection)) -> dict:
    username = body.username.strip()
    auth.check_new_account(username, body.password)
    address = f"ip:{request.client.host if request.client else '?'}"
    throttle.check(address)
    try:
        made = db.create_account(conn, auth.normalize_code(body.invite_code), username,
                                 auth.hash_password(body.password))
    except psycopg.errors.UniqueViolation:
        raise play.Problem(f"the username {username} is taken")
    if made is None:
        throttle.fail(address)
        raise play.Problem("that invite code isn't valid, or has been used up or expired")
    _start_session(conn, response, made["account_id"])
    return _me(conn, made)


@app.post("/api/signin", dependencies=[Depends(json_only)])
def signin(body: SignIn, request: Request, response: Response, conn=Depends(connection)) -> dict:
    name_key, address = f"user:{body.username.strip().lower()}", f"ip:{request.client.host if request.client else '?'}"
    throttle.check(name_key, address)
    found = db.account_by_name(conn, body.username.strip())
    ok = auth.check_password(body.password, found["password_hash"] if found else auth.DUMMY_HASH)
    if not found or not ok or found["disabled"]:
        throttle.fail(name_key, address)
        raise play.Problem("wrong username or password")
    throttle.clear(name_key)
    _start_session(conn, response, found["account_id"])
    return _me(conn, found)


@app.post("/api/signout", dependencies=[Depends(json_only)])
def signout(request: Request, response: Response, conn=Depends(connection)) -> dict:
    token = request.cookies.get(COOKIE)
    if token:
        db.delete_session(conn, auth.token_hash(token))
    response.delete_cookie(COOKIE, path="/")
    return {}


@app.get("/api/me")
def whoami(conn=Depends(connection), me: dict | None = Depends(signed_in)) -> dict | None:
    return _me(conn, me) if me else None


@app.post("/api/leagues/{league_id}/join", dependencies=[Depends(json_only)])
def join(league_id: int, conn=Depends(connection), me: dict = Depends(account)) -> dict:
    league = play.league(conn, league_id)
    if not _open_to_join(league):
        raise play.Problem("only official leagues that haven't ended can be joined from the site for now")
    roster_id = play.join(conn, league, me["username"], _today(), me["account_id"])
    return {"roster_id": roster_id}


def _open_to_join(league: dict) -> bool:
    """Private leagues will take invitations from their game master; until then only
    official leagues can be joined from the site."""
    return league["visibility"] == "official" and _today() < league["end_date"]


def _today() -> date:
    return date.today()


def _summary(league: dict, players: int) -> dict:
    return {k: league[k] for k in ("league_id", "name", "league_type", "visibility", "start_date", "end_date")} \
        | {"players": players}


def _year(m: play.Market, final: set[int], on: date) -> dict:
    ended = m.cal.settled(on)
    return {"year": m.year, "congress": m.congress, "session": m.session.number,
            "first_week": m.cal.weeks[0], "last_week": m.cal.weeks[-1], "weeks": len(m.cal.weeks),
            "ended": len(ended), "final": len(final & set(ended)), "next_week": m.cal.next_week(on),
            "run_id": m.run_id, "price_run": m.price_run}


def _pick(markets: list[play.Market], year: int | None, on: date) -> play.Market:
    """The year asked for, else the one under way on `on` (the first before the league, the
    last after it)."""
    if not markets:
        raise play.Problem("the league has no weeks")
    if year is not None:
        found = [m for m in markets if m.year == year]
        if not found:
            raise play.NotFound(f"the league has no weeks in {year}")
        return found[0]
    return next((m for m in markets if on < m.session.end), markets[-1])


def _weeks(m: play.Market, weekly: dict, bioguide: str, final: set[int], on: date) -> list[dict]:
    out = []
    for w in m.cal.weeks:
        state = "final" if w in final else "ended" if m.cal.end(w) <= on else "upcoming"
        # A live run scores weeks still to come at today's seats and attendance; don't show them.
        power, productivity = weekly.get((bioguide, w), (0.0, 0.0)) if state != "upcoming" else (None, None)
        out.append({"week": w, "start": m.cal.start(w), "end": m.cal.end(w) - timedelta(days=1),
                    "power": power, "productivity": productivity, "state": state})
    return out


@app.get("/api/status")
def status(conn=Depends(connection)) -> dict:
    sources = [dict(zip(("source", "congress", "attempted_at", "ok", "note", "succeeded_at", "latest"), row))
               for row in db.sync_status(conn)]
    return {"sources": sources,
            "updated_at": max((s["succeeded_at"] for s in sources if s["succeeded_at"]), default=None)}


@app.get("/api/leagues")
def league_list(conn=Depends(connection)) -> list[dict]:
    return [_summary(league, len(db.rosters(conn, league["league_id"]))) for league in db.leagues(conn)]


@app.get("/api/leagues/{league_id}")
def league_detail(league_id: int, on: date | None = None, conn=Depends(connection)) -> dict:
    on = on or _today()
    league = play.league(conn, league_id)
    markets = play.league_years(conn, league)
    table = play.standings(conn, league, markets, on)
    return _summary(league, len(table)) | {
        "as_of": on,
        "ruleset_version": league["ruleset_version"], "preset": league["preset"],
        "created_by": league["created_by"], "creator_role": league["creator_role"],
        "frozen": not leagues.can_change(league["start_date"], on),
        "open_to_join": _open_to_join(league),
        "settings": league["settings"],
        "years": [_year(m, play.final_weeks(conn, league, m), on) for m in markets],
        "standings": [{"rank": i, "roster_id": s.roster_id, "player": s.player, "total": s.total,
                       "power": s.power, "productivity": s.productivity, "penalties": s.penalties}
                      for i, s in enumerate(table, 1)],
    }


@app.get("/api/leagues/{league_id}/rosters/{roster_id}")
def roster_detail(league_id: int, roster_id: int, on: date | None = None, conn=Depends(connection)) -> dict:
    on = on or _today()
    league = play.league(conn, league_id)
    roster = next((r for r in db.rosters(conn, league_id) if r["roster_id"] == roster_id), None)
    if roster is None:
        raise play.NotFound(f"no roster {roster_id} in league {league_id}")
    markets = play.league_years(conn, league)
    scored = play.roster_points(conn, league, roster, markets, on)
    annual = league["settings"]["budget_rules"]["annual_budget"]
    years = []
    for m in markets:
        s = scored[m.year]
        held = [h for h, _ in s["holdings"]]
        b = ledger.budget(held, m.cal, annual, on)
        cards = db.critter_cards(conn, [h.bioguide_id for h in held], max(on, m.session.start))
        critters = []
        for h, (power, productivity) in s["holdings"]:
            state = play.status(h, on)
            if state is None:
                continue
            critters.append(cards[h.bioguide_id] | {
                "status": state, "made_on": h.made_on, "first_week": h.first_week, "last_week": h.last_week,
                "session_cost": h.session_cost, "signing_fee": h.signing_fee, "weekly_fee": h.weekly_fee,
                "dropped_on": h.dropped_on if h.dropped(on) else None, "drop_week": h.drop_week if h.dropped(on) else None,
                "left_office": h.left_office, "power": power, "productivity": productivity})
        years.append(_year(m, play.final_weeks(conn, league, m), on) | {
            "budget": {"budget": b.budget, "spent": b.spent, "reserved": b.reserved, "available": b.available},
            "power": s["power"], "productivity": s["productivity"], "penalties": s["penalties"],
            "total": s["power"] + s["productivity"] - s["penalties"], "critters": critters})
    return {"roster_id": roster_id, "player": roster["player"], "joined_on": roster["joined_on"], "as_of": on,
            "league": _summary(league, len(db.rosters(conn, league_id))) | {"settings": league["settings"]},
            "total": sum(y["total"] for y in years), "years": years}


@app.get("/api/leagues/{league_id}/market")
def market(league_id: int, year: int | None = None, on: date | None = None, conn=Depends(connection)) -> dict:
    on = on or _today()
    league = play.league(conn, league_id)
    markets = play.league_years(conn, league)
    m = _pick(markets, year, on)
    out = {"league": _summary(league, len(db.rosters(conn, league_id))) | {"settings": league["settings"]},
           "as_of": on, "years": [x.year for x in markets],
           **_year(m, play.final_weeks(conn, league, m), on), "closed": None, "critters": []}
    try:
        play.tradable(league, m)
    except play.Problem as e:
        out["closed"] = str(e)
        return out
    first = m.cal.next_week(on)
    if first is None:
        out["closed"] = f"no league weeks are left in {m.year}"
    weeks_left = len([w for w in m.cal.weeks if first and w >= first])
    day = max(on, m.session.start)
    seated = db.seated_on(conn, day)
    prices = [p for p in db.market_prices(conn, m.price_run, m.session.number) if p["bioguide_id"] in seated]
    bioguides = [p["bioguide_id"] for p in prices]
    cards = db.critter_cards(conn, bioguides, day)
    weekly = play.weekly_points(conn, league["ruleset"], m, bioguides)
    ended = set(m.cal.settled(on))
    points: dict[str, float] = {}
    for (b, w), (p, q) in weekly.items():
        if w in ended:
            points[b] = points.get(b, 0.0) + p + q
    owners = db.owners(conn, league_id, m.congress, m.session.number, on)
    out["weeks_left"] = weeks_left
    out["critters"] = [cards[p["bioguide_id"]] | p | {
        "cost_now": p["signing_fee"] + p["weekly_fee"] * weeks_left,
        "points": points.get(p["bioguide_id"], 0.0), "owners": owners.get(p["bioguide_id"], [])} for p in prices]
    return out


@app.get("/api/critters/{bioguide}")
def critter_detail(bioguide: str, league: int | None = None, year: int | None = None, on: date | None = None,
                   conn=Depends(connection)) -> dict:
    """A critter, and where their points came from in one legislative year: scored with a
    league's ruleset, or the default one."""
    on = on or _today()
    profile = db.critter(conn, bioguide.upper())
    if profile is None:
        raise play.NotFound(f"no critter {bioguide}")
    bioguide = profile["bioguide_id"]
    if league is not None:
        lg = play.league(conn, league)
        m = _pick(play.league_years(conn, lg), year, on)
        ruleset = lg["ruleset"]
        context = _summary(lg, len(db.rosters(conn, league))) | {"settings": lg["settings"]}
    else:
        ruleset = scoring.Ruleset.load(DEFAULT_RULESET).raw
        m = play.season(conn, ruleset, year or play.legislative_year(on))
        context = None
    final = db.settled_weeks(conn, ruleset, m.congress, m.session.number)
    weekly = play.weekly_points(conn, ruleset, m, [bioguide])
    weeks = _weeks(m, weekly, bioguide, final, on)
    counted = [w for w in weeks if w["state"] != "upcoming"]
    before = m.cal.end(counted[-1]["week"]) if counted else m.session.start
    day = min(max(on, m.session.start), m.session.end - timedelta(days=1))
    price = None
    if m.price_run:
        price = next((p for p in db.market_prices(conn, m.price_run, m.session.number)
                      if p["bioguide_id"] == bioguide), None)
    return profile | {
        "as_of": on, "league": context, "card": db.critter_cards(conn, [bioguide], day).get(bioguide),
        **_year(m, final, on),
        "power": sum(w["power"] for w in counted), "productivity": sum(w["productivity"] for w in counted),
        "weekly": weeks, "counted_through": before - timedelta(days=1),
        "breakdown": db.critter_points(conn, m.run_id, m.session.number, bioguide, before) if m.run_id else None,
        "price": price,
        "owners": db.owners(conn, league, m.congress, m.session.number, on).get(bioguide, []) if league else [],
    }


if SITE.exists():
    app.mount("/assets", StaticFiles(directory=SITE / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def site(path: str) -> FileResponse:
        """The built site; any path that isn't a file is a page the site routes itself."""
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (SITE / path).resolve()
        if path and file.is_file() and file.is_relative_to(SITE):
            return FileResponse(file)
        return FileResponse(SITE / "index.html")
