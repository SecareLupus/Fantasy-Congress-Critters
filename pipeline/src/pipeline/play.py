"""Playing a league: its legislative years, purchases, drops, rosters and standings.

Shared by the command line and the web API. The rules themselves are in ledger.py; this
module reads and writes the database around them. Anything a player or game master did
wrong raises Problem, whose message is meant for them.
"""

from dataclasses import dataclass
from datetime import date

from . import db, ledger, scoring
from .ledger import Holding


class Problem(Exception):
    pass


class NotFound(Problem):
    pass


def legislative_year(day: date) -> int:
    return day.year if day >= date(day.year, 1, 3) else day.year - 1


def league(conn, league_id: int) -> dict:
    found = db.leagues(conn, league_id)
    if not found:
        raise NotFound(f"no league {league_id}")
    return found[0]


def roster(conn, league: dict, player: str) -> dict:
    found = db.rosters(conn, league["league_id"], player)
    if not found:
        raise NotFound(f"{player} has no roster in league {league['league_id']}: critters league join")
    return found[0]


@dataclass
class Market:
    """One legislative year of a league: its weeks, the run it scores from (the latest),
    and the run it prices from."""
    year: int
    congress: int
    session: scoring.Session
    cal: ledger.Calendar
    run_id: int | None
    price_run: int | None


def season(conn, ruleset: dict, year: int, start: date | None = None, end: date | None = None) -> Market:
    """A legislative year scored and priced with `ruleset`, counting the weeks that start
    in [start, end) (default: all of them)."""
    congress, index = divmod(year - 1787, 2)
    session = scoring.congress_sessions(congress)[index]
    cal = ledger.Calendar.build(session, ruleset["settlement"]["weeks"],
                                start or session.start, end or session.end)
    return Market(year, congress, session, cal, db.league_run(conn, ruleset, congress),
                  db.price_run(conn, ruleset, congress, session.number))


def market(conn, league: dict, year: int) -> Market:
    return season(conn, league["ruleset"], year, league["start_date"], league["end_date"])


def league_years(conn, league: dict) -> list[Market]:
    years = range(legislative_year(league["start_date"]), legislative_year(league["end_date"]) + 1)
    return [m for m in (market(conn, league, y) for y in years) if m.cal.weeks]


def year_on(league: dict, day: date) -> int:
    """The legislative year a transaction on `day` trades in: the one under way, or the
    league's first before it starts."""
    return legislative_year(max(day, league["start_date"]))


def tradable(league: dict, m: Market) -> None:
    """Refuse trading in a year the league has no weeks, scores or prices for."""
    lid = league["league_id"]
    if not m.cal.weeks:
        raise Problem(f"league {lid} has no weeks in {m.year}")
    if m.run_id is None:
        raise Problem(f"no scoring run of the {m.congress}th Congress uses league {lid}'s ruleset: "
                      f"critters score --congress {m.congress} --league {lid}")
    if m.price_run is None:
        raise Problem(f"no prices for {m.year} from a run with league {lid}'s ruleset: "
                      f"critters price --run {m.run_id} --session {m.session.number}")


def check_date(conn, roster: dict, day: date) -> None:
    floor = max(roster["joined_on"], db.last_transaction(conn, roster["roster_id"]) or roster["joined_on"])
    if day < floor:
        raise Problem(f"{roster['player']} joined or last traded on {floor}; a transaction can't be dated earlier")


def one_critter(conn, text: str, among: list[str] | None = None) -> tuple[str, str]:
    found = db.find_critters(conn, text, among)
    if len(found) != 1:
        raise Problem(f"{text!r} matches {len(found)} critters" +
                      (": " + ", ".join(f"{b} {n}" for b, n in found[:8]) if found else ""))
    return found[0]


def join(conn, league: dict, player: str, day: date, account_id: int | None = None) -> int:
    if day >= league["end_date"]:
        raise Problem(f"league {league['league_id']} ended on {league['end_date']}")
    if any(r["player"].lower() == player.lower() or (account_id and r["account_id"] == account_id)
           for r in db.rosters(conn, league["league_id"])):
        raise Problem(f"{player} already has a roster in league {league['league_id']}")
    return db.join_league(conn, league["league_id"], player, day, account_id)


