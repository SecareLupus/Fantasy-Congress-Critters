from collections.abc import Iterable
from importlib.resources import files

import psycopg
from psycopg.types.json import Jsonb

from .billstatus import Action, Bill
from .config import DATABASE_URL
from .ledger import Holding
from .normalize import Event
from .rosters import Membership, Senator
from .votes import RollCall


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(files("pipeline").joinpath("schema.sql").read_text())
    conn.commit()


def _recorded_votes(action: Action) -> Jsonb:
    return Jsonb([{"chamber": v.chamber, "congress": v.congress, "session": v.session,
                   "roll_number": v.roll_number} for v in action.recorded_votes])


def save_bill(conn: psycopg.Connection, bill: Bill, events: Iterable[Event]) -> None:
    """Replace a bill and everything derived from it."""
    bill_id = bill.bill_id
    with conn.cursor() as cur:
        cur.execute("DELETE FROM bills WHERE bill_id = %s", (bill_id,))
        cur.execute(
            """INSERT INTO bills (bill_id, congress, bill_type, number, title, introduced_date,
                   origin_chamber, policy_area, sponsor_id, sponsor_by_request, update_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (bill_id, bill.congress, bill.bill_type, bill.number, bill.title, bill.introduced_date,
             bill.origin_chamber, bill.policy_area, bill.sponsor_id, bill.sponsor_by_request,
             bill.update_date),
        )
        cur.executemany(
            """INSERT INTO bill_cosponsors (bill_id, bioguide_id, sponsorship_date, is_original, withdrawn_date)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            [(bill_id, c.bioguide_id, c.sponsorship_date, c.is_original, c.withdrawn_date)
             for c in bill.cosponsors],
        )
        cur.executemany(
            "INSERT INTO bill_subjects (bill_id, subject) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            [(bill_id, subject) for subject in bill.subjects],
        )
        cur.executemany(
            """INSERT INTO bill_committee_activities (bill_id, committee_code, parent_committee_code,
                   committee_name, chamber, activity, activity_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [(bill_id, a.committee_code, a.parent_committee_code, a.committee_name, a.chamber,
              a.activity, a.activity_at) for a in bill.committee_activities],
        )
        cur.executemany(
            """INSERT INTO bill_actions (bill_id, seq, action_date, action_time, text, action_type,
                   action_code, source_name, committee_codes, recorded_votes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(bill_id, a.seq, a.action_date, a.action_time, a.text, a.action_type, a.action_code,
              a.source_name, a.committee_codes, _recorded_votes(a)) for a in bill.actions],
        )
        cur.executemany(
            """INSERT INTO amendments (amendment_id, bill_id, congress, amendment_type, number,
                   chamber, sponsor_id, sponsor_name, on_behalf_of_id, submitted_date,
                   proposed_date, description, purpose, amended_amendment_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(m.amendment_id, bill_id, m.congress, m.amendment_type, m.number, m.chamber,
              m.sponsor_id, m.sponsor_name, m.on_behalf_of_id, m.submitted_date, m.proposed_date,
              m.description, m.purpose, m.amended_amendment_id) for m in bill.amendments],
        )
        cur.executemany(
            """INSERT INTO amendment_cosponsors (amendment_id, bioguide_id, sponsorship_date,
                   is_original, withdrawn_date)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            [(m.amendment_id, c.bioguide_id, c.sponsorship_date, c.is_original, c.withdrawn_date)
             for m in bill.amendments for c in m.cosponsors],
        )
        cur.executemany(
            """INSERT INTO amendment_actions (amendment_id, seq, action_date, action_time, text,
                   action_type, action_code, source_name, recorded_votes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(m.amendment_id, a.seq, a.action_date, a.action_time, a.text, a.action_type,
              a.action_code, a.source_name, _recorded_votes(a))
             for m in bill.amendments for a in m.actions],
        )
        cur.executemany(
            """INSERT INTO events (bill_id, event_type, event_date, chamber, committee_code,
                   critter_id, source, detail, amendment_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(e.bill_id, e.event_type, e.event_date, e.chamber, e.committee_code, e.critter_id,
              e.source, e.detail, e.amendment_id) for e in events],
        )


