import argparse
import json
import time
import tomllib
from datetime import date, timedelta
from statistics import correlation, quantiles

from pathlib import Path

from . import auth, db, download, fec, leagues, ledger, legislators, live, play, pricing, scoring
from .build import DEFAULT_RULESET, load_rosters, score_congress
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


def cmd_score(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        if args.league:
            league = play.league(conn, args.league)
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
        names = db.names(conn)

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
    if league["join_code"]:
        print(f"  join code {league['join_code']}")
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
    role = args.role or ("gamemaker" if args.type in leagues.OFFICIAL_TYPES else "commissioner")
    try:
        overrides = leagues.parse_overrides(args.set or [])
    except ValueError as e:
        raise SystemExit(str(e))
    with db.connect() as conn:
        db.init_schema(conn)
        preset = db.presets(conn).get(args.preset)
        if preset is None:
            raise SystemExit(f"no preset {args.preset!r}; save one with critters league preset save")
        dates = {k: v for k in ("congress", "session", "year", "start", "end") if (v := getattr(args, k)) is not None}
        league_id = play.create_league(
            conn, name=args.name, league_type=args.type, timing=args.timing,
            settings=leagues.resolve(preset["settings"], overrides), preset=args.preset,
            ruleset=scoring.Ruleset.load(args.ruleset), created_by=args.by, role=role, **dates)
        _print_league(db.leagues(conn, league_id)[0])


def cmd_league_update(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        try:
            settings = leagues.resolve(league["settings"], leagues.parse_overrides(args.set or []))
        except ValueError as e:
            raise SystemExit(str(e))
        play.update_league(conn, league, settings, date.today(),
                           ruleset=scoring.Ruleset.load(args.ruleset) if args.ruleset else None)
        _print_league(db.leagues(conn, args.league)[0])


def cmd_league_show(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        found = db.leagues(conn, args.league)
        if args.league and not found:
            raise SystemExit(f"no league {args.league}")
        for league in found:
            _print_league(league)


def _weeks_done(m: play.Market, final: set[int], as_of: date) -> str:
    """How many league weeks have ended, and how many of those are settled for good."""
    ended = m.cal.settled(as_of)
    done = f"{len(ended)}/{len(m.cal.weeks)} weeks ended"
    if final:
        done += f", {len(final & set(ended))} final"
    return done


def cmd_league_join(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        play.join(conn, league, args.player, args.on)
    print(f"{args.player} joined league {args.league} ({league['name']}) on {args.on}")


def cmd_league_buy(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        roster = play.roster(conn, league, args.player)
        m = play.market(conn, league, args.year or play.year_on(league, args.on))
        play.tradable(league, m)
        market = db.priced(conn, m.price_run, m.session.number)
        for text in args.critters:
            bioguide, name = play.one_critter(conn, text, market)
            h = play.buy(conn, league, roster, m, bioguide, args.on)
            weeks = h.last_week - h.first_week + 1
            print(f"{args.player} bought {name} ({h.chamber}) on {args.on} for {m.year}: ${h.session_cost:,} "
                  f"Session Cost, ${h.signing_fee:,.2f} signing + {weeks} weeks at ${h.weekly_fee:,.2f} "
                  f"from week {h.first_week}")
        b = play.budget(conn, league, roster, m, args.on)
    print(f"available ${b.available:,.2f} of ${b.budget:,}")


def cmd_league_drop(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        roster = play.roster(conn, league, args.player)
        m = play.market(conn, league, args.year or play.year_on(league, args.on))
        for text in args.critters:
            held = db.holdings(conn, roster["roster_id"], m.congress, m.session)
            bioguide, name = play.one_critter(conn, text, [h.bioguide_id for h in held if h.active(args.on)])
            h = play.drop(conn, league, roster, m, bioguide, args.on)
            returned = h.weekly_fee * max(0, h.last_week - h.drop_week + 1)
            held = (f"held through week {h.drop_week - 1}" if h.drop_week > h.first_week
                    else "before its first week")
            print(f"{args.player} dropped {name} on {args.on}: {held}, ${returned:,.2f} reserved returned"
                  + (f", ${h.extra_fee:,} drop fee" if h.extra_fee else "")
                  + (f", {h.points_penalty:g} points penalty" if h.points_penalty else ""))
        b = play.budget(conn, league, roster, m, args.on)
    print(f"available ${b.available:,.2f} of ${b.budget:,}")


def cmd_league_roster(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        roster = play.roster(conn, league, args.player)
        markets = [m for m in play.league_years(conn, league) if args.year in (None, m.year)]
        scored = play.roster_points(conn, league, roster, markets, args.on)
        final = {m.year: play.final_weeks(conn, league, m) for m in markets}
        names = db.names(conn)
    annual = league["settings"]["budget_rules"]["annual_budget"]
    print(f"{args.player} in league {league['league_id']} ({league['name']}), as of {args.on}")
    for m in markets:
        s = scored[m.year]
        held = [h for h, _ in s["holdings"]]
        b = ledger.budget(held, m.cal, annual, args.on)
        print(f"\n{m.year} (weeks {m.cal.weeks[0]}-{m.cal.weeks[-1]}, {_weeks_done(m, final[m.year], args.on)}; "
              f"run {m.run_id})")
        print(f"  budget ${b.budget:,}: spent ${b.spent:,.2f}, reserved ${b.reserved:,.2f}, "
              f"available ${b.available:,.2f}")
        for h, (p, q) in s["holdings"]:
            match play.status(h, args.on):
                case "dropped" if h.drop_week <= h.first_week:
                    status = f"dropped {h.dropped_on}, before its first week"
                case "dropped":
                    status = f"dropped {h.dropped_on}, held weeks {h.first_week}-{h.drop_week - 1}"
                case "left_office":
                    status = f"left office {h.left_office}"
                case "held":
                    status = f"held from week {h.first_week}"
                case _:
                    continue
            print(f"  {names.get(h.bioguide_id, h.bioguide_id):<28} {h.chamber} ${h.session_cost:>6,} "
                  f"bought {h.made_on}  {p + q:>7.1f} pts ({p:.0f} power + {q:.0f} productivity)  {status}")
        total = s["power"] + s["productivity"] - s["penalties"]
        print(f"  total {total:.1f} = {s['power']:.1f} power + {s['productivity']:.1f} productivity"
              f" - {s['penalties']:g} penalties")


def cmd_league_standings(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        league = play.league(conn, args.league)
        markets = play.league_years(conn, league)
        final = {m.year: play.final_weeks(conn, league, m) for m in markets}
        table = play.standings(conn, league, markets, args.on)
    print(f"league {league['league_id']} ({league['name']}), as of {args.on}: "
          + ", ".join(f"{m.year} {_weeks_done(m, final[m.year], args.on)}" for m in markets))
    if league["settings"]["win_condition"] != "cumulative":
        print(f"(win condition {league['settings']['win_condition']} isn't built yet; showing cumulative points)")
    for rank, s in enumerate(table, 1):
        print(f"  {rank:>2}. {s.player:<20} {s.total:>8.1f}  ({s.power:.0f} power + {s.productivity:.0f} productivity"
              + (f" - {s.penalties:g} penalties" if s.penalties else "") + ")")


def cmd_update(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        if not conn.execute("SELECT pg_try_advisory_lock(hashtext('critters update'))").fetchone()[0]:
            raise SystemExit("another update is running")
        failures = live.update(conn, date.today(), rescore=args.rescore, congresses=args.congress)
    if failures:
        raise SystemExit(f"failed: {', '.join(failures)}")


def cmd_status(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        lines = live.status_lines(conn)
    print("\n".join(lines) or "no updates yet: critters update")


def cmd_invite_create(args) -> None:
    from datetime import datetime, timezone
    expires = datetime.now(timezone.utc) + timedelta(days=args.days) if args.days else None
    with db.connect() as conn:
        db.init_schema(conn)
        codes = [auth.new_invite_code() for _ in range(args.count)]
        for code in codes:
            db.create_invite(conn, code, args.role, args.uses, expires, args.note, args.by)
    for code in codes:
        print(code)
    print(f"{len(codes)} invite{'s' if len(codes) > 1 else ''} for {args.role}s, {args.uses} use"
          f"{'s' if args.uses > 1 else ''} each" + (f", expiring {expires:%Y-%m-%d %H:%M} UTC" if expires else ""))


def cmd_invite_list(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        for i in db.invites(conn):
            expiry = f"expires {i['expires_at']:%Y-%m-%d}" if i["expires_at"] else "no expiry"
            print(f"{i['code']}  {i['role']:<12} {i['uses']}/{i['max_uses']} used, {expiry}, by {i['created_by']}"
                  + (f" ({i['note']})" if i["note"] else "")
                  + (f": {', '.join(i['accounts'])}" if i["accounts"] else ""))


def _account(conn, username: str) -> dict:
    found = db.account_by_name(conn, username)
    if found is None:
        raise SystemExit(f"no account {username}")
    return found


def cmd_account_list(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        for a in db.accounts(conn):
            print(f"{a['username']:<24} {a['role']:<12} {a['rosters']} roster{'s' if a['rosters'] != 1 else ''}, "
                  f"joined {a['created_at']:%Y-%m-%d}" + (" DISABLED" if a["disabled"] else ""))


def cmd_account_update(args) -> None:
    changes = {}
    if args.role:
        changes["role"] = args.role
    if args.disable or args.enable:
        changes["disabled"] = bool(args.disable)
    password = None
    if args.reset_password:
        password = auth.new_token()[:16]
        changes["password_hash"] = auth.hash_password(password)
    if not changes:
        raise SystemExit("nothing to change: pass --role, --reset-password, --disable or --enable")
    with db.connect() as conn:
        db.init_schema(conn)
        account = _account(conn, args.username)
        db.update_account(conn, account["account_id"], **changes)
    done = [f"role {args.role}"] if args.role else []
    done += ["disabled"] if args.disable else ["enabled"] if args.enable else []
    done += ["password reset"] if password else []
    print(f"{account['username']}: {', '.join(done)}")
    if password:
        print(f"temporary password: {password} (signed out everywhere; send it privately)")


def cmd_serve(args) -> None:
    import uvicorn
    # Behind a proxy, trust its X-Forwarded-For so sign-in throttling sees visitors' addresses.
    uvicorn.run("pipeline.api:app", host=args.host, port=args.port, reload=args.reload,
                proxy_headers=bool(args.forwarded_allow_ips), forwarded_allow_ips=args.forwarded_allow_ips)


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

    p = sub.add_parser("update", help="bring live data current, rescore and settle weeks (run daily)")
    p.add_argument("--congress", type=int, action="append",
                   help="update this Congress (repeatable; default: the one in session, and the one "
                        "before it for the new Congress's first 30 days)")
    p.add_argument("--rescore", action="store_true", help="rescore even if no data changed")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("status", help="when each source last updated, and what failed")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("invite", help="invite codes for website accounts (the beta is invite-only)")
    invite_sub = p.add_subparsers(required=True)
    q = invite_sub.add_parser("create", help="make invite codes")
    q.add_argument("--by", required=True, help="who is inviting")
    q.add_argument("--role", choices=auth.ROLES, default="player")
    q.add_argument("--uses", type=int, default=1, help="accounts each code can make (default 1)")
    q.add_argument("--days", type=int, default=30, help="days until it expires (0: never; default 30)")
    q.add_argument("--count", type=int, default=1, help="how many codes")
    q.add_argument("--note", help="who it's for")
    q.set_defaults(func=cmd_invite_create)
    q = invite_sub.add_parser("list", help="invite codes and the accounts they made")
    q.set_defaults(func=cmd_invite_list)

    p = sub.add_parser("account", help="website accounts")
    account_sub = p.add_subparsers(required=True)
    q = account_sub.add_parser("list", help="every account")
    q.set_defaults(func=cmd_account_list)
    q = account_sub.add_parser("update", help="change an account's role, reset its password, or disable it")
    q.add_argument("username")
    q.add_argument("--role", choices=auth.ROLES)
    q.add_argument("--reset-password", action="store_true", help="set and print a temporary password")
    q.add_argument("--disable", action="store_true", help="block sign-in and sign it out everywhere")
    q.add_argument("--enable", action="store_true")
    q.set_defaults(func=cmd_account_update)

    p = sub.add_parser("serve", help="run the web API (and the built site, if web/dist exists)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--reload", action="store_true", help="restart when the code changes (development)")
    p.add_argument("--forwarded-allow-ips", metavar="IPS",
                   help="addresses of a reverse proxy to trust for the visitor's address, e.g. '*' when only "
                        "the proxy can reach the app")
    p.set_defaults(func=cmd_serve)

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
    try:
        args.func(args)
    except play.Problem as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
