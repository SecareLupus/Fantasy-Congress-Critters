"""Score critters from normalized data (Design-Scoring).

Two pipelines, kept separate as the design requires:

- Productivity: each event, vote, or amendment outcome produces items for the critters
  who earned it, after gating, authorship category, and coalition dilution.
- Power: each committee seat and leadership post produces one item per session, its
  value prorated by days held and multiplied by roll-call participation.

Every constant comes from the ruleset; this module has no point values of its own.
"""

import re
import tomllib
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

CAST = {"yea", "nay", "present", "other"}
# Delegates and the Resident Commissioner: House members who vote only in the Committee
# of the Whole, not on final passage.
NON_VOTING_STATES = {"DC", "PR", "GU", "VI", "AS", "MP"}
FULL_COMMITTEE_SUFFIX = "00"


@dataclass(frozen=True)
class Session:
    number: int
    start: date
    end: date  # exclusive

    @property
    def days(self) -> int:
        return (self.end - self.start).days


def congress_sessions(congress: int) -> list[Session]:
    first = 1787 + 2 * congress
    return [Session(1, date(first, 1, 3), date(first + 1, 1, 3)),
            Session(2, date(first + 1, 1, 3), date(first + 2, 1, 3))]


def session_of(sessions: list[Session], day: date) -> Session | None:
    return next((s for s in sessions if s.start <= day < s.end), None)


@dataclass
class ScoreItem:
    bioguide_id: str
    session: int
    pillar: str  # power | productivity
    category: str
    item_date: date
    points: float
    bill_id: str | None = None
    amendment_id: str | None = None
    vote_id: str | None = None
    committee_code: str | None = None
    detail: dict = field(default_factory=dict)


# --- ruleset -----------------------------------------------------------------------

@dataclass
class Ruleset:
    version: str
    raw: dict

    @classmethod
    def load(cls, path: Path) -> "Ruleset":
        with open(path, "rb") as f:
            raw = tomllib.load(f)
        return cls(raw["version"], raw)

    def event_rule(self, event_type: str) -> dict | None:
        return self.raw["events"].get(event_type)

    def authorship(self, category: str) -> float:
        return self.raw["authorship"][category]

    def dilution_exponent(self, rule: dict) -> float:
        d = self.raw["dilution"]
        return d["heavy_exponent"] if rule.get("dilution") == "heavy" else d["default_exponent"]


# --- productivity: bills -----------------------------------------------------------

@dataclass
class Cosponsor:
    bioguide_id: str
    sponsorship_date: date
    is_original: bool
    withdrawn_date: date | None


@dataclass
class EventRow:
    event_type: str
    event_date: date
    chamber: str | None
    committee_code: str | None
    critter_id: str | None
    amendment_id: str | None


@dataclass
class BillInputs:
    bill_id: str
    bill_type: str
    sponsor_id: str | None
    by_request: bool
    origin_chamber: str | None
    cosponsors: list[Cosponsor]
    events: list[EventRow]
    title: str = ""
    subjects: list[str] = field(default_factory=list)


STAGE_EVENTS = [
    ("COMMITTEE_HEARING_HELD", "COMMITTEE_MARKUP"),             # ends Early
    ("ORDERED_REPORTED", "REPORTED", "COMMITTEE_DISCHARGED"),   # ends Mid
    ("FLOOR_CONSIDERATION", "PASSED_CHAMBER", "FAILED_PASSAGE"),  # ends Late
]
STAGE_CATEGORIES = ["early", "mid", "late", "procedural"]


def stage_cutoffs(events: Iterable[EventRow], origin_chamber: str | None) -> list[date | None]:
    """First date of each stage in the chamber of origin. A skipped stage takes the next
    cutoff, so its window is empty (Design-Scoring §8.3 Stage Cutoffs)."""
    firsts: list[date | None] = []
    for types in STAGE_EVENTS:
        dates = [e.event_date for e in events if e.event_type in types and e.chamber == origin_chamber]
        firsts.append(min(dates) if dates else None)
    cutoffs: list[date | None] = []
    later: date | None = None
    for first in reversed(firsts):
        later = first if first and (later is None or first < later) else later
        cutoffs.append(later)
    return list(reversed(cutoffs))


def cosponsor_category(cosponsor: Cosponsor, cutoffs: list[date | None]) -> str:
    if cosponsor.is_original:
        return "early"
    for category, cutoff in zip(STAGE_CATEGORIES, cutoffs):
        if cutoff is None or cosponsor.sponsorship_date < cutoff:
            return category
    return "procedural"


def coalition_ranks(cosponsors: Iterable[Cosponsor]) -> dict[str, int]:
    """Sponsor is rank 1; co-sponsors joining on the same day share a rank, and the next
    day's joiners rank after all earlier joiners (Design-Scoring §3.2)."""
    by_date: dict[date, list[str]] = defaultdict(list)
    for c in cosponsors:
        by_date[c.sponsorship_date].append(c.bioguide_id)
    ranks, joined = {}, 0
    for day in sorted(by_date):
        for bioguide in by_date[day]:
            ranks[bioguide] = 2 + joined
        joined += len(by_date[day])
    return ranks