def save_roll_call(conn: psycopg.Connection, rc: RollCall) -> None:
    """Replace a roll call and its member positions."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM roll_calls WHERE vote_id = %s", (rc.vote_id,))
        cur.execute(
            """INSERT INTO roll_calls (vote_id, chamber, congress, session, roll_number, vote_date,
                   vote_time, question, vote_type, result, legis_num, bill_id, amendment_num,
                   amendment_author, description)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (rc.vote_id, rc.chamber, rc.congress, rc.session, rc.roll_number, rc.vote_date,
             rc.vote_time, rc.question, rc.vote_type, rc.result, rc.legis_num, rc.bill_id,
             rc.amendment_num, rc.amendment_author, rc.description),
        )
        cur.executemany(
            """INSERT INTO member_votes (vote_id, bioguide_id, position, raw_position, party, state)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            [(rc.vote_id, m.bioguide_id, m.position, m.raw_position, m.party, m.state)
             for m in rc.members],
        )


def save_memberships(conn: psycopg.Connection, congress: int, memberships: Iterable[Membership]) -> None:
    """Replace a Congress's committee memberships."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM committee_memberships WHERE congress = %s", (congress,))
        cur.executemany(
            """INSERT INTO committee_memberships (congress, committee_code, bioguide_id, side, role,
                   title, start_date, end_date, first_seen, last_seen)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [(congress, m.seat.committee_code, m.seat.bioguide_id, m.seat.side, m.seat.role,
              m.seat.title, m.start_date, m.end_date, m.first_seen, m.last_seen)
             for m in memberships],
        )


def chamber_terms(conn: psycopg.Connection) -> dict[tuple[str, str], list]:
    """(bioguide_id, term_type) -> [(start, end)], end inclusive."""
    terms: dict[tuple[str, str], list] = {}
    for bioguide, term_type, start, end in conn.execute(
        "SELECT bioguide_id, term_type, start_date, end_date FROM critter_terms ORDER BY start_date"
    ):
        terms.setdefault((bioguide, term_type), []).append((start, end))
    return terms


def parties_on(conn: psycopg.Connection, day) -> dict[str, str]:
    """bioguide_id -> party on a day. On a day two periods share (January 3, when one
    term ends as the next begins), the later one wins."""
    return dict(conn.execute(
        """SELECT DISTINCT ON (bioguide_id) bioguide_id, party FROM critter_parties
           WHERE start_date <= %(day)s AND end_date >= %(day)s
           ORDER BY bioguide_id, start_date DESC""", {"day": day}).fetchall())


def add_missing_committees(conn: psycopg.Connection) -> int:
    """Committees named in bill activity but absent from the reference data, e.g. hsha06."""
    cur = conn.execute(
        """INSERT INTO committees (committee_code, parent_committee_code, name, chamber, is_current)
           SELECT DISTINCT ON (committee_code) committee_code, parent_committee_code,
                  committee_name, lower(chamber), false
           FROM bill_committee_activities
           WHERE committee_code NOT IN (SELECT committee_code FROM committees)
           ORDER BY committee_code
           ON CONFLICT DO NOTHING"""
    )
    conn.commit()
    return cur.rowcount


def scoring_inputs(conn: psycopg.Connection, congress: int):
    """Everything the scoring engine reads for one Congress."""
    from .scoring import BillInputs, Cosponsor, EventRow, Position, VoteRow

    bills = {
        bill_id: BillInputs(bill_id, bill_type, sponsor, by_request, origin, [], [], title or "", subjects)
        for bill_id, bill_type, sponsor, by_request, origin, title, subjects in conn.execute(
            """SELECT b.bill_id, b.bill_type, b.sponsor_id, b.sponsor_by_request, b.origin_chamber, b.title,
                      coalesce(array_agg(s.subject) FILTER (WHERE s.subject IS NOT NULL), '{}')
               FROM bills b LEFT JOIN bill_subjects s USING (bill_id)
               WHERE b.congress = %s GROUP BY b.bill_id""", (congress,))
    }
    for bill_id, *row in conn.execute(
        """SELECT c.bill_id, c.bioguide_id, c.sponsorship_date, c.is_original, c.withdrawn_date
           FROM bill_cosponsors c JOIN bills b USING (bill_id)
           WHERE b.congress = %s AND c.sponsorship_date IS NOT NULL""", (congress,)):
        bills[bill_id].cosponsors.append(Cosponsor(*row))
    for bill_id, *row in conn.execute(
        """SELECT e.bill_id, e.event_type, e.event_date, e.chamber, e.committee_code,
                  e.critter_id, e.amendment_id
           FROM events e JOIN bills b USING (bill_id) WHERE b.congress = %s""", (congress,)):
        bills[bill_id].events.append(EventRow(*row))

    votes = [VoteRow(*row) for row in conn.execute(
        """SELECT rc.vote_id, rc.vote_date, rc.question, rc.result, rc.legis_num,
                  mv.bioguide_id, mv.position
           FROM member_votes mv JOIN roll_calls rc USING (vote_id)
           WHERE rc.congress = %s""", (congress,))]

    positions = [Position(*row) for row in conn.execute(
        """SELECT bioguide_id, 'committee', committee_code, role, start_date, end_date
           FROM committee_memberships WHERE congress = %s""", (congress,))]
    leadership = list(conn.execute(
        """SELECT bioguide_id, title, start_date, end_date FROM critter_leadership"""))
    return list(bills.values()), votes, positions, leadership


def save_score_run(conn: psycopg.Connection, congress: int, ruleset, items, weekly: dict,
                   live: bool = False) -> int:
    run_id = conn.execute(
        """INSERT INTO score_runs (congress, ruleset_version, ruleset, live) VALUES (%s, %s, %s, %s)
           RETURNING run_id""",
        (congress, ruleset.version, Jsonb(ruleset.raw), live),
    ).fetchone()[0]
    with conn.cursor().copy(
        """COPY score_items (run_id, bioguide_id, session, pillar, category, item_date, points,
               bill_id, amendment_id, vote_id, committee_code, detail) FROM STDIN"""
    ) as copy:
        for i in items:
            copy.write_row((run_id, i.bioguide_id, i.session, i.pillar, i.category, i.item_date,
                            i.points, i.bill_id, i.amendment_id, i.vote_id, i.committee_code,
                            Jsonb(i.detail) if i.detail else None))
    with conn.cursor().copy(
        "COPY weekly_points (run_id, bioguide_id, session, week, power, productivity) FROM STDIN"
    ) as copy:
        for (bioguide, session, week), (power, productivity) in weekly.items():
            copy.write_row((run_id, bioguide, session, week, power, productivity))
    conn.commit()
    return run_id


def score_report(conn: psycopg.Connection, run_id: int) -> dict:
    """Balance and composition of a run, over members seated for a whole session."""
    full_members = """
        SELECT DISTINCT t.bioguide_id, s.session, t.term_type AS chamber
        FROM critter_terms t
        JOIN (SELECT DISTINCT session FROM score_items WHERE run_id = %(run)s) x ON true
        JOIN LATERAL (SELECT x.session,
                             make_date(r.congress * 2 + 1787 + x.session - 1, 1, 3) AS a,
                             make_date(r.congress * 2 + 1787 + x.session, 1, 2) AS b
                      FROM score_runs r WHERE r.run_id = %(run)s) s ON true
        WHERE t.start_date <= s.a AND t.end_date >= s.b
          AND t.state NOT IN ('DC', 'PR', 'GU', 'VI', 'AS', 'MP')"""
    totals = f"""
        SELECT f.session, f.chamber, f.bioguide_id,
               coalesce(sum(i.points) FILTER (WHERE i.pillar = 'power'), 0) AS power,
               coalesce(sum(i.points) FILTER (WHERE i.pillar = 'productivity'), 0) AS productivity
        FROM ({full_members}) f
        LEFT JOIN score_items i ON i.run_id = %(run)s AND i.bioguide_id = f.bioguide_id
                               AND i.session = f.session
        GROUP BY 1, 2, 3"""
    args = {"run": run_id}
    balance = conn.execute(f"""
        SELECT session, chamber, count(*),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY power),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY productivity),
               max(power), max(productivity)
        FROM ({totals}) t GROUP BY 1, 2 ORDER BY 1, 2""", args).fetchall()
    even_scale = conn.execute(f"""
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY power / productivity)
        FROM ({totals}) t WHERE productivity > 0""", args).fetchone()[0]
    # Per pillar, the Senate factor that would bring the median senator to the median
    # House member (over both sessions).
    chamber_medians = conn.execute(f"""
        SELECT t.chamber,
               coalesce((r.ruleset->'positions'->'chamber_factor'->>t.chamber)::float, 1.0),
               coalesce((r.ruleset->'productivity'->'chamber_factor'->>t.chamber)::float, 1.0),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY power),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY productivity)
        FROM ({totals}) t JOIN score_runs r ON r.run_id = %(run)s
        GROUP BY 1, 2, 3 ORDER BY 1""", args).fetchall()
    composition = conn.execute("""
        SELECT pillar, category, sum(points), 100 * sum(points) / sum(sum(points)) OVER (PARTITION BY pillar)
        FROM score_items WHERE run_id = %(run)s GROUP BY 1, 2 ORDER BY 1, 3 DESC""", args).fetchall()
    top = conn.execute(f"""
        SELECT t.session, c.official_full_name, t.chamber, t.power, t.productivity
        FROM (SELECT *, row_number() OVER (PARTITION BY session ORDER BY power + productivity DESC) AS n
              FROM ({totals}) t) t
        JOIN critters c USING (bioguide_id) WHERE n <= 10 ORDER BY 1, n""", args).fetchall()
    return {"balance": balance, "even_scale": even_scale, "chamber_medians": chamber_medians,
            "composition": composition, "top": top}


def pricing_inputs(conn: psycopg.Connection, run_id: int, session: int, min_days: int,
                   prev_run: int | None = None, as_of=None) -> list[dict]:
    """Members seated on `as_of` (default: the first day of `session`), with what pricing
    needs: seats held that day (from `run_id`), and last session's participation and
    productivity rate. A new Congress seats its committees weeks after it convenes, so
    session 1 is priced as of a later date. Last
    session is session 1 of the same run, or, for session 1, session 2 of `prev_run`
    (a run scoring the previous Congress)."""
    if session == 1 and prev_run is None:
        raise ValueError("pricing session 1 needs a run of the previous Congress")
    prev_run, prev_session = (prev_run, 2) if session == 1 else (run_id, session - 1)
    return [dict(zip(("bioguide_id", "chamber", "up_for_election", "fec_ids", "seat_value",
                      "committee_value", "participation", "productivity_rate", "left_office"), row))
            for row in conn.execute("""
        WITH r AS (SELECT congress FROM score_runs WHERE run_id = %(run)s),
        s AS (SELECT coalesce(%(as_of)s::date, make_date(congress * 2 + 1787 + %(s)s - 1, 1, 3)) AS d,
                     make_date(congress * 2 + 1787 + %(s)s - 1, 1, 3) AS a,
                     make_date(congress * 2 + 1787 + %(s)s, 1, 3) AS b,
                     make_date(congress * 2 + 1787 + %(s)s - 2, 1, 3) AS pa FROM r),
        seated AS (
            SELECT DISTINCT ON (t.bioguide_id) t.bioguide_id, t.term_type, t.end_date
            FROM critter_terms t, s WHERE t.start_date <= s.d AND t.end_date > s.d
            ORDER BY t.bioguide_id, t.start_date DESC),
        served AS (
            SELECT t.bioguide_id, sum(least(t.end_date, s.a) - greatest(t.start_date, s.pa)) AS days
            FROM critter_terms t, s WHERE t.start_date < s.a AND t.end_date > s.pa GROUP BY 1),
        seats AS (
            SELECT bioguide_id, sum((detail->>'value')::float) AS value,
                   coalesce(sum((detail->>'value')::float) FILTER (WHERE category <> 'LEADERSHIP'), 0) AS committee
            FROM score_items, s WHERE run_id = %(run)s AND session = %(s)s AND pillar = 'power'
              AND item_date <= s.d AND s.d < item_date + (detail->>'days')::int GROUP BY 1),
        prev AS (
            SELECT bioguide_id,
                   sum((detail->>'participation')::float * (detail->>'days')::float)
                       / nullif(sum((detail->>'days')::float), 0) AS participation,
                   sum(points) FILTER (WHERE pillar = 'productivity') AS productivity
            FROM score_items WHERE run_id = %(prev_run)s AND session = %(prev_s)s GROUP BY 1)
        SELECT x.bioguide_id, CASE x.term_type WHEN 'sen' THEN 'sen' ELSE 'rep' END,
               x.end_date <= s.b, c.fec_ids, coalesce(seats.value, 0), coalesce(seats.committee, 0),
               prev.participation,
               CASE WHEN served.days >= %(min)s
                    THEN coalesce(prev.productivity, 0) * (s.a - s.pa) / served.days END,
               (SELECT max(end_date) FROM critter_terms t WHERE t.bioguide_id = x.bioguide_id)
        FROM seated x CROSS JOIN s JOIN critters c USING (bioguide_id)
        LEFT JOIN seats USING (bioguide_id) LEFT JOIN served USING (bioguide_id)
        LEFT JOIN prev USING (bioguide_id)""",
        {"run": run_id, "s": session, "min": min_days, "prev_run": prev_run, "prev_s": prev_session,
         "as_of": as_of})]


def session_points(conn: psycopg.Connection, run_id: int, session: int) -> dict[str, float]:
    return dict(conn.execute(
        "SELECT bioguide_id, sum(points) FROM score_items WHERE run_id = %s AND session = %s GROUP BY 1",
        (run_id, session)).fetchall())


def save_prices(conn: psycopg.Connection, run_id: int, session: int, fec_cycle: int, prices) -> None:
    conn.execute("DELETE FROM critter_prices WHERE run_id = %s AND session = %s", (run_id, session))
    with conn.cursor().copy(
        """COPY critter_prices (run_id, session, fec_cycle, bioguide_id, chamber, projected_power,
               projected_productivity, multiplier, session_cost, signing_fee, weekly_fee) FROM STDIN"""
    ) as copy:
        for p in prices:
            copy.write_row((run_id, session, fec_cycle, p.bioguide_id, p.chamber, p.projected_power,
                            p.projected_productivity, p.multiplier, p.session_cost, p.signing_fee,
                            p.weekly_fee))
    conn.commit()


def seated_on(conn: psycopg.Connection, day) -> dict[str, str]:
    """bioguide -> chamber (rep | sen) for members in office on `day`."""
    return dict(conn.execute("""
        SELECT DISTINCT ON (bioguide_id) bioguide_id, CASE term_type WHEN 'sen' THEN 'sen' ELSE 'rep' END
        FROM critter_terms WHERE start_date <= %(d)s AND end_date > %(d)s
        ORDER BY bioguide_id, start_date DESC""", {"d": day}).fetchall())


def majority_sides(conn: psycopg.Connection, day) -> dict[str, str]:
    """chamber -> the caucus holding most seats on `day`."""
    rows = conn.execute("""
        WITH seated AS (
            SELECT DISTINCT ON (t.bioguide_id) t.bioguide_id, t.term_type
            FROM critter_terms t WHERE t.start_date <= %(d)s AND t.end_date > %(d)s
            ORDER BY t.bioguide_id, t.start_date DESC),
        side AS (
            SELECT DISTINCT ON (p.bioguide_id) p.bioguide_id, coalesce(p.caucus, p.party) AS side
            FROM critter_parties p WHERE p.start_date <= %(d)s ORDER BY p.bioguide_id, p.start_date DESC)
        SELECT CASE term_type WHEN 'sen' THEN 'sen' ELSE 'rep' END, side, count(*)
        FROM seated JOIN side USING (bioguide_id) GROUP BY 1, 2 ORDER BY 1, 3 DESC""", {"d": day}).fetchall()
    out: dict[str, str] = {}
    for chamber, side, _ in rows:
        out.setdefault(chamber, side)
    return out


def senators_on(conn: psycopg.Connection, day) -> list[Senator]:
    """Senators in office on `day`, with the first letter of the caucus they sit with."""
    return [Senator(*row) for row in conn.execute("""
        SELECT DISTINCT ON (t.bioguide_id) t.bioguide_id, t.state, c.last_name,
               left((SELECT coalesce(p.caucus, p.party) FROM critter_parties p
                     WHERE p.bioguide_id = t.bioguide_id AND p.start_date <= %(d)s
                     ORDER BY p.start_date DESC LIMIT 1), 1)
        FROM critter_terms t JOIN critters c USING (bioguide_id)
        WHERE t.term_type = 'sen' AND t.start_date <= %(d)s AND t.end_date >= %(d)s
        ORDER BY t.bioguide_id, t.start_date DESC""", {"d": day})]


def held_seats(conn: psycopg.Connection, run_id: int, session: int, day) -> list[tuple]:
    """Committee and subcommittee seats held on `day`: (bioguide, chamber, category, role, value)."""
    return conn.execute("""
        SELECT bioguide_id, detail->>'chamber', category, detail->>'role', (detail->>'value')::float
        FROM score_items WHERE run_id = %(run)s AND session = %(s)s
          AND category IN ('COMMITTEE_SEAT', 'SUBCOMMITTEE_SEAT')
          AND item_date <= %(d)s AND %(d)s::date < item_date + (detail->>'days')::int""",
        {"run": run_id, "s": session, "d": day}).fetchall()


def freshmen(conn: psycopg.Connection, start, end) -> set[str]:
    """Members whose first term in their chamber began in [start, end)."""
    return {row[0] for row in conn.execute("""
        SELECT bioguide_id FROM critter_terms GROUP BY bioguide_id, term_type
        HAVING min(start_date) >= %s AND min(start_date) < %s""", (start, end))}


def save_preset(conn: psycopg.Connection, name: str, description: str | None, settings: dict, by: str) -> None:
    conn.execute("""
        INSERT INTO league_presets (name, description, settings, authored_by) VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET description = excluded.description, settings = excluded.settings,
            authored_by = excluded.authored_by, updated_at = now()""",
        (name, description, Jsonb(settings), by))
    conn.commit()


def presets(conn: psycopg.Connection) -> dict[str, dict]:
    return {name: {"description": desc, "settings": settings, "authored_by": by, "updated_at": at}
            for name, desc, settings, by, at in conn.execute(
                "SELECT name, description, settings, authored_by, updated_at FROM league_presets ORDER BY name")}


LEAGUE_COLUMNS = ("league_id", "name", "league_type", "visibility", "start_date", "end_date",
                  "ruleset_version", "ruleset", "preset", "settings", "created_by", "creator_role",
                  "created_at", "updated_at")


def create_league(conn: psycopg.Connection, **league) -> int:
    cols = [c for c in LEAGUE_COLUMNS if c in league]
    values = [Jsonb(league[c]) if c in ("ruleset", "settings") else league[c] for c in cols]
    league_id = conn.execute(
        f"INSERT INTO leagues ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) RETURNING league_id",
        values).fetchone()[0]
    conn.commit()
    return league_id


def leagues(conn: psycopg.Connection, league_id: int | None = None) -> list[dict]:
    rows = conn.execute(
        f"SELECT {', '.join(LEAGUE_COLUMNS)} FROM leagues"
        + (" WHERE league_id = %s" if league_id else "") + " ORDER BY league_id",
        (league_id,) if league_id else ()).fetchall()
    return [dict(zip(LEAGUE_COLUMNS, row)) for row in rows]


def update_league(conn: psycopg.Connection, league_id: int, settings: dict,
                  ruleset_version: str, ruleset: dict) -> None:
    conn.execute("""UPDATE leagues SET settings = %s, ruleset_version = %s, ruleset = %s, updated_at = now()
                    WHERE league_id = %s""", (Jsonb(settings), ruleset_version, Jsonb(ruleset), league_id))
    conn.commit()


def league_run(conn: psycopg.Connection, ruleset: dict, congress: int) -> int | None:
    """The latest run scoring `congress` with exactly this ruleset."""
    return conn.execute("SELECT max(run_id) FROM score_runs WHERE congress = %s AND ruleset = %s",
                        (congress, Jsonb(ruleset))).fetchone()[0]


def join_league(conn: psycopg.Connection, league_id: int, player: str, day) -> int:
    roster_id = conn.execute(
        "INSERT INTO rosters (league_id, player, joined_on) VALUES (%s, %s, %s) RETURNING roster_id",
        (league_id, player, day)).fetchone()[0]
    conn.commit()
    return roster_id


ROSTER_COLUMNS = ("roster_id", "league_id", "player", "joined_on")


def rosters(conn: psycopg.Connection, league_id: int, player: str | None = None) -> list[dict]:
    rows = conn.execute(
        f"SELECT {', '.join(ROSTER_COLUMNS)} FROM rosters WHERE league_id = %s"
        + (" AND player = %s" if player else "") + " ORDER BY roster_id",
        (league_id, player) if player else (league_id,)).fetchall()
    return [dict(zip(ROSTER_COLUMNS, row)) for row in rows]


def lock_roster(conn: psycopg.Connection, roster_id: int) -> None:
    """Hold a roster until the transaction ends, so trades on it happen one at a time."""
    conn.execute("SELECT 1 FROM rosters WHERE roster_id = %s FOR UPDATE", (roster_id,))


def last_transaction(conn: psycopg.Connection, roster_id: int):
    return conn.execute("SELECT max(made_on) FROM transactions WHERE roster_id = %s", (roster_id,)).fetchone()[0]


def critter_price(conn: psycopg.Connection, run_id: int, session: int, bioguide: str) -> dict | None:
    row = conn.execute("""SELECT chamber, session_cost, signing_fee, weekly_fee FROM critter_prices
                          WHERE run_id = %s AND session = %s AND bioguide_id = %s""",
                       (run_id, session, bioguide)).fetchone()
    return dict(zip(("chamber", "session_cost", "signing_fee", "weekly_fee"), row)) if row else None


def priced(conn: psycopg.Connection, run_id: int, session: int) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT bioguide_id FROM critter_prices WHERE run_id = %s AND session = %s", (run_id, session))]


def service_end(conn: psycopg.Connection, bioguide: str, day):
    """When the service that includes `day` ends (exclusive), following back-to-back terms;
    None if the critter is not in office on `day`."""
    end = None
    for start, term_end in conn.execute(
            "SELECT start_date, end_date FROM critter_terms WHERE bioguide_id = %s ORDER BY start_date",
            (bioguide,)):
        if end is None:
            if start <= day < term_end:
                end = term_end
        elif start <= end:
            end = max(end, term_end)
    return end


def holdings(conn: psycopg.Connection, roster_id: int, congress: int, session) -> list[Holding]:
    """A roster's purchases for a session (scoring.Session), with their drops."""
    out = []
    for row in conn.execute("""
            SELECT p.txn_id, p.bioguide_id, p.chamber, p.made_on, p.week, p.last_week, p.session_cost,
                   p.signing_fee, p.weekly_fee, d.made_on, d.week, d.extra_fee, d.points_penalty
            FROM transactions p LEFT JOIN transactions d ON d.purchase_id = p.txn_id
            WHERE p.roster_id = %s AND p.kind = 'purchase' AND p.congress = %s AND p.session = %s
            ORDER BY p.txn_id""", (roster_id, congress, session.number)).fetchall():
        (txn_id, bioguide, chamber, made_on, first, last, cost, signing, weekly,
         dropped_on, drop_week, extra_fee, penalty) = row
        end = service_end(conn, bioguide, max(made_on, session.start))
        out.append(Holding(bioguide, chamber, made_on, first, last, cost, signing, weekly,
                           left_office=end if end and end < session.end else None,
                           dropped_on=dropped_on, drop_week=drop_week, extra_fee=extra_fee or 0,
                           points_penalty=penalty or 0.0, txn_id=txn_id))
    return out


