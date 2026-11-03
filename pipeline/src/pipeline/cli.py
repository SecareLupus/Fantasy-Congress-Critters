import argparse
import json
import time
import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import correlation, quantiles

from pathlib import Path

from . import db, download, fec, leagues, ledger, legislators, pricing, rosters, scoring
from .billstatus import iter_zip
from .config import BILL_TYPES
from .normalize import normalize_bill
from .votes import iter_house_votes, parse_voteview_senate


def cmd_download(args) -> None:
    download.download_billstatus(args.congress, force=args.force)
    download.download_legislators(force=args.force)
    download.download_roster_history(args.congress, force=args.force)
    download.download_house_votes(args.congress, force=args.force)
    download.download_senate_votes(args.congress, force=args.force)
    download.download_fec_summary(download.pricing_cycle(args.congress, 2), force=args.force)


# Committee code prefix -> the term types whose dates bound a seat on it.
ROSTER_TERM_TYPES = {"h": ("rep",), "s": ("sen",), "j": ("rep", "sen")}


def load_rosters(conn, congress: int) -> None:
    start, end = download.congress_dates(congress)
    snapshots = rosters.load_snapshots(download.roster_history_dir(congress))
    terms = db.chamber_terms(conn)
    built = rosters.build_memberships(snapshots, start, end)
    rosters.backfill_starts(built, rosters.SEATED_BEFORE_LISTED.get(congress, {}))
    memberships = []
    for m in built:
        seat_terms = sorted(t for tt in ROSTER_TERM_TYPES[m.seat.committee_code[0]]
                            for t in terms.get((m.seat.bioguide_id, tt), []))
        memberships.extend(rosters.clip_to_terms(m, seat_terms))
    db.save_memberships(conn, congress, memberships)
    conn.commit()
    print(f"committee memberships {congress}: {len(memberships)} from {len(snapshots)} snapshots")


DEFAULT_RULESET = Path(__file__).resolve().parents[2] / "rulesets" / "default.toml"


def _merge(periods: list[tuple]) -> list[tuple]:
    merged: list[list] = []
    for start, end in sorted(periods):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(p) for p in merged]


def score_congress(conn, congress: int, ruleset: scoring.Ruleset) -> tuple[int, list]:
    start, end = download.congress_dates(congress)
    sessions = scoring.congress_sessions(congress)
    bills, votes, positions, leadership = db.scoring_inputs(conn, congress)

    # Leadership entries overlap or repeat in the source; merge per holder and title.
    held: dict[tuple, list] = {}
    for bioguide, title, lead_start, lead_end in leadership:
        held.setdefault((bioguide, title), []).append((lead_start, lead_end or end))
    exempt_titles = set(ruleset.raw["participation"]["exempt_titles"])
    exempt: dict[str, list] = {}
    for (bioguide, title), periods in held.items():
        for p_start, p_end in _merge(periods):
            p_start, p_end = max(p_start, start), min(p_end, end)
            if p_start < p_end:
                positions.append(scoring.Position(bioguide, "leadership", title, None, p_start, p_end))
                if title in exempt_titles:
                    exempt.setdefault(bioguide, []).append((p_start, p_end))

    terms = db.chamber_terms(conn)
    for pos in positions:
        pos.chamber = "sen" if any(a <= pos.start <= b for a, b in terms.get((pos.bioguide_id, "sen"), [])) else "rep"

    memberships: dict[tuple, list] = {}
    for pos in positions:
        if pos.kind == "committee":
            memberships.setdefault((pos.bioguide_id, pos.key), []).append((pos.start, pos.end))

    def on_committee(bioguide: str, code: str, day) -> bool:
        parent = code[:4] + scoring.FULL_COMMITTEE_SUFFIX
        return any(a <= day < b for c in (code, parent) for a, b in memberships.get((bioguide, c), []))

    def seated(bioguide: str, day) -> bool:
        return any(a <= day <= b for tt in ("rep", "sen") for a, b in terms.get((bioguide, tt), []))

    items = []
    for bill in bills:
        items.extend(scoring.score_bill(bill, ruleset, sessions, on_committee))
    scoring.apply_caps(items, ruleset)
    items.extend(scoring.score_votes(votes, ruleset, sessions, seated))

    def chamber_of(bioguide: str, day) -> str:
        return "sen" if any(a <= day <= b for a, b in terms.get((bioguide, "sen"), [])) else "rep"

    scoring.apply_chamber_factor(items, ruleset, chamber_of)
    weeks = ruleset.raw["settlement"]["weeks"]
    participation = scoring.floor_participation(votes, exempt, sessions, weeks)
    items.extend(scoring.score_positions(positions, ruleset, sessions, participation))
    weekly = scoring.weekly_points(items, sessions, participation, weeks)
    return db.save_score_run(conn, congress, ruleset, items, weekly), items


