"""Keep a live season current: `critters update`, run once a day by a scheduler.

Each source is brought up to date on its own and logged in source_syncs, so one failing
doesn't stop the others; the command exits non-zero when any did, for the scheduler to report.

- legislators: congress-legislators members, terms and committees, when the files change.
- rosters: the House Clerk's MemberData.xml and senate.gov's committee lists, recorded as a
  roster snapshot whenever a seat changes, so seat changes are dated to the day.
- billstatus: GovInfo rebuilds its BILLSTATUS zips daily; bills whose update date changed
  are reloaded.
- house_votes: new House Clerk roll calls.
- senate_votes: Voteview's Senate files, reloaded when they change.

When anything changed, the Congress is rescored with each ruleset in play (the default and
those of leagues not yet over) as a live run, which replaces the previous one. Then weeks
settle (Design-Data §10.4): a week's points are frozen once it has been over for
SETTLE_AFTER_DAYS, every source has synced since then, and every roll call that bill
actions cite for the week is loaded. Later corrections to a settled week are reported as
drift, not applied.
"""

import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import db, download, legislators, rosters, scoring
from .billstatus import iter_zip
from .build import DEFAULT_RULESET, load_rosters, score_congress
from .normalize import normalize_bill
from .votes import iter_house_votes, parse_voteview_senate

SOURCES = ("legislators", "rosters", "billstatus", "house_votes", "senate_votes")
SETTLE_AFTER_DAYS = 3
# Days into a new Congress that the previous one is still updated, for its last week.
PREVIOUS_CONGRESS_DAYS = 30
# A roster snapshot smaller than this share of the last one is taken as a source glitch.
MIN_ROSTER_SHARE = 0.8


def congress_on(day: date) -> int:
    year = day.year if day >= date(day.year, 1, 3) else day.year - 1
    return (year - 1787) // 2


class Step:
    """Run one source's sync and log it; an exception is logged as a failure and swallowed."""

    units = {"score": "run", "settle": "weeks settled"}

    def __init__(self, conn, failures: list[str]):
        self.conn, self.failures = conn, failures

    def __call__(self, source: str, congress: int | None, fn: Callable[[], tuple[int, object, str | None]]) -> int:
        started, clock = datetime.now(timezone.utc), time.time()
        label = source + (f" {congress}" if congress else "")
        try:
            changed, latest, note = fn()
        except Exception as e:  # noqa: BLE001 - any failure is logged and the next source runs
            self.conn.rollback()
            db.record_sync(self.conn, source, congress, started, False, note=f"{type(e).__name__}: {e}")
            self.failures.append(label)
            print(f"{label}: FAILED {type(e).__name__}: {e}")
            return 0
        db.record_sync(self.conn, source, congress, started, True, changed, latest, note)
        print(f"{label}: {changed} {self.units.get(source, 'changed')}" + (f", latest {latest}" if latest else "")
              + (f" ({note})" if note else "") + f" ({time.time() - clock:.1f}s)")
        return changed


def sync_legislators(conn) -> tuple[int, object, str | None]:
    changed = download.refresh_legislators()
    if changed:
        legislators.load_critters(conn)
        legislators.load_committees(conn)
        db.add_missing_committees(conn)
        conn.commit()
    return len(changed), None, ", ".join(changed) or None


def official_snapshot(conn, congress: int, day: date) -> tuple[dict, list[str]]:
    """Today's rosters from both chambers, and notes on what was left out. Until the House
    Clerk lists the new Congress (the House has no committees before it organizes), the
    House's seats are left out."""
    with open(download.legislators_path("committees-current.yaml")) as f:
        committees = yaml.load(f, Loader=yaml.CSafeLoader)
    house_ids = {c["house_committee_id"]: c["thomas_id"] for c in committees if c.get("house_committee_id")}
    senate_codes = [c["senate_committee_id"] for c in committees if c.get("senate_committee_id")]
    house, senate = download.fetch_official_rosters(senate_codes)
    notes = []
    listed = rosters.house_congress(house)
    if listed == congress:
        snapshot = rosters.house_seats(house, house_ids)
    else:
        snapshot = {}
        notes.append(f"the House Clerk still lists the {listed}th Congress; House seats left out")
    unmatched = []
    senators = db.senators_on(conn, day)
    for xml in senate.values():
        seats, missed = rosters.senate_seats(xml, senators)
        unmatched += missed
        for key, members in seats.items():
            snapshot.setdefault(key, []).extend(members)
    if unmatched:
        notes.append(f"{len(unmatched)} Senate seats of members not in congress-legislators yet: "
                     + "; ".join(sorted(unmatched)[:5]))
    return snapshot, notes