def record_purchase(conn: psycopg.Connection, roster_id: int, congress: int, session: int, run_id: int, h) -> int:
    txn_id = conn.execute("""
        INSERT INTO transactions (roster_id, kind, bioguide_id, congress, session, made_on, week, price_run,
                                  chamber, session_cost, signing_fee, weekly_fee, last_week)
        VALUES (%s, 'purchase', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING txn_id""",
        (roster_id, h.bioguide_id, congress, session, h.made_on, h.first_week, run_id, h.chamber,
         h.session_cost, h.signing_fee, h.weekly_fee, h.last_week)).fetchone()[0]
    conn.commit()
    return txn_id


def record_drop(conn: psycopg.Connection, roster_id: int, congress: int, session: int, h) -> int:
    txn_id = conn.execute("""
        INSERT INTO transactions (roster_id, kind, bioguide_id, congress, session, made_on, week, purchase_id,
                                  extra_fee, points_penalty)
        VALUES (%s, 'drop', %s, %s, %s, %s, %s, %s, %s, %s) RETURNING txn_id""",
        (roster_id, h.bioguide_id, congress, session, h.dropped_on, h.drop_week, h.txn_id,
         h.extra_fee, h.points_penalty)).fetchone()[0]
    conn.commit()
    return txn_id