def buy(conn, league: dict, roster: dict, m: Market, bioguide: str, day: date) -> Holding:
    """Buy one critter on `day` in the year `m`, or Problem with the reason."""
    check_date(conn, roster, day)
    tradable(league, m)
    name = db.names(conn, [bioguide]).get(bioguide, bioguide)
    price = db.critter_price(conn, m.price_run, m.session.number, bioguide)
    if price is None:
        raise Problem(f"{name} has no price for {m.year}")
    end = db.service_end(conn, bioguide, max(day, m.session.start))
    if end is None:
        raise Problem(f"{name} is not in office on {max(day, m.session.start)}")
    # Hold the roster until the purchase commits, so two at once can't both spend the balance.
    db.lock_roster(conn, roster["roster_id"])
    held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
    try:
        h = ledger.purchase(held, m.cal, league["settings"], day, bioguide_id=bioguide, **price,
                            left_office=end if end < m.session.end else None)
    except ledger.Refused as e:
        conn.rollback()
        raise Problem(f"can't buy {name}: {e}")
    h.txn_id = db.record_purchase(conn, roster["roster_id"], m.congress, m.session.number, m.price_run, h)
    return h


def drop(conn, league: dict, roster: dict, m: Market, bioguide: str, day: date) -> Holding:
    """Drop one critter on `day` in the year `m`, or Problem with the reason."""
    check_date(conn, roster, day)
    name = db.names(conn, [bioguide]).get(bioguide, bioguide)
    db.lock_roster(conn, roster["roster_id"])
    held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
    try:
        h = ledger.drop(held, m.cal, league["settings"], day, bioguide)
    except ledger.Refused as e:
        conn.rollback()
        raise Problem(f"can't drop {name}: {e}")
    db.record_drop(conn, roster["roster_id"], m.congress, m.session.number, h)
    return h


def budget(conn, league: dict, roster: dict, m: Market, as_of: date) -> ledger.Budget:
    return ledger.budget(db.holdings(conn, roster["roster_id"], m.congress, m.session), m.cal,
                         league["settings"]["budget_rules"]["annual_budget"], as_of)


def final_weeks(conn, league: dict, m: Market) -> set[int]:
    return db.settled_weeks(conn, league["ruleset"], m.congress, m.session.number)


def weekly_points(conn, ruleset: dict, m: Market, bioguides: list[str]) -> dict[tuple[str, int], tuple[float, float]]:
    """(bioguide, week) -> (power, productivity): settled weeks as settled, later weeks from
    the latest run."""
    final = db.settled_weeks(conn, ruleset, m.congress, m.session.number)
    weekly = {k: v for k, v in (db.roster_weekly_points(conn, m.run_id, m.session.number, bioguides)
                                if m.run_id else {}).items() if k[1] not in final}
    weekly.update(db.settled_points(conn, ruleset, m.congress, m.session.number, bioguides))
    return weekly


def roster_points(conn, league: dict, roster: dict, markets: list[Market], as_of: date) -> dict:
    """Points and holdings of a roster in each legislative year, as of `as_of`."""
    out = {}
    for m in markets:
        held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
        weekly = weekly_points(conn, league["ruleset"], m, [h.bioguide_id for h in held])
        by = [(h, ledger.points(h, m.cal, weekly, as_of)) for h in held]
        out[m.year] = {"holdings": by, "penalties": ledger.penalties(held, as_of),
                       "power": sum(p for _, (p, _) in by), "productivity": sum(q for _, (_, q) in by)}
    return out


def status(h: Holding, as_of: date) -> str | None:
    """held, dropped or left_office; None for a purchase made after `as_of`."""
    if h.dropped(as_of):
        return "dropped"
    if h.departed(as_of):
        return "left_office"
    return None if h.made_on > as_of else "held"


@dataclass
class Standing:
    roster_id: int
    player: str
    power: float
    productivity: float
    penalties: float

    @property
    def total(self) -> float:
        return self.power + self.productivity - self.penalties


def standings(conn, league: dict, markets: list[Market], as_of: date) -> list[Standing]:
    """Rosters ranked by total points (cumulative; head-to-head isn't built yet)."""
    table = []
    for r in db.rosters(conn, league["league_id"]):
        scored = roster_points(conn, league, r, markets, as_of).values()
        table.append(Standing(r["roster_id"], r["player"], sum(s["power"] for s in scored),
                              sum(s["productivity"] for s in scored), sum(s["penalties"] for s in scored)))
    return sorted(table, key=lambda s: (-s.total, -s.power, -s.productivity, -s.penalties, s.player))
