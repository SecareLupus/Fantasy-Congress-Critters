"""Parse GovInfo BILLSTATUS XML into plain records."""

import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from xml.etree.ElementTree import Element, fromstring


@dataclass
class Cosponsor:
    bioguide_id: str
    sponsorship_date: date | None
    is_original: bool
    withdrawn_date: date | None


@dataclass
class CommitteeActivity:
    committee_code: str
    parent_committee_code: str | None  # set when committee_code is a subcommittee
    committee_name: str
    chamber: str | None
    activity: str
    activity_at: datetime | None


@dataclass
class RecordedVote:
    chamber: str
    congress: int
    session: int
    roll_number: int
    vote_date: datetime | None


@dataclass
class Action:
    seq: int
    action_date: date
    action_time: time | None
    text: str
    action_type: str | None
    action_code: str | None
    source_code: str | None
    source_name: str | None
    committee_codes: list[str]
    recorded_votes: list[RecordedVote]


@dataclass
class Bill:
    congress: int
    bill_type: str
    number: int
    title: str | None
    introduced_date: date | None
    origin_chamber: str | None
    policy_area: str | None
    sponsor_id: str | None
    sponsor_by_request: bool
    update_date: datetime | None
    cosponsors: list[Cosponsor] = field(default_factory=list)
    committee_activities: list[CommitteeActivity] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)

    @property
    def bill_id(self) -> str:
        return f"{self.congress}-{self.bill_type}-{self.number}"


def _text(el: Element | None, path: str) -> str | None:
    if el is None:
        return None
    found = el.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _items(el: Element | None, path: str) -> list[Element]:
    if el is None:
        return []
    container = el.find(path)
    return [] if container is None else list(container)


def _committee_activities(item: Element, parent_code: str | None) -> list[CommitteeActivity]:
    code = _text(item, "systemCode")
    name = _text(item, "name") or ""
    chamber = _text(item, "chamber")
    activities = [
        CommitteeActivity(
            committee_code=code,
            parent_committee_code=parent_code,
            committee_name=name,
            chamber=chamber,
            activity=_text(act, "name") or "",
            activity_at=_datetime(_text(act, "date")),
        )
        for act in _items(item, "activities")
    ]
    for sub in _items(item, "subcommittees"):
        for activity in _committee_activities(sub, code):
            activity.chamber = activity.chamber or chamber
            activities.append(activity)
    return activities


def parse_bill(xml: bytes) -> Bill:
    bill = fromstring(xml).find("bill")
    sponsor = next(iter(_items(bill, "sponsors")), None)

    result = Bill(
        congress=int(_text(bill, "congress")),
        bill_type=_text(bill, "type").lower(),
        number=int(_text(bill, "number")),
        title=_text(bill, "title"),
        introduced_date=_date(_text(bill, "introducedDate")),
        origin_chamber=_text(bill, "originChamber"),
        policy_area=_text(bill, "policyArea/name"),
        sponsor_id=_text(sponsor, "bioguideId"),
        sponsor_by_request=_text(sponsor, "isByRequest") == "Y",
        update_date=_datetime(_text(bill, "updateDate")),
    )

    for item in _items(bill, "cosponsors"):
        result.cosponsors.append(
            Cosponsor(
                bioguide_id=_text(item, "bioguideId"),
                sponsorship_date=_date(_text(item, "sponsorshipDate")),
                is_original=_text(item, "isOriginalCosponsor") == "True",
                withdrawn_date=_date(_text(item, "sponsorshipWithdrawnDate")),
            )
        )

    for item in _items(bill, "committees"):
        result.committee_activities.extend(_committee_activities(item, None))

    # The feed lists actions newest first; number them oldest first.
    for seq, item in enumerate(reversed(_items(bill, "actions"))):
        action_time = _text(item, "actionTime")
        result.actions.append(
            Action(
                seq=seq,
                action_date=_date(_text(item, "actionDate")),
                action_time=time.fromisoformat(action_time) if action_time else None,
                text=_text(item, "text") or "",
                action_type=_text(item, "type"),
                action_code=_text(item, "actionCode"),
                source_code=_text(item, "sourceSystem/code"),
                source_name=_text(item, "sourceSystem/name"),
                committee_codes=[
                    code for c in _items(item, "committees") if (code := _text(c, "systemCode"))
                ],
                recorded_votes=[
                    RecordedVote(
                        chamber=_text(v, "chamber"),
                        congress=int(_text(v, "congress")),
                        session=int(_text(v, "sessionNumber")),
                        roll_number=int(_text(v, "rollNumber")),
                        vote_date=_datetime(_text(v, "date")),
                    )
                    for v in _items(item, "recordedVotes")
                ],
            )
        )

    return result


def iter_zip(path: Path) -> Iterator[Bill]:
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith(".xml"):
                yield parse_bill(zf.read(name))