def roster_weekly_points(conn: psycopg.Connection, run_id: int, session: int,
                         bioguides: list[str]) -> dict[tuple[str, int], tuple[float, float]]:
    return {(b, w): (p, q) for b, w, p, q in conn.execute(
        """SELECT bioguide_id, week, power, productivity FROM weekly_points
           WHERE run_id = %s AND session = %s AND bioguide_id = ANY(%s)""", (run_id, session, bioguides))}


def names(conn: psycopg.Connection, bioguides: list[str] | None = None) -> dict[str, str]:
    """bioguide -> official full name, of these critters or all of them."""
    return dict(conn.execute(
        "SELECT bioguide_id, official_full_name FROM critters WHERE %(b)s::text[] IS NULL OR bioguide_id = ANY(%(b)s)",
        {"b": bioguides}).fetchall())


def find_critters(conn: psycopg.Connection, text: str, among: list[str] | None = None) -> list[tuple[str, str]]:
    """(bioguide, name) of critters whose bioguide is `text`, or whose name contains it."""
    rows = conn.execute("""
        SELECT bioguide_id, official_full_name FROM critters
        WHERE (bioguide_id = upper(%(t)s) OR official_full_name ILIKE '%%' || %(t)s || '%%')
          AND (%(among)s::text[] IS NULL OR bioguide_id = ANY(%(among)s))
        ORDER BY bioguide_id = upper(%(t)s) DESC, official_full_name""", {"t": text, "among": among}).fetchall()
    exact = [r for r in rows if r[0] == text.upper()]
    return exact or rows


