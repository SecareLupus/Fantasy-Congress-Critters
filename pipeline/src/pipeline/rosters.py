"""Build dated committee memberships from snapshots of committee-membership-current.yaml.

congress-legislators keeps only the current roster, so history comes from the file's
commits. A snapshot is dated by its commit, which can trail the real change by weeks:

- Each (committee, member, side, role) present in consecutive snapshots is one membership.
- It starts at the snapshot where it first appears and ends at the snapshot where it is
  gone. Memberships in the Congress's first snapshot start on the Congress's first day,
  since there is no earlier record for the new Congress.
- Memberships still present in the last snapshot end with the Congress.
- Each membership is clipped to the member's terms in the committee's chamber, which
  have exact dates, so deaths and resignations are not lagged. A member who joined the
  chamber between the previous snapshot and the one where the seat appears (a special
  election or appointment) holds it from their first day.
- A committee the file listed only long after its members were seated (SEATED_BEFORE_LISTED)
  has its first listed seats start on the day they were filled.
"""

import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree

import yaml

ROLES = {
    "chairman": "chair",
    "chair": "chair",
    "chairwoman": "chair",
    "cochairman": "chair",
    "ranking member": "ranking_member",
    "vice chairman": "vice_chair",
    "vice chair": "vice_chair",
    "vice chairwoman": "vice_chair",
    "ex officio": "ex_officio",
}
SNAPSHOT_NAME = re.compile(r"^(\d{8})T\d{6}_")

# Congress -> committee -> the day its members were named, for committees that
# congress-legislators added to the roster file months after they were seated.
SEATED_BEFORE_LISTED = {
    118: {
        # Task Force on the Attempted Assassination of Donald J. Trump: created by
        # H.Res. 1367 on 2024-07-24, members named 2024-07-29, first listed 2024-12-17.
        "hszt00": date(2024, 7, 29),
    },
}


@dataclass(frozen=True)
class Seat:
    committee_code: str
    bioguide_id: str
    side: str  # majority | minority
    role: str  # member, chair, ranking_member, vice_chair, ex_officio, or other
    title: str | None


@dataclass
class Membership:
    seat: Seat
    start_date: date
    end_date: date  # exclusive
    first_seen: date
    last_seen: date
    previous_snapshot: date  # the seat began after this date (the Congress start for the first)


def committee_code(thomas_id: str) -> str:
    """HSAG -> hsag00, HSAG15 -> hsag15 (BILLSTATUS system codes)."""
    thomas_id = thomas_id.lower()
    return thomas_id + "00" if len(thomas_id) == 4 else thomas_id


def role(title: str | None) -> str:
    if not title:
        return "member"
    return ROLES.get(title.strip().lower(), "other")


def parse_snapshot(data: dict) -> set[Seat]:
    seats = set()
    for thomas_id, members in (data or {}).items():
        for m in members or []:
            if not m.get("bioguide"):
                continue
            seats.add(Seat(committee_code(thomas_id), m["bioguide"], m.get("party"),
                           role(m.get("title")), m.get("title")))
    return seats


def load_snapshots(directory: Path) -> list[tuple[date, set[Seat]]]:
    """Snapshots in commit order; several commits on one day collapse to the day's last."""
    by_day: dict[date, set[Seat]] = {}
    for path in sorted(directory.glob("*.yaml")):
        day = date.fromisoformat(SNAPSHOT_NAME.match(path.name).group(1))
        with open(path) as f:
            by_day[day] = parse_snapshot(yaml.load(f, Loader=yaml.CSafeLoader))
    return sorted(by_day.items())


def fold(name: str) -> str:
    """Lowercase without accents, for matching names across sources (Luján, Lujan)."""
    return "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c)).lower()


def _house_title(leadership: str | None, side: str, rank: int) -> str | None:
    if leadership:
        return leadership
    return "Ranking Member" if side == "minority" and rank == 1 else None


def house_seats(member_data: bytes, house_ids: dict[str, str]) -> dict[str, list[dict]]:
    """The House Clerk's MemberData.xml as a roster snapshot (thomas id -> members).

    house_ids maps the Clerk's two-letter committee codes to thomas ids (AG -> HSAG,
    EC -> JSEC). Sides follow the caucus (an independent who caucuses with the majority
    sits with it). The Clerk lists ranks but titles only chairs and vice chairs; the
    minority's first member is the ranking member, as congress-legislators records it.
    """
    root = ElementTree.fromstring(member_data)
    majority = root.findtext("title-info/majority")
    snapshot: dict[str, list[dict]] = {}
    for member in root.iter("member"):
        bioguide = (member.findtext("member-info/bioguideID") or "").strip()
        if not bioguide:
            continue  # vacant seat
        caucus = member.findtext("member-info/caucus") or member.findtext("member-info/party")
        side = "majority" if caucus == majority else "minority"
        name = member.findtext("member-info/official-name")
        for el in member.findall("committee-assignments/*"):
            code = el.get("comcode") or el.get("subcomcode")
            thomas_id = house_ids.get((code or "")[:2])
            if thomas_id is None:
                continue  # an empty assignment, or a committee congress-legislators doesn't list
            key = thomas_id + ("" if code.endswith("00") else code[2:])
            rank = int(el.get("rank") or 0)
            entry = {"name": name, "party": side, "rank": rank, "bioguide": bioguide}
            title = _house_title(el.get("leadership"), side, rank)
            if title:
                entry["title"] = title
            if thomas_id.startswith("J"):
                entry["chamber"] = "house"
            snapshot.setdefault(key, []).append(entry)
    return snapshot