def sync_rosters(conn, congress: int, day: date, rebuild: bool) -> tuple[int, object, str | None]:
    snapshot, notes = official_snapshot(conn, congress, day)
    seats = rosters.parse_snapshot(snapshot)
    known = download.official_rosters_dir(congress)
    previous = rosters.load_snapshots(known)
    last = previous[-1][1] if previous else None
    if last is not None and len(seats) < MIN_ROSTER_SHARE * len(last):
        raise RuntimeError(f"{len(seats)} seats listed against {len(last)} last time; not recorded")
    changed = len(seats ^ last) if last is not None else len(seats)
    if changed:
        known.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        with open(known / f"{stamp}_official.yaml", "w") as f:
            yaml.safe_dump(snapshot, f, sort_keys=True, allow_unicode=True)
    if changed or rebuild:
        load_rosters(conn, congress)
    return changed, None, "; ".join(notes) or None


def sync_billstatus(conn, congress: int) -> tuple[int, object, str | None]:
    types = download.refresh_billstatus(congress)
    known = db.bill_update_dates(conn, congress)
    changed = 0
    for bill_type in types:
        for bill in iter_zip(download.billstatus_path(congress, bill_type)):
            if bill.bill_id not in known or known[bill.bill_id] != bill.update_date:
                db.save_bill(conn, bill, normalize_bill(bill))
                changed += 1
        conn.commit()
    if changed:
        db.add_missing_committees(conn)
        conn.commit()
    latest = max((d for d in db.bill_update_dates(conn, congress).values() if d), default=None)
    return changed, latest, ", ".join(types) + " rebuilt" if types else None


def sync_house_votes(conn, congress: int, day: date) -> tuple[int, object, str | None]:
    sessions = [s for s in scoring.congress_sessions(congress) if s.start <= day]
    download.download_house_votes(congress, sessions=[s.number for s in sessions])
    changed = 0
    for s in sessions:
        have = db.roll_numbers(conn, "House", congress, s.number)
        for rc in iter_house_votes(download.house_votes_dir(congress, s.number)):
            if rc.roll_number not in have:
                db.save_roll_call(conn, rc)
                changed += 1
        conn.commit()
    return changed, db.latest_vote(conn, "House", congress), None


def sync_senate_votes(conn, congress: int) -> tuple[int, object, str | None]:
    try:
        fresh = download.refresh_senate_votes(congress)
    except download.NotPublished:
        # Voteview starts a Congress's files with its first votes; settlement still waits
        # for any Senate roll call that bill actions cite.
        return 0, None, "Voteview has no files for this Congress yet"
    if not fresh:
        return 0, db.latest_vote(conn, "Senate", congress), None
    have = {s.number: db.roll_numbers(conn, "Senate", congress, s.number) for s in scoring.congress_sessions(congress)}
    senate = parse_voteview_senate(*(download.voteview_path(congress, k) for k in download.VOTEVIEW_KINDS))
    for rc in senate:
        db.save_roll_call(conn, rc)
    conn.commit()
    new = sum(rc.roll_number not in have[rc.session] for rc in senate)
    return new, db.latest_vote(conn, "Senate", congress), f"{len(senate)} roll calls reloaded"


def live_rulesets(conn, day: date) -> list[scoring.Ruleset]:
    """The default ruleset and those of leagues not yet over, without repeats."""
    found = [scoring.Ruleset.load(DEFAULT_RULESET)]
    found += [scoring.Ruleset(lg["ruleset_version"], lg["ruleset"]) for lg in db.leagues(conn) if lg["end_date"] > day]
    unique: dict[str, scoring.Ruleset] = {}
    for r in found:
        unique.setdefault(yaml.safe_dump(r.raw, sort_keys=True), r)
    return list(unique.values())


def settle_plan(bounds: list[tuple[date, date]], settled: set[int], day: date, synced: dict[str, datetime | None],
                missing: Callable[[date], list[str]], sources: tuple[str, ...] = SOURCES,
                after_days: int = SETTLE_AFTER_DAYS) -> tuple[list[int], str | None]:
    """The weeks that can settle now, in order, and why the next one can't (None if it isn't due)."""
    ready = []
    for week, (_, end) in enumerate(bounds, 1):
        if week in settled:
            continue
        due = end + timedelta(days=after_days)
        if due > day:
            return ready, None
        stale = [s for s in sources if synced.get(s) is None or synced[s].date() < due]
        if stale:
            return ready, f"week {week} waits for {', '.join(stale)} to sync on or after {due}"
        gaps = missing(end)
        if gaps:
            return ready, (f"week {week} waits for {len(gaps)} roll calls cited in bill actions: "
                           + ", ".join(gaps[:5]))
        ready.append(week)
    return ready, None


