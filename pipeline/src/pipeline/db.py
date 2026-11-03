from collections.abc import Iterable
from importlib.resources import files

import psycopg
from psycopg.types.json import Jsonb

from .billstatus import Action, Bill
from .config import DATABASE_URL
from .normalize import Event
from .rosters import Membership
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


def save_score_run(conn: psycopg.Connection, congress: int, ruleset, items) -> int:
    run_id = conn.execute(
        "INSERT INTO score_runs (congress, ruleset_version, ruleset) VALUES (%s, %s, %s) RETURNING run_id",
        (congress, ruleset.version, Jsonb(ruleset.raw)),
    ).fetchone()[0]
    with conn.cursor().copy(
        """COPY score_items (run_id, bioguide_id, session, pillar, category, item_date, points,
               bill_id, amendment_id, vote_id, committee_code, detail) FROM STDIN"""
    ) as copy:
        for i in items:
            copy.write_row((run_id, i.bioguide_id, i.session, i.pillar, i.category, i.item_date,
                            i.points, i.bill_id, i.amendment_id, i.vote_id, i.committee_code,
                            Jsonb(i.detail) if i.detail else None))
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


def delegates(conn: psycopg.Connection) -> frozenset[str]:
    """Members who have served as a delegate or the Resident Commissioner."""
    from .scoring import NON_VOTING_STATES
    return frozenset(row[0] for row in conn.execute(
        "SELECT DISTINCT bioguide_id FROM critter_terms WHERE term_type = 'rep' AND state = ANY(%s)",
        (list(NON_VOTING_STATES),)))