def price_run(conn: psycopg.Connection, ruleset: dict, congress: int, session: int) -> int | None:
    """The latest run scoring `congress` with this ruleset that has prices for `session`.
    Live runs replace each other daily; prices stay with the run they were made from."""
    return conn.execute("""
        SELECT max(r.run_id) FROM score_runs r
        WHERE r.congress = %s AND r.ruleset = %s
          AND EXISTS (SELECT 1 FROM critter_prices p WHERE p.run_id = r.run_id AND p.session = %s)""",
                        (congress, Jsonb(ruleset), session)).fetchone()[0]


def record_sync(conn: psycopg.Connection, source: str, congress: int | None, started_at, ok: bool,
                changed: int = 0, latest=None, note: str | None = None) -> None:
    conn.execute("""INSERT INTO source_syncs (source, congress, started_at, finished_at, ok, changed, latest, note)
                    VALUES (%s, %s, %s, now(), %s, %s, %s, %s)""",
                 (source, congress, started_at, ok, changed, latest, note))
    conn.commit()


def last_synced(conn: psycopg.Connection, congress: int) -> dict[str, object]:
    """source -> when it last synced successfully for `congress` (or for every Congress)."""
    return dict(conn.execute("""
        SELECT source, max(finished_at) FROM source_syncs
        WHERE ok AND (congress = %s OR congress IS NULL) GROUP BY source""", (congress,)).fetchall())


