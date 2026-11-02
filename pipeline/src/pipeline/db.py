from collections.abc import Iterable
from importlib.resources import files

import psycopg
from psycopg.types.json import Jsonb

from .billstatus import Bill
from .config import DATABASE_URL
from .normalize import Event


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(files("pipeline").joinpath("schema.sql").read_text())
    conn.commit()


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
              a.source_name, a.committee_codes,
              Jsonb([{"chamber": v.chamber, "congress": v.congress, "session": v.session,
                      "roll_number": v.roll_number} for v in a.recorded_votes]))
             for a in bill.actions],
        )
        cur.executemany(
            """INSERT INTO events (bill_id, event_type, event_date, chamber, committee_code,
                   critter_id, source, detail)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            [(e.bill_id, e.event_type, e.event_date, e.chamber, e.committee_code, e.critter_id,
              e.source, e.detail) for e in events],
        )