def cmd_score(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        if args.league:
            league = _league(conn, args.league)
            ruleset = scoring.Ruleset(league["ruleset_version"], league["ruleset"])
        else:
            ruleset = scoring.Ruleset.load(args.ruleset)
        start = time.time()
        run_id, items = score_congress(conn, args.congress, ruleset)
        print(f"run {run_id}: ruleset {ruleset.version}, {len(items)} items ({time.time() - start:.1f}s)")


def cmd_report(args) -> None:
    with db.connect() as conn:
        run_id = args.run or conn.execute("SELECT max(run_id) FROM score_runs").fetchone()[0]
        scale = conn.execute("SELECT ruleset->'productivity'->>'scale' FROM score_runs WHERE run_id = %s",
                             (run_id,)).fetchone()[0]
        report = db.score_report(conn, run_id)
    print(f"run {run_id}, members seated for a whole session")
    print(f"{'session':>7} {'chamber':>7} {'n':>4} {'med power':>10} {'med prod':>9} {'max power':>10} {'max prod':>9}")
    for session, chamber, n, med_pow, med_prod, max_pow, max_prod in report["balance"]:
        print(f"{session:>7} {chamber:>7} {n:>4} {med_pow:>10.1f} {med_prod:>9.1f} {max_pow:>10.1f} {max_prod:>9.1f}")
    print(f"productivity scale for an even median member: {float(scale) * report['even_scale']:.4f}"
          f" (this run: {scale})")
    medians = {row[0]: row[1:] for row in report["chamber_medians"]}
    if "rep" in medians and "sen" in medians:
        _, _, house_power, house_prod = medians["rep"]
        power_factor, prod_factor, sen_power, sen_prod = medians["sen"]
        print(f"sen power factor to match the median House member: {power_factor * house_power / sen_power:.3f}"
              f" (this run: {power_factor})")
        print(f"sen productivity factor to match the median House member: {prod_factor * house_prod / sen_prod:.3f}"
              f" (this run: {prod_factor})")
    print("\ncomposition")
    for pillar, category, points, pct in report["composition"]:
        print(f"  {pillar:<13} {category:<26} {points:>10.0f} {pct:>5.1f}%")
    print("\ntop 10 per session (power + productivity)")
    for session, name, chamber, power, productivity in report["top"]:
        print(f"  {session} {name:<28} {chamber} {power:>7.0f} {productivity:>7.0f}")


def cmd_price(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        run_id = args.run or conn.execute("SELECT max(run_id) FROM score_runs").fetchone()[0]
        congress = conn.execute("SELECT congress FROM score_runs WHERE run_id = %s", (run_id,)).fetchone()[0]
        league = None
        if args.league:
            found = db.leagues(conn, args.league)
            if not found:
                raise SystemExit(f"no league {args.league}")
            league = found[0]
            ruleset = scoring.Ruleset(league["ruleset_version"], league["ruleset"])
        else:
            ruleset = scoring.Ruleset.load(args.ruleset)
        cfg = ruleset.raw["pricing"]
        cycle = args.fec_cycle or download.pricing_cycle(congress, args.session)
        path = download.fec_summary_path(cycle)
        if not path.exists():
            raise SystemExit(f"missing {path}: run critters download (or pass --fec-cycle)")
        receipts = fec.receipts(path)
        prev_run = args.prev_run
        if args.session == 1 and prev_run is None:
            prev_run = conn.execute("SELECT max(run_id) FROM score_runs WHERE congress = %s",
                                    (congress - 1,)).fetchone()[0]
            if prev_run is None:
                raise SystemExit(f"pricing session 1 needs a scoring run of the {congress - 1}th Congress")
        rows = db.pricing_inputs(conn, run_id, args.session, cfg["min_days_served"], prev_run, args.as_of)
        unposted = args.session == 1 and not any(r["committee_value"] for r in rows)
        if unposted:
            # A new Congress before its committee rosters are posted: project the seats.
            first_day = date(download.session_year(congress, 1), 1, 3)
            last_day = first_day - timedelta(days=1)
            old, new = db.majority_sides(conn, last_day), db.majority_sides(conn, first_day)
            flipped = {chamber for chamber in new if old.get(chamber) != new[chamber]}
            held = [pricing.HeldSeat(*h) for h in db.held_seats(conn, prev_run, 2, last_day)]
            projected = pricing.carried_seats(
                held, flipped, db.freshmen(conn, download.congress_dates(congress - 1)[0], first_day),
                ruleset.raw["positions"], {r["bioguide_id"]: r["chamber"] for r in rows},
                db.seated_on(conn, last_day))
            keep = 1 - cfg["unposted_seat_discount"]
            for r in rows:
                r["seat_value"] += projected[r["bioguide_id"]] * keep - r["committee_value"]
        members = []
        for r in rows:
            found = [receipts[i] for i in r["fec_ids"] if i in receipts]
            members.append(pricing.Member(r["bioguide_id"], r["chamber"], r["seat_value"], r["participation"],
                                          r["productivity_rate"], sum(found) if found else None,
                                          r["up_for_election"]))
        prices = pricing.price_session(members, cfg)
        db.save_prices(conn, run_id, args.session, cycle, prices)
        actual = db.session_points(conn, run_id, args.session)
        names = dict(conn.execute("SELECT bioguide_id, official_full_name FROM critters").fetchall())

    start = args.as_of or date(download.session_year(congress, args.session), 1, 3)
    end = date(download.session_year(congress, args.session) + 1, 1, 3)
    left = {r["bioguide_id"]: r["left_office"] for r in rows}
    costs = sorted(p.session_cost for p in prices)
    q1, q2, q3 = quantiles(costs, n=4)
    print(f"run {run_id}: {congress}th Congress session {args.session} ({start.year}), "
          f"ruleset {ruleset.version}, FEC cycle {cycle}")
    if unposted:
        print(f"committee rosters not posted yet: seats projected from {last_day}"
              f"{', majority changed in ' + ' and '.join(sorted(flipped)) if flipped else ''}"
              f", at {keep:.0%} of their value")
    print(f"{len(prices)} critters seated on {start}: "
          + ", ".join(f"{c} {sum(p.chamber == c for p in prices)}" for c in ("rep", "sen")))
    print(f"Session Cost: min ${costs[0]:,}  25% ${q1:,.0f}  median ${q2:,.0f}  75% ${q3:,.0f}  max ${costs[-1]:,}")
    if league:
        budget = league["settings"]["budget_rules"]["annual_budget"]
        limit = league["settings"]["roster_rules"]["roster_limit"]
        print(f"league {league['league_id']} ({league['name']}): budget ${budget:,} for {limit} critters, "
              f"{budget / limit / q2:.2f} x the median price per slot, {budget / q3:.1f} x the 75th percentile")

    scored = [p for p in prices if actual.get(p.bioguide_id)]
    if scored:
        r = correlation([p.session_cost for p in scored], [actual[p.bioguide_id] for p in scored])
        print(f"\nagainst session {args.session} points: r = {r:.3f} (price), "
              f"{correlation([p.projected_points for p in scored], [actual[p.bioguide_id] for p in scored]):.3f} (projection)")

        def value(p) -> float:
            weeks = min(cfg["weeks"], max(0, (min(left[p.bioguide_id], end) - start).days / 7))
            return actual[p.bioguide_id] / pricing.charged(p, weeks) * 1000

        ranked = sorted(scored, key=value, reverse=True)
        for label, group in (("best value", ranked[:args.top]), ("worst value", ranked[::-1][:args.top])):
            print(f"\n{label} (points per $1,000 charged)")
            for p in group:
                print(f"  {names[p.bioguide_id]:<28} {p.chamber} ${p.session_cost:>6,} "
                      f"{actual[p.bioguide_id]:>6.0f} pts {value(p):>6.1f}")
    print(f"\nmost expensive")
    for p in sorted(prices, key=lambda p: -p.session_cost)[:args.top]:
        print(f"  {names[p.bioguide_id]:<28} {p.chamber} ${p.session_cost:>6,}  projected {p.projected_power:>4.0f} power "
              f"+ {p.projected_productivity:>4.0f} productivity, x{p.multiplier:.2f}")


def _print_league(league: dict) -> None:
    print(f"league {league['league_id']}: {league['name']}")
    print(f"  {league['league_type']} ({league['visibility']}), {league['start_date']} to {league['end_date']}")
    print(f"  ruleset {league['ruleset_version']}, from preset {league['preset'] or '(none)'}")
    print(f"  created by {league['created_by']} ({league['creator_role']}) {league['created_at']:%Y-%m-%d}")
    state = "open to changes until it starts" if leagues.can_change(league["start_date"], date.today()) else "started: frozen"
    print(f"  {state}")
    for s in leagues.SETTINGS:
        print(f"  {s.path:<30} {json.dumps(leagues.get_path(league['settings'], s.path))}")


def _check_or_exit(settings: dict) -> None:
    errors = leagues.validate(settings)
    if errors:
        raise SystemExit("invalid league settings:\n  " + "\n  ".join(errors))


def cmd_preset_save(args) -> None:
    with open(args.file, "rb") as f:
        data = tomllib.load(f)
    settings = leagues.complete(data["settings"])
    _check_or_exit(settings)
    with db.connect() as conn:
        db.init_schema(conn)
        db.save_preset(conn, args.name, data.get("description"), settings, args.by)
    print(f"preset {args.name} saved by {args.by}")


def cmd_preset_list(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        for name, p in db.presets(conn).items():
            print(f"{name}: {p['description'] or ''} (by {p['authored_by']}, {p['updated_at']:%Y-%m-%d})")
            for s in leagues.SETTINGS:
                print(f"  {s.path:<30} {json.dumps(leagues.get_path(p['settings'], s.path))}")


def cmd_league_create(args) -> None:
    official = args.type in leagues.OFFICIAL_TYPES
    role = args.role or ("gamemaker" if official else "commissioner")
    if official and role != "gamemaker":
        raise SystemExit("official leagues are created by GameMakers (--role gamemaker)")
    timing = args.timing if args.type == "standard_private" else args.type
    if timing not in leagues.OFFICIAL_TYPES + ("flexible_private",):
        raise SystemExit("a standard_private league needs --timing, one of: " + ", ".join(leagues.OFFICIAL_TYPES))
    try:
        start, end = leagues.league_dates(timing, congress=args.congress, session=args.session,
                                          year=args.year, start=args.start, end=args.end)
        overrides = leagues.parse_overrides(args.set or [])
    except ValueError as e:
        raise SystemExit(str(e))
    ruleset = scoring.Ruleset.load(args.ruleset)
    with db.connect() as conn:
        db.init_schema(conn)
        preset = db.presets(conn).get(args.preset)
        if preset is None:
            raise SystemExit(f"no preset {args.preset!r}; save one with critters league preset save")
        settings = leagues.resolve(preset["settings"], overrides)
        _check_or_exit(settings)
        league_id = db.create_league(
            conn, name=args.name, league_type=args.type, visibility="official" if official else "private",
            start_date=start, end_date=end, ruleset_version=ruleset.version, ruleset=ruleset.raw,
            preset=args.preset, settings=settings, created_by=args.by, creator_role=role)
        _print_league(db.leagues(conn, league_id)[0])


def cmd_league_update(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        found = db.leagues(conn, args.league)
        if not found:
            raise SystemExit(f"no league {args.league}")
        league = found[0]
        if not leagues.can_change(league["start_date"], date.today()):
            raise SystemExit(f"league {args.league} started on {league['start_date']}: its settings and ruleset are frozen")
        try:
            settings = leagues.resolve(league["settings"], leagues.parse_overrides(args.set or []))
        except ValueError as e:
            raise SystemExit(str(e))
        _check_or_exit(settings)
        ruleset = scoring.Ruleset.load(args.ruleset) if args.ruleset else \
            scoring.Ruleset(league["ruleset_version"], league["ruleset"])
        db.update_league(conn, args.league, settings, ruleset.version, ruleset.raw)
        _print_league(db.leagues(conn, args.league)[0])


def cmd_league_show(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        found = db.leagues(conn, args.league)
        if args.league and not found:
            raise SystemExit(f"no league {args.league}")
        for league in found:
            _print_league(league)


def _league(conn, league_id: int) -> dict:
    found = db.leagues(conn, league_id)
    if not found:
        raise SystemExit(f"no league {league_id}")
    return found[0]


def _roster(conn, league: dict, player: str) -> dict:
    found = db.rosters(conn, league["league_id"], player)
    if not found:
        raise SystemExit(f"{player} has no roster in league {league['league_id']}: critters league join")
    return found[0]


def _legislative_year(day: date) -> int:
    return day.year if day >= date(day.year, 1, 3) else day.year - 1


@dataclass
class _Market:
    """One legislative year of a league: its weeks, and the run it scores and prices from."""
    year: int
    congress: int
    session: scoring.Session
    cal: ledger.Calendar
    run_id: int | None


def _market(conn, league: dict, year: int) -> _Market:
    congress, index = divmod(year - 1787, 2)
    session = scoring.congress_sessions(congress)[index]
    cal = ledger.Calendar.build(session, league["ruleset"]["settlement"]["weeks"],
                                league["start_date"], league["end_date"])
    return _Market(year, congress, session, cal, db.league_run(conn, league["ruleset"], congress))


def _league_years(conn, league: dict) -> list[_Market]:
    years = range(_legislative_year(league["start_date"]), _legislative_year(league["end_date"]) + 1)
    return [m for m in (_market(conn, league, y) for y in years) if m.cal.weeks]


def _check_date(conn, roster: dict, day: date) -> None:
    floor = max(roster["joined_on"], db.last_transaction(conn, roster["roster_id"]) or roster["joined_on"])
    if day < floor:
        raise SystemExit(f"{roster['player']} joined or last traded on {floor}; a transaction can't be dated earlier")


def _one_critter(conn, text: str, among: list[str] | None = None) -> tuple[str, str]:
    found = db.find_critters(conn, text, among)
    if len(found) != 1:
        raise SystemExit(f"{text!r} matches {len(found)} critters" +
                         (": " + ", ".join(f"{b} {n}" for b, n in found[:8]) if found else ""))
    return found[0]


def cmd_league_join(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = _league(conn, args.league)
        if args.on >= league["end_date"]:
            raise SystemExit(f"league {args.league} ended on {league['end_date']}")
        if db.rosters(conn, args.league, args.player):
            raise SystemExit(f"{args.player} already has a roster in league {args.league}")
        db.join_league(conn, args.league, args.player, args.on)
    print(f"{args.player} joined league {args.league} ({league['name']}) on {args.on}")


def cmd_league_buy(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = _league(conn, args.league)
        roster = _roster(conn, league, args.player)
        _check_date(conn, roster, args.on)
        m = _market(conn, league, args.year or _legislative_year(max(args.on, league["start_date"])))
        if not m.cal.weeks:
            raise SystemExit(f"league {args.league} has no weeks in {m.year}")
        if m.run_id is None:
            raise SystemExit(f"no scoring run of the {m.congress}th Congress uses league {args.league}'s ruleset: "
                             f"critters score --congress {m.congress} --league {args.league}")
        settings = league["settings"]
        market = db.priced(conn, m.run_id, m.session.number)
        if not market:
            raise SystemExit(f"no prices for {m.year} in run {m.run_id}: "
                             f"critters price --run {m.run_id} --session {m.session.number}")
        for text in args.critters:
            bioguide, name = _one_critter(conn, text, market)
            price = db.critter_price(conn, m.run_id, m.session.number, bioguide)
            end = db.service_end(conn, bioguide, max(args.on, m.session.start))
            if end is None:
                raise SystemExit(f"{name} is not in office on {max(args.on, m.session.start)}")
            held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
            try:
                h = ledger.purchase(held, m.cal, settings, args.on, bioguide_id=bioguide, **price,
                                    left_office=end if end < m.session.end else None)
            except ledger.Refused as e:
                raise SystemExit(f"can't buy {name}: {e}")
            db.record_purchase(conn, roster["roster_id"], m.congress, m.session.number, m.run_id, h)
            weeks = h.last_week - h.first_week + 1
            print(f"{args.player} bought {name} ({h.chamber}) on {args.on} for {m.year}: ${h.session_cost:,} "
                  f"Session Cost, ${h.signing_fee:,.2f} signing + {weeks} weeks at ${h.weekly_fee:,.2f} "
                  f"from week {h.first_week}")
        b = ledger.budget(db.holdings(conn, roster["roster_id"], m.congress, m.session), m.cal,
                          settings["budget_rules"]["annual_budget"], args.on)
    print(f"available ${b.available:,.2f} of ${b.budget:,}")


def cmd_league_drop(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = _league(conn, args.league)
        roster = _roster(conn, league, args.player)
        _check_date(conn, roster, args.on)
        m = _market(conn, league, args.year or _legislative_year(max(args.on, league["start_date"])))
        settings = league["settings"]
        for text in args.critters:
            held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
            bioguide, name = _one_critter(conn, text, [h.bioguide_id for h in held if h.active(args.on)])
            try:
                h = ledger.drop(held, m.cal, settings, args.on, bioguide)
            except ledger.Refused as e:
                raise SystemExit(f"can't drop {name}: {e}")
            db.record_drop(conn, roster["roster_id"], m.congress, m.session.number, h)
            returned = h.weekly_fee * max(0, h.last_week - h.drop_week + 1)
            print(f"{args.player} dropped {name} on {args.on}: held through week {h.drop_week - 1}, "
                  f"${returned:,.2f} reserved returned"
                  + (f", ${h.extra_fee:,} drop fee" if h.extra_fee else "")
                  + (f", {h.points_penalty:g} points penalty" if h.points_penalty else ""))
        b = ledger.budget(db.holdings(conn, roster["roster_id"], m.congress, m.session), m.cal,
                          settings["budget_rules"]["annual_budget"], args.on)
    print(f"available ${b.available:,.2f} of ${b.budget:,}")


def _roster_points(conn, roster: dict, markets: list[_Market], as_of: date) -> dict:
    """Points and budget of a roster in each legislative year, as of `as_of`."""
    out = {}
    for m in markets:
        held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
        weekly = db.roster_weekly_points(conn, m.run_id, m.session.number, [h.bioguide_id for h in held]) \
            if m.run_id else {}
        by = [(h, ledger.points(h, m.cal, weekly, as_of)) for h in held]
        out[m.year] = {"holdings": by, "penalties": ledger.penalties(held, as_of),
                       "power": sum(p for _, (p, _) in by), "productivity": sum(q for _, (_, q) in by)}
    return out


def cmd_league_roster(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = _league(conn, args.league)
        roster = _roster(conn, league, args.player)
        markets = [m for m in _league_years(conn, league) if args.year in (None, m.year)]
        scored = _roster_points(conn, roster, markets, args.on)
        names = dict(conn.execute("SELECT bioguide_id, official_full_name FROM critters").fetchall())
    annual = league["settings"]["budget_rules"]["annual_budget"]
    print(f"{args.player} in league {league['league_id']} ({league['name']}), as of {args.on}")
    for m in markets:
        s = scored[m.year]
        held = [h for h, _ in s["holdings"]]
        b = ledger.budget(held, m.cal, annual, args.on)
        settled = m.cal.settled(args.on)
        print(f"\n{m.year} (weeks {m.cal.weeks[0]}-{m.cal.weeks[-1]}, {len(settled)} settled; run {m.run_id})")
        print(f"  budget ${b.budget:,}: spent ${b.spent:,.2f}, reserved ${b.reserved:,.2f}, "
              f"available ${b.available:,.2f}")
        for h, (p, q) in s["holdings"]:
            if h.dropped(args.on):
                status = f"dropped {h.dropped_on}, held weeks {h.first_week}-{h.drop_week - 1}"
            elif h.departed(args.on):
                status = f"left office {h.left_office}"
            elif h.made_on > args.on:
                continue
            else:
                status = f"held from week {h.first_week}"
            print(f"  {names.get(h.bioguide_id, h.bioguide_id):<28} {h.chamber} ${h.session_cost:>6,} "
                  f"bought {h.made_on}  {p + q:>7.1f} pts ({p:.0f} power + {q:.0f} productivity)  {status}")
        total = s["power"] + s["productivity"] - s["penalties"]
        print(f"  total {total:.1f} = {s['power']:.1f} power + {s['productivity']:.1f} productivity"
              f" - {s['penalties']:g} penalties")


def cmd_league_standings(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = _league(conn, args.league)
        markets = _league_years(conn, league)
        table = []
        for roster in db.rosters(conn, args.league):
            scored = _roster_points(conn, roster, markets, args.on)
            power = sum(s["power"] for s in scored.values())
            productivity = sum(s["productivity"] for s in scored.values())
            penalties = sum(s["penalties"] for s in scored.values())
            table.append((power + productivity - penalties, power, productivity, penalties, roster["player"]))
    print(f"league {league['league_id']} ({league['name']}), as of {args.on}: "
          + ", ".join(f"{m.year} {len(m.cal.settled(args.on))}/{len(m.cal.weeks)} weeks settled" for m in markets))
    if league["settings"]["win_condition"] != "cumulative":
        print(f"(win condition {league['settings']['win_condition']} isn't built yet; showing cumulative points)")
    for rank, (total, power, productivity, penalties, player) in enumerate(sorted(table, reverse=True), 1):
        print(f"  {rank:>2}. {player:<20} {total:>8.1f}  ({power:.0f} power + {productivity:.0f} productivity"
              + (f" - {penalties:g} penalties" if penalties else "") + ")")


def cmd_load(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        print(f"critters: {legislators.load_critters(conn)}")
        print(f"committees: {legislators.load_committees(conn)}")
        load_rosters(conn, args.congress)
        for bill_type in BILL_TYPES:
            start, count, n_events = time.time(), 0, 0
            for bill in iter_zip(download.billstatus_path(args.congress, bill_type)):
                events = normalize_bill(bill)
                db.save_bill(conn, bill, events)
                count += 1
                n_events += len(events)
            conn.commit()
            print(f"{bill_type}: {count} bills, {n_events} events ({time.time() - start:.1f}s)")
        print(f"committees added from bill activity: {db.add_missing_committees(conn)}")
        for session in (1, 2):
            start, count, n_members = time.time(), 0, 0
            for rc in iter_house_votes(download.house_votes_dir(args.congress, session)):
                db.save_roll_call(conn, rc)
                count += 1
                n_members += len(rc.members)
            conn.commit()
            print(f"house votes {args.congress}-{session}: {count} roll calls, "
                  f"{n_members} positions ({time.time() - start:.1f}s)")
        start = time.time()
        senate = parse_voteview_senate(
            *(download.voteview_path(args.congress, kind) for kind in download.VOTEVIEW_KINDS)
        )
        for rc in senate:
            db.save_roll_call(conn, rc)
        conn.commit()
        print(f"senate votes {args.congress}: {len(senate)} roll calls, "
              f"{sum(len(rc.members) for rc in senate)} positions ({time.time() - start:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="critters")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("download", help="fetch raw source files")
    p.add_argument("--congress", type=int, default=118)
    p.add_argument("--force", action="store_true", help="re-download files already on disk")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("load", help="parse, normalize, and load into Postgres")
    p.add_argument("--congress", type=int, default=118)
    p.set_defaults(func=cmd_load)

    p = sub.add_parser("score", help="score a Congress with a ruleset")
    p.add_argument("--congress", type=int, default=118)
    p.add_argument("--ruleset", type=Path, default=DEFAULT_RULESET)
    p.add_argument("--league", type=int, help="score with this league's frozen ruleset")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("report", help="balance and composition of a scoring run")
    p.add_argument("--run", type=int, help="run id (default: latest)")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("league", help="leagues and their settings, for game masters")
    league_sub = p.add_subparsers(required=True)
    pp = league_sub.add_parser("preset", help="settings presets authored by GameMakers")
    preset_sub = pp.add_subparsers(required=True)
    q = preset_sub.add_parser("save", help="create or replace a preset from a TOML file")
    q.add_argument("name")
    q.add_argument("--file", type=Path, required=True)
    q.add_argument("--by", required=True, help="who authored it")
    q.set_defaults(func=cmd_preset_save)
    q = preset_sub.add_parser("list", help="show presets")
    q.set_defaults(func=cmd_preset_list)
    q = league_sub.add_parser("create", help="create a league from a preset, with overrides")
    q.add_argument("--name", required=True)
    q.add_argument("--type", required=True, choices=leagues.OFFICIAL_TYPES + leagues.PRIVATE_TYPES)
    q.add_argument("--timing", choices=leagues.OFFICIAL_TYPES, help="for standard_private: whose dates to follow")
    q.add_argument("--congress", type=int)
    q.add_argument("--session", type=int)
    q.add_argument("--year", type=int, help="annual: the year; presidential or senatorial: the first year")
    q.add_argument("--start", type=date.fromisoformat, help="flexible_private only")
    q.add_argument("--end", type=date.fromisoformat, help="flexible_private only (exclusive)")
    q.add_argument("--preset", default="standard")
    q.add_argument("--set", action="append", metavar="PATH=VALUE",
                   help="override a setting, e.g. budget_rules.annual_budget=40000 or "
                        "'roster_rules.chamber_slots={\"house\": 6, \"senate\": 2}'")
    q.add_argument("--ruleset", type=Path, default=DEFAULT_RULESET)
    q.add_argument("--by", required=True, help="the game master creating it")
    q.add_argument("--role", choices=("gamemaker", "commissioner"))
    q.set_defaults(func=cmd_league_create)
    q = league_sub.add_parser("update", help="change a league's settings or ruleset before it starts")
    q.add_argument("league", type=int)
    q.add_argument("--set", action="append", metavar="PATH=VALUE")
    q.add_argument("--ruleset", type=Path, help="switch to this ruleset")
    q.set_defaults(func=cmd_league_update)
    q = league_sub.add_parser("show", help="show one league, or all")
    q.add_argument("league", type=int, nargs="?")
    q.set_defaults(func=cmd_league_show)
    on = dict(type=date.fromisoformat, default=date.today(), help="the date it happens (default: today)")
    year = dict(type=int, help="legislative year (default: the one under way on --on, or the league's first)")
    q = league_sub.add_parser("join", help="give a player a roster in a league")
    q.add_argument("league", type=int)
    q.add_argument("player")
    q.add_argument("--on", **on)
    q.set_defaults(func=cmd_league_join)
    q = league_sub.add_parser("buy", help="buy critters for a player's roster")
    q.add_argument("league", type=int)
    q.add_argument("player")
    q.add_argument("critters", nargs="+", help="bioguide ids or parts of names")
    q.add_argument("--year", **year)
    q.add_argument("--on", **on)
    q.set_defaults(func=cmd_league_buy)
    q = league_sub.add_parser("drop", help="drop critters from a player's roster")
    q.add_argument("league", type=int)
    q.add_argument("player")
    q.add_argument("critters", nargs="+", help="bioguide ids or parts of names")
    q.add_argument("--year", **year)
    q.add_argument("--on", **on)
    q.set_defaults(func=cmd_league_drop)
    q = league_sub.add_parser("roster", help="a player's critters, budget and points")
    q.add_argument("league", type=int)
    q.add_argument("player")
    q.add_argument("--year", type=int, help="only this legislative year")
    q.add_argument("--on", **{**on, "help": "as of this date (default: today)"})
    q.set_defaults(func=cmd_league_roster)
    q = league_sub.add_parser("standings", help="players ranked by points")
    q.add_argument("league", type=int)
    q.add_argument("--on", **{**on, "help": "as of this date (default: today)"})
    q.set_defaults(func=cmd_league_standings)

    p = sub.add_parser("price", help="price critters for a session from a scoring run")
    p.add_argument("--run", type=int, help="run id (default: latest)")
    p.add_argument("--session", type=int, default=2, help="session to price (needs the one before it)")
    p.add_argument("--prev-run", type=int, help="run of the previous Congress, for session 1 "
                                                "(default: its latest run)")
    p.add_argument("--as-of", type=date.fromisoformat,
                   help="price critters seated, with the seats they hold, on this date (default: "
                        "the session's first day; a new Congress seats committees weeks later)")
    p.add_argument("--fec-cycle", type=int, help="FEC cycle for donations (default: last one complete "
                                                  "when the session opens)")
    p.add_argument("--ruleset", type=Path, default=DEFAULT_RULESET, help="ruleset with the pricing constants")
    p.add_argument("--league", type=int, help="price with this league's ruleset and check its budget")
    p.add_argument("--top", type=int, default=8)
    p.set_defaults(func=cmd_price)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