def dilution_share(rank: int, exponent: float) -> float:
    return 1 / rank ** exponent


def is_ceremonial(bill: BillInputs, ruleset: Ruleset) -> bool:
    """Namings, gold medals, commemorative coins: tagged as a tribute by CRS on a narrow
    bill, or titled like one. Big bills carry the tag for a naming section, hence the limit."""
    rule = ruleset.raw["ceremonial"]
    if rule["subject"] in bill.subjects and len(bill.subjects) <= rule["max_subjects"]:
        return True
    return any(re.search(pattern, bill.title, re.I) for pattern in rule["title_patterns"])


def bill_weight(bill: BillInputs, ruleset: Ruleset) -> float:
    """Bill-type weight, or the ceremonial weight when lower; the two don't stack."""
    weight = ruleset.raw["bill_types"][bill.bill_type]
    if is_ceremonial(bill, ruleset):
        weight = min(weight, ruleset.raw["ceremonial"]["weight"])
    return weight


OnCommittee = Callable[[str, str, date], bool]


def score_bill(bill: BillInputs, ruleset: Ruleset, sessions: list[Session],
               on_committee: OnCommittee) -> list[ScoreItem]:
    cutoffs = stage_cutoffs(bill.events, bill.origin_chamber)
    ranks = coalition_ranks(bill.cosponsors)
    categories = {c.bioguide_id: cosponsor_category(c, cutoffs) for c in bill.cosponsors}
    if bill.sponsor_id:
        ranks[bill.sponsor_id] = 1
        categories[bill.sponsor_id] = "procedural" if bill.by_request else "author"

    def backers(day: date) -> list[str]:
        ids = [bill.sponsor_id] if bill.sponsor_id else []
        ids += [c.bioguide_id for c in bill.cosponsors
                if c.sponsorship_date <= day and (c.withdrawn_date is None or c.withdrawn_date > day)]
        return ids

    weight = bill_weight(bill, ruleset) * ruleset.raw["productivity"]["scale"]
    items: list[ScoreItem] = []
    scored: set[tuple] = set()  # repeated actions on a bill score once (Design-Scoring §9.2)
    for event in sorted(bill.events, key=lambda e: e.event_date):
        rule = ruleset.event_rule(event.event_type)
        session = session_of(sessions, event.event_date)
        if rule is None or session is None:
            continue
        credit = rule["credit"]
        if credit in ("sponsor", "cosponsor", "amendment"):
            recipients = [event.critter_id] if event.critter_id else []
        elif credit == "backers":
            recipients = backers(event.event_date)
        elif credit == "backers_gated":
            recipients = [b for b in backers(event.event_date)
                          if event.committee_code and on_committee(b, event.committee_code, event.event_date)]
        else:
            raise ValueError(f"unknown credit rule {credit!r} for {event.event_type}")

        for bioguide in recipients:
            key = (bioguide, event.event_type, event.chamber, event.amendment_id)
            if key in scored:
                continue
            scored.add(key)
            points, detail = rule["points"] * weight, {}
            if rule.get("authorship"):
                if credit == "amendment":
                    category, rank = "author", 1
                else:
                    category, rank = categories.get(bioguide, "procedural"), ranks.get(bioguide, 1)
                share = dilution_share(rank, ruleset.dilution_exponent(rule))
                points *= ruleset.authorship(category) * share
                detail = {"category": category, "rank": rank, "share": round(share, 4)}
            items.append(ScoreItem(bioguide, session.number, "productivity", event.event_type,
                                   event.event_date, points, bill_id=bill.bill_id,
                                   amendment_id=event.amendment_id,
                                   committee_code=event.committee_code, detail=detail))
    return items


def apply_caps(items: list[ScoreItem], ruleset: Ruleset) -> list[ScoreItem]:
    """Only the first N items of a capped category score per critter and session; the
    rest stay in the ledger at zero so the cap is visible (Design-Scoring §9.1)."""
    caps = ruleset.raw.get("caps", {})
    counts: dict[tuple, int] = defaultdict(int)
    for item in sorted(items, key=lambda i: (i.item_date, i.bill_id or "")):
        cap = caps.get(item.category)
        if cap is None:
            continue
        key = (item.bioguide_id, item.session, item.category)
        counts[key] += 1
        if counts[key] > cap:
            item.detail = {**item.detail, "capped": True, "uncapped_points": item.points}
            item.points = 0.0
    return items


def apply_chamber_factor(items: list[ScoreItem], ruleset: Ruleset,
                         chamber_of: Callable[[str, date], str]) -> list[ScoreItem]:
    """Scale productivity by the earner's chamber, so the median senator and the median
    House member come out alike (power has its own factor in score_positions). Votes are
    left alone: they are already worth the same per session in both chambers."""
    factors = ruleset.raw["productivity"]["chamber_factor"]
    for item in items:
        if item.pillar != "productivity" or item.vote_id:
            continue
        factor = factors.get(chamber_of(item.bioguide_id, item.item_date), 1.0)
        if factor != 1.0:
            item.points *= factor
            item.detail = {**item.detail, "chamber_factor": factor}
    return items