def house_congress(member_data: bytes) -> int:
    """The Congress MemberData.xml describes."""
    return int(ElementTree.fromstring(member_data).findtext("title-info/congress-num"))


SENATE_TITLES = {"Ranking": "Ranking Member", "Member": None}


@dataclass(frozen=True)
class Senator:
    bioguide_id: str
    state: str
    last_name: str
    caucus: str | None  # party letter: R, D


def _match(senators: list[Senator], state: str, last: str) -> Senator | None:
    """The sitting senator from `state` named `last`; the Senate's roster may give only the
    first of two surnames (Graham for Graham Nordone)."""
    here = [s for s in senators if s.state == state]
    for found in ([s for s in here if fold(s.last_name) == fold(last)],
                  [s for s in here if fold(last) in fold(s.last_name).replace("-", " ").split()]):
        if len(found) == 1:
            return found[0]
    return None


def senate_seats(xml: bytes, senators: list[Senator],
                 former: list[Senator] = ()) -> tuple[dict[str, list[dict]], list[str]]:
    """One senate.gov committee_memberships_{code}.xml as a roster snapshot, and the
    members it couldn't match. The Senate lists names and states, not bioguide ids, so
    members are matched to sitting senators by state and last name, or failing that to
    `former` senators whose terms ended recently. congress-legislators ends an appointed
    senator's term on the day of the special election, but they serve until the winner
    takes office, and the Senate keeps listing them; their seats are kept, and scoring
    clips them to their terms as congress-legislators records them. Sides follow the
    caucus, as in house_seats.
    """
    root = ElementTree.fromstring(xml)
    committees = root.find("committees")
    majority = committees.findtext("majority_party")
    snapshot: dict[str, list[dict]] = {}
    unmatched = []
    groups = [committees] + committees.findall("subcommittee")
    for group in groups:
        code = group.findtext("committee_code")
        key = code[:4] if code.endswith("00") else code
        ranks: dict[str, int] = {}
        for member in group.findall("members/member"):
            first, last = member.findtext("name/first"), member.findtext("name/last")
            state = member.findtext("state")
            senator = _match(senators, state, last) or _match(former, state, last)
            if senator is None:
                unmatched.append(f"{key} {first} {last} ({state})")
                continue
            side = "majority" if (senator.caucus or member.findtext("party")) == majority else "minority"
            ranks[side] = ranks.get(side, 0) + 1
            entry = {"name": f"{first} {last}", "party": side, "rank": ranks[side],
                     "bioguide": senator.bioguide_id}
            position = (member.findtext("position") or "").strip()
            title = SENATE_TITLES.get(position, position or None)
            if title:
                entry["title"] = title
            if key.startswith("J"):
                entry["chamber"] = "senate"
            snapshot.setdefault(key, []).append(entry)
    return snapshot, unmatched


def build_memberships(snapshots: list[tuple[date, set[Seat]]], congress_start: date,
                      congress_end: date) -> list[Membership]:
    memberships: list[Membership] = []
    open_: dict[Seat, Membership] = {}
    for i, (day, seats) in enumerate(snapshots):
        for seat in list(open_):
            if seat not in seats:
                memberships.append(open_.pop(seat))
                memberships[-1].end_date = day
        for seat in seats:
            if seat in open_:
                open_[seat].last_seen = day
            else:
                start = congress_start if i == 0 else day
                previous = congress_start if i == 0 else snapshots[i - 1][0]
                open_[seat] = Membership(seat, start, congress_end, day, day, previous)
    memberships.extend(open_.values())
    return memberships


def backfill_starts(memberships: list[Membership], seated: dict[str, date]) -> None:
    """Start a late-listed committee's first listed seats on the day they were filled."""
    first_listed: dict[str, date] = {}
    for m in memberships:
        code = m.seat.committee_code
        first_listed[code] = min(first_listed.get(code, m.first_seen), m.first_seen)
    for m in memberships:
        code = m.seat.committee_code
        if code in seated and m.first_seen == first_listed[code] and seated[code] < m.start_date:
            m.start_date = m.previous_snapshot = seated[code]


def _service(terms: list[tuple[date, date]]) -> list[tuple[date, date]]:
    """Merge terms (end dates inclusive) into continuous periods with exclusive ends.

    Consecutive terms share a day (one ends January 3 as the next begins), so they merge.
    """
    periods: list[list[date]] = []
    for start, end in sorted(terms):
        end = end + timedelta(days=1)
        if periods and start <= periods[-1][1]:
            periods[-1][1] = max(periods[-1][1], end)
        else:
            periods.append([start, end])
    return [(start, end) for start, end in periods]


def clip_to_terms(membership: Membership, terms: list[tuple[date, date]]) -> list[Membership]:
    """Intersect with the member's terms (end dates inclusive) in the committee's chamber."""
    pieces = []
    for term_start, term_end in _service(terms):
        start = max(membership.start_date, term_start)
        if membership.previous_snapshot < term_start < membership.start_date:
            start = term_start  # joined the chamber after the last snapshot without this seat
        end = min(membership.end_date, term_end)
        if start < end:
            pieces.append(replace(membership, start_date=start, end_date=end))
    return pieces