def sync_status(conn: psycopg.Connection) -> list[tuple]:
    """Per source and Congress: the last attempt (when, ok, note), the last success and the
    newest data it held."""
    return conn.execute("""
        SELECT DISTINCT ON (source, congress) source, congress, finished_at, ok, note,
               (SELECT max(finished_at) FROM source_syncs o
                WHERE o.ok AND o.source = s.source AND o.congress IS NOT DISTINCT FROM s.congress),
               (SELECT max(latest) FROM source_syncs o
                WHERE o.ok AND o.source = s.source AND o.congress IS NOT DISTINCT FROM s.congress)
        FROM source_syncs s ORDER BY source, congress, finished_at DESC""").fetchall()


def bill_update_dates(conn: psycopg.Connection, congress: int) -> dict:
    return dict(conn.execute("SELECT bill_id, update_date FROM bills WHERE congress = %s", (congress,)).fetchall())


def roll_numbers(conn: psycopg.Connection, chamber: str, congress: int, session: int) -> set[int]:
    return {r[0] for r in conn.execute(
        "SELECT roll_number FROM roll_calls WHERE chamber = %s AND congress = %s AND session = %s",
        (chamber, congress, session))}


def latest_vote(conn: psycopg.Connection, chamber: str, congress: int):
    return conn.execute("SELECT max(vote_date) FROM roll_calls WHERE chamber = %s AND congress = %s",
                        (chamber, congress)).fetchone()[0]


