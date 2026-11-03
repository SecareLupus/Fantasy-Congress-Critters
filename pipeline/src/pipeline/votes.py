"""Parse roll-call vote records.

House: one Clerk XML file per roll call (clerk.house.gov/evs/{year}/roll{NNN}.xml).
Members are identified by bioguide ID. Delegates and the Resident Commissioner vote
in the Committee of the Whole (mostly amendments); the Clerk gives them state "XX".

Senate: Voteview CSVs (rollcalls, votes, members) per Congress, because senate.gov
blocks automated downloads. Members are identified by ICPSR and mapped to bioguide
through the members file. Voteview also records the President's stated position;
it is skipped.
"""

import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path

# Measure prefixes with spaces removed: House "H J RES 9", Voteview "HJRES9".
# Nominations (PN) and treaties (TREATYDOC) are not bills.
LEGIS_TYPES = {
    "HR": "hr",
    "HRES": "hres",
    "HJRES": "hjres",
    "HCONRES": "hconres",
    "S": "s",
    "SRES": "sres",
    "SJRES": "sjres",
    "SCONRES": "sconres",
}
LEGIS_NUM = re.compile(r"^([A-Z ]+?)\s*(\d+)$")

POSITIONS = {
    "yea": "yea",
    "aye": "yea",
    "nay": "nay",
    "no": "nay",
    "present": "present",
    "not voting": "not_voting",
}


@dataclass
class MemberVote:
    bioguide_id: str
    position: str  # yea, nay, present, not_voting, or other (e.g. a name in a Speaker election)
    raw_position: str
    party: str | None
    state: str | None


@dataclass
class RollCall:
    chamber: str
    congress: int
    session: int
    roll_number: int
    vote_date: date
    vote_time: time | None
    question: str | None
    vote_type: str | None
    result: str | None
    legis_num: str | None
    bill_id: str | None
    amendment_num: str | None
    amendment_author: str | None
    description: str | None
    members: list[MemberVote] = field(default_factory=list)

    @property
    def vote_id(self) -> str:
        return f"{self.congress}-{self.chamber[0].lower()}{self.session}-{self.roll_number}"


def _text(el: ET.Element | None, tag: str) -> str | None:
    if el is None:
        return None
    value = el.findtext(tag)
    return value.strip() if value and value.strip() else None


def position_category(raw: str) -> str:
    return POSITIONS.get(raw.strip().lower(), "other")


def legis_bill_id(congress: int, legis_num: str | None) -> str | None:
    if not legis_num:
        return None
    match = LEGIS_NUM.match(legis_num.strip().upper())
    prefix = match.group(1).replace(" ", "") if match else None
    if prefix not in LEGIS_TYPES:
        return None
    return f"{congress}-{LEGIS_TYPES[prefix]}-{int(match.group(2))}"


def parse_house_vote(xml: bytes) -> RollCall:
    root = ET.fromstring(xml)
    meta = root.find("vote-metadata")
    congress = int(_text(meta, "congress"))
    time_el = meta.find("action-time")
    etz = time_el.get("time-etz") if time_el is not None else None

    roll_call = RollCall(
        chamber="House",
        congress=congress,
        session=int(re.match(r"\d+", _text(meta, "session")).group()),
        roll_number=int(_text(meta, "rollcall-num")),
        vote_date=datetime.strptime(_text(meta, "action-date"), "%d-%b-%Y").date(),
        vote_time=datetime.strptime(etz, "%H:%M").time() if etz else None,
        question=_text(meta, "vote-question"),
        vote_type=_text(meta, "vote-type"),
        result=_text(meta, "vote-result"),
        legis_num=_text(meta, "legis-num"),
        bill_id=legis_bill_id(congress, _text(meta, "legis-num")),
        amendment_num=_text(meta, "amendment-num"),
        amendment_author=_text(meta, "amendment-author"),
        description=_text(meta, "vote-desc"),
    )
    for rv in root.iterfind("vote-data/recorded-vote"):
        legislator = rv.find("legislator")
        raw = (rv.findtext("vote") or "").strip()
        roll_call.members.append(
            MemberVote(
                bioguide_id=legislator.get("name-id"),
                position=position_category(raw),
                raw_position=raw,
                party=legislator.get("party"),
                state=None if legislator.get("state") == "XX" else legislator.get("state"),
            )
        )
    return roll_call


def iter_house_votes(directory: Path):
    for path in sorted(directory.glob("roll*.xml")):
        yield parse_house_vote(path.read_bytes())


# Voteview cast codes. Paired and announced positions were not cast and are not in
# the tally, so they count as not voting; the raw text keeps the stated side.
VOTEVIEW_CAST = {
    "1": ("yea", "Yea"),
    "2": ("not_voting", "Paired Yea"),
    "3": ("not_voting", "Announced Yea"),
    "4": ("not_voting", "Announced Nay"),
    "5": ("not_voting", "Paired Nay"),
    "6": ("nay", "Nay"),
    "7": ("present", "Present"),
    "8": ("present", "Present"),
    "9": ("not_voting", "Not Voting"),
}
VOTEVIEW_PARTY = {"100": "D", "200": "R", "328": "I"}


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def parse_voteview_senate(rollcalls: Path, votes: Path, members: Path) -> list[RollCall]:
    senators = {m["icpsr"]: m for m in _read_csv(members) if m["chamber"] == "Senate"}
    roll_calls = {}
    for row in _read_csv(rollcalls):
        congress = int(row["congress"])
        roll_calls[row["rollnumber"]] = RollCall(
            chamber="Senate",
            congress=congress,
            session=int(row["session"]),
            roll_number=int(row["clerk_rollnumber"]),
            vote_date=date.fromisoformat(row["date"]),
            vote_time=None,
            question=row["vote_question"] or None,
            vote_type=None,
            result=row["vote_result"] or None,
            legis_num=row["bill_number"] or None,
            bill_id=legis_bill_id(congress, row["bill_number"]),
            amendment_num=None,
            amendment_author=None,
            description=row["vote_desc"] or None,
        )
    for row in _read_csv(votes):
        member = senators.get(row["icpsr"])
        if member is None or row["cast_code"] not in VOTEVIEW_CAST:
            continue  # the President, or code 0 (not a member)
        position, raw = VOTEVIEW_CAST[row["cast_code"]]
        roll_calls[row["rollnumber"]].members.append(
            MemberVote(
                bioguide_id=member["bioguide_id"],
                position=position,
                raw_position=raw,
                party=VOTEVIEW_PARTY.get(member["party_code"], member["party_code"]),
                state=member["state_abbrev"],
            )
        )
    return list(roll_calls.values())
