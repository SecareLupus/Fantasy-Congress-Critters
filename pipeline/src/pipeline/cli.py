import argparse
import time
from datetime import date
from statistics import correlation, quantiles

from pathlib import Path

from . import db, download, fec, legislators, pricing, rosters, scoring
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
    memberships = []
    for m in rosters.build_memberships(snapshots, start, end):
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
    items.extend(scoring.score_votes(votes, ruleset, sessions, seated, db.delegates(conn)))

    def chamber_of(bioguide: str, day) -> str:
        return "sen" if any(a <= day <= b for a, b in terms.get((bioguide, "sen"), [])) else "rep"

    scoring.apply_chamber_factor(items, ruleset, chamber_of)
    items.extend(scoring.score_positions(positions, ruleset, sessions,
                                         scoring.floor_participation(votes, exempt)))
    return db.save_score_run(conn, congress, ruleset, items), items


def cmd_score(args) -> None:
    ruleset = scoring.Ruleset.load(args.ruleset)
    with db.connect() as conn:
        db.init_schema(conn)
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
        ruleset = scoring.Ruleset.load(args.ruleset)
        cfg = ruleset.raw["pricing"]
        cycle = args.fec_cycle or download.pricing_cycle(congress, args.session)
        path = download.fec_summary_path(cycle)
        if not path.exists():
            raise SystemExit(f"missing {path}: run critters download (or pass --fec-cycle)")
        receipts = fec.receipts(path)
        rows = db.pricing_inputs(conn, run_id, args.session, cfg["min_days_served"])
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

    start = date(download.session_year(congress, args.session), 1, 3)
    end = date(start.year + 1, 1, 3)
    left = {r["bioguide_id"]: r["left_office"] for r in rows}
    costs = sorted(p.session_cost for p in prices)
    q1, q2, q3 = quantiles(costs, n=4)
    print(f"run {run_id}: {congress}th Congress session {args.session} ({start.year}), "
          f"ruleset {ruleset.version}, FEC cycle {cycle}")
    print(f"{len(prices)} critters seated on {start}: "
          + ", ".join(f"{c} {sum(p.chamber == c for p in prices)}" for c in ("rep", "sen")))
    print(f"Session Cost: min ${costs[0]:,}  25% ${q1:,.0f}  median ${q2:,.0f}  75% ${q3:,.0f}  max ${costs[-1]:,}")
    budget = ruleset.raw.get("league", {}).get("budget")
    if budget:
        print(f"budget ${budget:,} = {budget / q3:.1f} x the 75th percentile")

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
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("report", help="balance and composition of a scoring run")
    p.add_argument("--run", type=int, help="run id (default: latest)")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("price", help="price critters for a session from a scoring run")
    p.add_argument("--run", type=int, help="run id (default: latest)")
    p.add_argument("--session", type=int, default=2, help="session to price (needs the one before it)")
    p.add_argument("--fec-cycle", type=int, help="FEC cycle for donations (default: last one complete "
                                                  "when the session opens)")
    p.add_argument("--ruleset", type=Path, default=DEFAULT_RULESET, help="ruleset with the pricing constants")
    p.add_argument("--top", type=int, default=8)
    p.set_defaults(func=cmd_price)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