def settle(conn, congress: int, ruleset: scoring.Ruleset, run_id: int, day: date) -> tuple[int, object, str | None]:
    weeks = ruleset.raw["settlement"]["weeks"]
    synced = db.last_synced(conn, congress)
    # Rosters are recorded for the Congress in session only; a past one's are final.
    sources = SOURCES if congress == congress_on(day) else tuple(s for s in SOURCES if s != "rosters")
    done, notes = 0, []
    for session in scoring.congress_sessions(congress):
        if session.start > day:
            continue
        ready, waiting = settle_plan(scoring.week_bounds(session, weeks), db.settled_weeks(conn, ruleset.raw, congress, session.number),
                                     day, synced, lambda end: db.missing_roll_calls(conn, congress, session.number, end),
                                     sources)
        for week in ready:
            db.settle_week(conn, ruleset.raw, congress, session.number, week, run_id)
        done += len(ready)
        if ready:
            notes.append(f"session {session.number} weeks {ready[0]}-{ready[-1]} settled from run {run_id}")
        if waiting:
            notes.append(f"session {session.number} {waiting}")
    drifted = db.drift(conn, run_id)
    if drifted:
        notes.append("corrections to settled weeks not applied: " + "; ".join(
            f"session {s} week {w}: {n} critters, {net:+.1f} points" for s, w, n, net, _ in drifted[:5])
            + (f" (+{len(drifted) - 5} weeks)" if len(drifted) > 5 else ""))
    return done, None, "; ".join(notes) or None


def update(conn, day: date, rescore: bool = False, congresses: list[int] | None = None) -> list[str]:
    """Bring every source current, rescore and settle; returns the steps that failed."""
    failures: list[str] = []
    step = Step(conn, failures)
    current = congress_on(day)
    if congresses is None:
        congresses = [current]
        if day < scoring.congress_sessions(current)[0].start + timedelta(days=PREVIOUS_CONGRESS_DAYS):
            congresses.insert(0, current - 1)
    terms_changed = step("legislators", None, lambda: sync_legislators(conn))
    for congress in congresses:
        changed = terms_changed
        if congress == current:
            changed += step("rosters", congress, lambda: sync_rosters(conn, congress, day, rebuild=bool(terms_changed)))
        elif terms_changed:
            load_rosters(conn, congress)
        changed += step("billstatus", congress, lambda: sync_billstatus(conn, congress))
        changed += step("house_votes", congress, lambda: sync_house_votes(conn, congress, day))
        changed += step("senate_votes", congress, lambda: sync_senate_votes(conn, congress))
        for ruleset in live_rulesets(conn, day):
            run_id = db.league_run(conn, ruleset.raw, congress)
            if changed or rescore or run_id is None:
                def score() -> tuple[int, object, str | None]:
                    new_run, items = score_congress(conn, congress, ruleset, live=True)
                    gone = db.prune_live_runs(conn, ruleset.raw, congress, new_run)
                    return 1, None, f"run {new_run}, ruleset {ruleset.version}, {len(items):,} items" + (
                        f", replaced run {', '.join(map(str, gone))}" if gone else "")
                if not step("score", congress, score):
                    continue
                run_id = db.league_run(conn, ruleset.raw, congress)
            step("settle", congress, lambda: settle(conn, congress, ruleset, run_id, day))
    return failures


def status_lines(conn) -> list[str]:
    lines = []
    for source, congress, at, ok, note, last_ok, latest in db.sync_status(conn):
        label = source + (f" {congress}" if congress else "")
        lines.append(f"{label:<17} last {'ok' if ok else 'FAILED'} {at:%Y-%m-%d %H:%M}"
                     + (f", last success {last_ok:%Y-%m-%d %H:%M}" if not ok and last_ok else "")
                     + (f", newest data {latest:%Y-%m-%d}" if latest else "")
                     + (f"\n{'':<17} {note}" if note else ""))
    for run_id, congress, version, created, settled in db.live_runs(conn):
        lines.append(f"live run {run_id} ({congress}th Congress, ruleset {version}, {created:%Y-%m-%d %H:%M}): "
                     + (", ".join(f"session {s} settled through week {w}" for s, w in settled) or "nothing settled"))
    return lines