def missing_roll_calls(conn: psycopg.Connection, congress: int, session: int, before) -> list[str]:
    """Roll calls that bill actions before `before` cite but that aren't loaded: votes a
    source hasn't published yet."""
    return [r[0] for r in conn.execute("""
        SELECT DISTINCT (v->>'chamber') || ' ' || (v->>'roll_number')
        FROM bill_actions a JOIN bills b USING (bill_id), jsonb_array_elements(a.recorded_votes) v
        WHERE b.congress = %(c)s AND (v->>'congress')::int = %(c)s AND (v->>'session')::int = %(s)s
          AND a.action_date < %(d)s
          AND NOT EXISTS (SELECT 1 FROM roll_calls rc
                          WHERE rc.chamber = v->>'chamber' AND rc.congress = %(c)s AND rc.session = %(s)s
                            AND rc.roll_number = (v->>'roll_number')::int)
        ORDER BY 1""", {"c": congress, "s": session, "d": before})]


def prune_live_runs(conn: psycopg.Connection, ruleset: dict, congress: int, keep: int) -> list[int]:
    """Delete live runs of `congress` with this ruleset older than `keep`, unless prices or
    purchases point at them."""
    gone = [r[0] for r in conn.execute("""
        DELETE FROM score_runs r
        WHERE r.live AND r.congress = %s AND r.ruleset = %s AND r.run_id < %s
          AND NOT EXISTS (SELECT 1 FROM critter_prices p WHERE p.run_id = r.run_id)
          AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.price_run = r.run_id)
        RETURNING r.run_id""", (congress, Jsonb(ruleset), keep))]
    conn.commit()
    return gone


def settled_weeks(conn: psycopg.Connection, ruleset: dict, congress: int, session: int) -> set[int]:
    return {r[0] for r in conn.execute("""
        SELECT week FROM settled_weeks
        WHERE ruleset_key = md5(%s::jsonb::text) AND congress = %s AND session = %s""",
                                       (Jsonb(ruleset), congress, session))}


def settle_week(conn: psycopg.Connection, ruleset: dict, congress: int, session: int, week: int,
                run_id: int) -> int:
    """Freeze a week's points from `run_id`; returns how many critters scored in it."""
    key = conn.execute("SELECT md5(%s::jsonb::text)", (Jsonb(ruleset),)).fetchone()[0]
    conn.execute("""INSERT INTO settled_weeks (ruleset_key, congress, session, week, run_id)
                    VALUES (%s, %s, %s, %s, %s)""", (key, congress, session, week, run_id))
    n = conn.execute("""
        INSERT INTO settled_points (ruleset_key, congress, session, week, bioguide_id, power, productivity)
        SELECT %s, %s, session, week, bioguide_id, power, productivity FROM weekly_points
        WHERE run_id = %s AND session = %s AND week = %s""",
                     (key, congress, run_id, session, week)).rowcount
    conn.commit()
    return n


def settled_points(conn: psycopg.Connection, ruleset: dict, congress: int, session: int,
                   bioguides: list[str]) -> dict[tuple[str, int], tuple[float, float]]:
    return {(b, w): (p, q) for b, w, p, q in conn.execute("""
        SELECT bioguide_id, week, power, productivity FROM settled_points
        WHERE ruleset_key = md5(%s::jsonb::text) AND congress = %s AND session = %s
          AND bioguide_id = ANY(%s)""", (Jsonb(ruleset), congress, session, bioguides))}


def drift(conn: psycopg.Connection, run_id: int) -> list[tuple]:
    """Settled weeks whose points the run would now score differently, which settlement keeps
    out (Design-Data §10.4): (session, week, critters changed, net points, absolute points)."""
    return conn.execute("""
        WITH run AS (SELECT congress, md5(ruleset::text) AS key FROM score_runs WHERE run_id = %(r)s),
        settled AS (
            SELECT p.session, p.week, p.bioguide_id, p.power + p.productivity AS points
            FROM settled_points p JOIN run ON p.ruleset_key = run.key AND p.congress = run.congress),
        now AS (
            SELECT w.session, w.week, w.bioguide_id, w.power + w.productivity AS points
            FROM weekly_points w
            WHERE w.run_id = %(r)s AND (w.session, w.week) IN (
                SELECT s.session, s.week FROM settled_weeks s JOIN run
                ON s.ruleset_key = run.key AND s.congress = run.congress))
        SELECT session, week, count(*), sum(coalesce(n.points, 0) - coalesce(s.points, 0)),
               sum(abs(coalesce(n.points, 0) - coalesce(s.points, 0)))
        FROM settled s FULL JOIN now n USING (session, week, bioguide_id)
        WHERE abs(coalesce(n.points, 0) - coalesce(s.points, 0)) > 1e-6
        GROUP BY session, week ORDER BY session, week""", {"r": run_id}).fetchall()


def live_runs(conn: psycopg.Connection) -> list[tuple]:
    """Each live run, with how far each of its sessions has settled: (run, congress,
    ruleset version, created, [(session, last settled week)])."""
    rows = conn.execute("""
        SELECT r.run_id, r.congress, r.ruleset_version, r.created_at, s.session, max(s.week)
        FROM score_runs r LEFT JOIN settled_weeks s ON s.ruleset_key = md5(r.ruleset::text) AND s.congress = r.congress
        WHERE r.live GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 5""").fetchall()
    out: dict[int, tuple] = {}
    for run_id, congress, version, created, session, week in rows:
        out.setdefault(run_id, (run_id, congress, version, created, []))
        if session is not None:
            out[run_id][4].append((session, week))
    return list(out.values())


