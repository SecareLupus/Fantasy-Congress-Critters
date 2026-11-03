"""Load members, terms, and committees from the unitedstates/congress-legislators dataset."""

from datetime import date, timedelta
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


def party_periods(term: dict) -> list[tuple[date, date, str | None, str | None]]:
    """(start, end inclusive, party, caucus) over a term.

    A term's own party is the one it ended with; a member who switched mid-term has
    party_affiliations. The source either ends an affiliation on the day the next one
    starts or the day before; the day of the switch goes to the new party.
    """
    affiliations = term.get("party_affiliations") or [term]
    periods = []
    for i, a in enumerate(affiliations):
        end = _date(a["end"])
        if i + 1 < len(affiliations):
            end = min(end, _date(affiliations[i + 1]["start"]) - timedelta(days=1))
        periods.append((_date(a["start"]), end, a.get("party"), a.get("caucus")))
    return periods


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
            cur.executemany(
                """INSERT INTO critter_parties (bioguide_id, start_date, end_date, party, caucus)
                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                [(bioguide, *period) for t in person.get("terms", []) for period in party_periods(t)],
            )
            cur.executemany(
                """INSERT INTO critter_leadership (bioguide_id, chamber, title, start_date, end_date)
                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                [(bioguide, r["chamber"], r["title"], _date(r["start"]), _date(r.get("end")))
                 for r in person.get("leadership_roles", [])],
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
