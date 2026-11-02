"""Load members, terms, and committees from the unitedstates/congress-legislators dataset."""

from datetime import date
from pathlib import Path

import psycopg
import yaml

from .download import legislators_path


def _load(path: Path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.CSafeLoader)


def _date(value) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def load_critters(conn: psycopg.Connection) -> int:
    people = _load(legislators_path("legislators-historical.yaml"))
    people += _load(legislators_path("legislators-current.yaml"))
    with conn.cursor() as cur:
        cur.execute("TRUNCATE critters CASCADE")
        for person in people:
            ids, name = person["id"], person.get("name", {})
            bioguide = ids.get("bioguide")
            if not bioguide:
                continue
            cur.execute(
                """INSERT INTO critters (bioguide_id, first_name, last_name, official_full_name,
                       birthday, govtrack_id, thomas_id, lis_id, wikidata_id, fec_ids)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (bioguide, name.get("first"), name.get("last"), name.get("official_full"),
                 _date(person.get("bio", {}).get("birthday")), ids.get("govtrack"),
                 ids.get("thomas"), ids.get("lis"), ids.get("wikidata"), ids.get("fec", [])),
            )
            cur.executemany(
                """INSERT INTO critter_terms (bioguide_id, term_type, start_date, end_date, state,
                       district, senate_class, party)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                [(bioguide, t["type"], _date(t["start"]), _date(t["end"]), t["state"],
                  t.get("district"), t.get("class"), t.get("party"))
                 for t in person.get("terms", [])],
            )
    conn.commit()
    return len(people)


def load_committees(conn: psycopg.Connection) -> int:
    rows = []
    for name, is_current in (("committees-historical.yaml", False), ("committees-current.yaml", True)):
        for committee in _load(legislators_path(name)):
            code = committee["thomas_id"].lower() + "00"
            rows.append((code, None, committee["name"], committee.get("type"), is_current))
            for sub in committee.get("subcommittees", []):
                sub_code = committee["thomas_id"].lower() + sub["thomas_id"]
                rows.append((sub_code, code, sub["name"], committee.get("type"), is_current))
    with conn.cursor() as cur:
        cur.execute("TRUNCATE committees")
        # Current entries come last and win.
        cur.executemany(
            """INSERT INTO committees (committee_code, parent_committee_code, name, chamber, is_current)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (committee_code) DO UPDATE SET name = EXCLUDED.name,
                   parent_committee_code = EXCLUDED.parent_committee_code,
                   chamber = EXCLUDED.chamber, is_current = EXCLUDED.is_current""",
            rows,
        )
    conn.commit()
    return len(rows)