# --- productivity: votes -----------------------------------------------------------

@dataclass
class VoteRow:
    vote_id: str
    vote_date: date
    question: str | None
    result: str | None
    legis_num: str | None
    bioguide_id: str
    position: str


def score_votes(votes: Iterable[VoteRow], ruleset: Ruleset, sessions: list[Session],
                seated: Callable[[str, date], bool], delegates: frozenset[str] = frozenset()) -> list[ScoreItem]:
    """A vote cast is worth a session's full-attendance value over the roll calls the member
    could cast: House, Senate, or for delegates the Committee of the Whole roll calls."""
    rules = ruleset.raw["votes"]
    scale = ruleset.raw["productivity"]["scale"]
    items = []
    for v in votes:
        session = session_of(sessions, v.vote_date)
        if session is None or v.position not in CAST or not seated(v.bioguide_id, v.vote_date):
            continue

        def item(category: str, points: float) -> ScoreItem:
            return ScoreItem(v.bioguide_id, session.number, "productivity", category,
                             v.vote_date, points * scale, vote_id=v.vote_id)

        chamber = "rep" if v.vote_id.split("-")[1].startswith("h") else "sen"
        if chamber == "rep" and v.bioguide_id in delegates:
            chamber = "delegate"
        items.append(item("VOTE_CAST", rules["full_attendance"] / rules["expected_roll_calls"][chamber]))
        if v.question == "On the Nomination":
            if rules["confirmation"]:
                items.append(item("CONFIRMATION_VOTE", rules["confirmation"]))
            if rules["confirmation_success"] and v.position == "yea" and v.result and "Confirmed" in v.result:
                items.append(item("CONFIRMATION_SUCCESS", rules["confirmation_success"]))
    return items


# --- power -------------------------------------------------------------------------

@dataclass
class Position:
    bioguide_id: str
    kind: str  # committee | leadership
    key: str   # committee code or leadership title
    role: str | None
    start: date
    end: date  # exclusive
    chamber: str | None = None  # the holder's chamber: rep | sen


def position_value(position: Position, ruleset: Ruleset) -> tuple[str, float] | None:
    """(category, value per session) or None when the position carries no value."""
    p = ruleset.raw["positions"]
    if position.kind == "leadership":
        return "LEADERSHIP", p["leadership"].get(position.key, p["leadership"]["default"])
    code = position.key
    if code.endswith(FULL_COMMITTEE_SUFFIX):
        if code in p["ad_hoc"]:
            return "AD_HOC_SEAT", p["ad_hoc"][code]
        tier = p["committees"].get(code)
        if tier is None:
            return None
        return "COMMITTEE_SEAT", p["committee_tiers"][str(tier)] * p["committee_roles"][position.role]
    tier = p["committees"].get(code[:4] + FULL_COMMITTEE_SUFFIX)
    if tier is None:
        return None
    return "SUBCOMMITTEE_SEAT", p["committee_tiers"][str(tier)] * p["subcommittee_bonus"][position.role]


Participation = Callable[[str, date, date], float]


def score_positions(positions: Iterable[Position], ruleset: Ruleset, sessions: list[Session],
                    participation: Participation) -> list[ScoreItem]:
    items = []
    for pos in positions:
        valued = position_value(pos, ruleset)
        if valued is None or valued[1] == 0:
            continue
        category, value = valued
        value *= ruleset.raw["positions"]["chamber_factor"].get(pos.chamber, 1.0)
        for s in sessions:
            start, end = max(pos.start, s.start), min(pos.end, s.end)
            if start >= end:
                continue
            days = (end - start).days
            rate = participation(pos.bioguide_id, start, end)
            points = value * days / s.days * rate
            items.append(ScoreItem(
                pos.bioguide_id, s.number, "power", category, start, points,
                committee_code=pos.key if pos.kind == "committee" else None,
                detail={"key": pos.key, "role": pos.role, "chamber": pos.chamber,
                        "value": value, "days": days,
                        "session_days": s.days, "participation": round(rate, 4)},
            ))
    return items


def floor_participation(votes: Iterable[VoteRow], exempt: dict[str, list[tuple[date, date]]]) -> Participation:
    """Share of a member's recorded roll calls in a window that they voted on. Days in an
    exempt post (the Speaker) are left out; a window with no votes counts as full."""
    by_member: dict[str, list[tuple[date, bool]]] = defaultdict(list)
    for v in votes:
        by_member[v.bioguide_id].append((v.vote_date, v.position in CAST))

    def rate(bioguide: str, start: date, end: date) -> float:
        periods = exempt.get(bioguide, [])
        window = [cast for day, cast in by_member.get(bioguide, [])
                  if start <= day < end and not any(a <= day < b for a, b in periods)]
        return sum(window) / len(window) if window else 1.0

    return rate