def _rows(cur) -> list[dict]:
    names = [c.name for c in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def critter_cards(conn: psycopg.Connection, bioguides: list[str] | None, day) -> dict[str, dict]:
    """bioguide -> name, chamber, state, district and party of the term held on `day`, or the
    last one before it."""
    return {r["bioguide_id"]: r for r in _rows(conn.execute("""
        SELECT DISTINCT ON (c.bioguide_id) c.bioguide_id, c.official_full_name AS name,
               CASE t.term_type WHEN 'sen' THEN 'sen' ELSE 'rep' END AS chamber, t.state, t.district,
               coalesce((SELECT p.party FROM critter_parties p
                         WHERE p.bioguide_id = c.bioguide_id AND p.start_date <= %(d)s
                         ORDER BY p.start_date DESC LIMIT 1), t.party) AS party
        FROM critters c JOIN critter_terms t USING (bioguide_id)
        WHERE (%(b)s::text[] IS NULL OR c.bioguide_id = ANY(%(b)s)) AND t.start_date <= %(d)s
        ORDER BY c.bioguide_id, t.start_date DESC""", {"b": bioguides, "d": day}))}


def market_prices(conn: psycopg.Connection, run_id: int, session: int) -> list[dict]:
    return _rows(conn.execute("""
        SELECT bioguide_id, chamber, session_cost, signing_fee, weekly_fee, projected_power,
               projected_productivity, multiplier
        FROM critter_prices WHERE run_id = %s AND session = %s ORDER BY session_cost DESC""", (run_id, session)))


def owners(conn: psycopg.Connection, league_id: int, congress: int, session: int, day) -> dict[str, list[str]]:
    """bioguide -> players in the league holding the critter on `day` (bought, not dropped)."""
    out: dict[str, list[str]] = {}
    for bioguide, player in conn.execute("""
            SELECT p.bioguide_id, r.player FROM transactions p JOIN rosters r USING (roster_id)
            WHERE r.league_id = %(l)s AND p.kind = 'purchase' AND p.congress = %(c)s AND p.session = %(s)s
              AND p.made_on <= %(d)s
              AND NOT EXISTS (SELECT 1 FROM transactions d WHERE d.purchase_id = p.txn_id AND d.made_on <= %(d)s)
            ORDER BY r.player""", {"l": league_id, "c": congress, "s": session, "d": day}):
        out.setdefault(bioguide, []).append(player)
    return out


def critter(conn: psycopg.Connection, bioguide: str) -> dict | None:
    """A critter's identity, terms, party changes and leadership posts."""
    row = _rows(conn.execute("""
        SELECT bioguide_id, official_full_name AS name, first_name, last_name, birthday,
               govtrack_id, wikidata_id, fec_ids FROM critters WHERE bioguide_id = %s""", (bioguide,)))
    if not row:
        return None
    out = row[0]
    out["terms"] = _rows(conn.execute("""
        SELECT CASE term_type WHEN 'sen' THEN 'sen' ELSE 'rep' END AS chamber, start_date, end_date, state,
               district, senate_class, party
        FROM critter_terms WHERE bioguide_id = %s ORDER BY start_date DESC""", (bioguide,)))
    out["leadership"] = _rows(conn.execute("""
        SELECT chamber, title, start_date, end_date FROM critter_leadership
        WHERE bioguide_id = %s ORDER BY start_date DESC""", (bioguide,)))
    return out


def critter_points(conn: psycopg.Connection, run_id: int, session: int, bioguide: str, before) -> dict:
    """What a critter's points in a run's session came from, counting items dated before
    `before` (the end of the last week that has ended): productivity by category and by
    bill, the positions behind power, and roll-call participation."""
    args = {"r": run_id, "s": session, "b": bioguide, "d": before}
    categories = _rows(conn.execute("""
        SELECT category, count(*) AS items, sum(points) AS points FROM score_items
        WHERE run_id = %(r)s AND session = %(s)s AND bioguide_id = %(b)s AND pillar = 'productivity'
          AND item_date < %(d)s
        GROUP BY 1 ORDER BY 3 DESC""", args))
    bills = _rows(conn.execute("""
        SELECT i.bill_id, b.title, sum(i.points) AS points, array_agg(DISTINCT i.category) AS categories,
               b.sponsor_id = %(b)s AS sponsor
        FROM score_items i JOIN bills b USING (bill_id)
        WHERE i.run_id = %(r)s AND i.session = %(s)s AND i.bioguide_id = %(b)s AND i.item_date < %(d)s
        GROUP BY 1, 2, b.sponsor_id ORDER BY 3 DESC LIMIT 25""", args))
    positions = _rows(conn.execute("""
        SELECT i.category, i.committee_code, coalesce(c.name, i.detail->>'key') AS name, i.detail->>'role' AS role,
               i.item_date AS start_date, i.item_date + (i.detail->>'days')::int - 1 AS end_date,
               (i.detail->>'value')::float AS value
        FROM score_items i LEFT JOIN committees c USING (committee_code)
        WHERE i.run_id = %(r)s AND i.session = %(s)s AND i.bioguide_id = %(b)s AND i.pillar = 'power'
        ORDER BY 7 DESC""", args))
    participation = conn.execute("""
        SELECT sum((detail->>'participation')::float * (detail->>'days_seated')::int)
               / nullif(sum((detail->>'days_seated')::int), 0)
        FROM score_items WHERE run_id = %(r)s AND session = %(s)s AND bioguide_id = %(b)s
          AND category = 'VOTE_CAST' AND item_date < %(d)s""", args).fetchone()[0]
    return {"categories": categories, "bills": bills, "positions": positions, "participation": participation}
