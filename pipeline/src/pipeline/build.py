"""Steps that rebuild derived tables, shared by the manual commands and `critters update`:
committee memberships from roster snapshots, and scoring runs."""

from pathlib import Path

from . import db, download, rosters, scoring

# Committee code prefix -> the term types whose dates bound a seat on it.
ROSTER_TERM_TYPES = {"h": ("rep",), "s": ("sen",), "j": ("rep", "sen")}


def roster_snapshots(congress: int) -> list:
    """Snapshots from congress-legislators' history, then from the chambers' own lists once
    `critters update` has recorded them (which replace the history from their first day)."""
    history = rosters.load_snapshots(download.roster_history_dir(congress))
    official = rosters.load_snapshots(download.official_rosters_dir(congress))
    if not official:
        return history
    return [s for s in history if s[0] < official[0][0]] + official


def load_rosters(conn, congress: int) -> None:
    start, end = download.congress_dates(congress)
    snapshots = roster_snapshots(congress)
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


def score_congress(conn, congress: int, ruleset: scoring.Ruleset, live: bool = False) -> tuple[int, list]:
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
    return db.save_score_run(conn, congress, ruleset, items, weekly, live), items
