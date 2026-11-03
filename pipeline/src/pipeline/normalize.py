"""Turn a parsed bill into ontology events (Design-Data §10.3).

Events are facts about the bill. They do not decide who earns credit; the
scoring engine applies gating and authorship rules to them.

Sources, in order of preference:
- Sponsor and cosponsor lists, for introduction and cosponsorship.
- Amendment records, for amendments offered, agreed to, and rejected.
- Structured committee activities, for referral, hearings, markup, reporting, discharge.
- Library of Congress action codes, for passage and presidential actions.
- House floor action codes, for House scheduling and floor steps.
- Senate and House committee action text, which carries no codes.

The same step often appears in several sources; events are deduplicated on
(type, date, chamber, committee, critter, amendment).
"""

import re
from dataclasses import dataclass
from datetime import date

from .billstatus import Action, Amendment, Bill

LOC = "Library of Congress"
HOUSE_FLOOR = "House floor actions"
HOUSE_COMMITTEE = "House committee actions"
SENATE = "Senate"


@dataclass(frozen=True)
class Event:
    bill_id: str
    event_type: str
    event_date: date
    chamber: str | None
    committee_code: str | None = None
    critter_id: str | None = None
    source: str = ""
    detail: str | None = None
    amendment_id: str | None = None

    @property
    def key(self) -> tuple:
        return (self.event_type, self.event_date, self.chamber, self.committee_code, self.critter_id,
                self.amendment_id)


COMMITTEE_ACTIVITIES = {
    "referred to": "COMMITTEE_REFERRAL",
    "re-referred to": "COMMITTEE_REFERRAL",
    "hearings by": "COMMITTEE_HEARING_HELD",
    "hearings by (full committee)": "COMMITTEE_HEARING_HELD",
    "hearings by (subcommittee)": "COMMITTEE_HEARING_HELD",
    "markup by": "COMMITTEE_MARKUP",
    "reported by": "REPORTED",
    "reported original measure": "REPORTED",
    "discharged from": "COMMITTEE_DISCHARGED",
}

LOC_CODES = {
    "8000": ("PASSED_CHAMBER", "House"),
    "17000": ("PASSED_CHAMBER", "Senate"),
    "9000": ("FAILED_PASSAGE", "House"),
    "18000": ("FAILED_PASSAGE", "Senate"),
    "19500": ("RESOLVED_DIFFERENCES", "House"),
    "20500": ("RESOLVED_DIFFERENCES", "Senate"),
    "21000": ("CONFERENCE_REPORT_AGREED", "House"),
    "23000": ("CONFERENCE_REPORT_AGREED", "Senate"),
    "28000": ("PRESENTED_TO_PRESIDENT", None),
    "31000": ("VETOED", None),
    "32000": ("VETO_OVERRIDE_PASSED", "House"),
    "33000": ("VETO_OVERRIDE_FAILED", "House"),
    "34000": ("VETO_OVERRIDE_PASSED", "Senate"),
    "35000": ("VETO_OVERRIDE_FAILED", "Senate"),
    "E40000": ("BECAME_LAW", None),
}

HOUSE_FLOOR_CODES = {
    "H12410": "PLACED_ON_CALENDAR",  # Union Calendar
    "H12420": "PLACED_ON_CALENDAR",  # House Calendar
    "H1L210": "RULE_REPORTED",
    "H1L220": "RULE_ADOPTED",
    "H30000": "FLOOR_CONSIDERATION",  # considered under a rule
    "H30200": "FLOOR_CONSIDERATION",  # unanimous consent to discharge and consider
    "H30300": "FLOOR_CONSIDERATION",  # motion to suspend the rules and pass
    "H30800": "FLOOR_CONSIDERATION",  # consideration under a previous order
    "H17000": "DISCHARGE_PETITION_FILED",
    "H12450": "DISCHARGE_PETITION_FILED",
    "H41800": "CONFERENCE_APPOINTED",
}

# Senate floor actions carry no codes; first matching pattern wins.
SENATE_FLOOR_PATTERNS = [
    (re.compile(r"placed on senate legislative calendar", re.I), "PLACED_ON_CALENDAR"),
    (re.compile(r"cloture motion .* (presented|filed)", re.I), "CLOTURE_FILED"),
    (re.compile(r"cloture .* not invoked", re.I), None),
    (re.compile(r"cloture .* invoked in senate", re.I), "CLOTURE_INVOKED"),
    (re.compile(r"motion to proceed to (consideration of )?(the )?measure", re.I), "MOTION_TO_PROCEED"),
    (re.compile(r"measure laid before senate|considered by senate", re.I), "FLOOR_CONSIDERATION"),
    (re.compile(r"senate appointed conferees", re.I), "CONFERENCE_APPOINTED"),
]

# Library of Congress codes on amendment actions. Senate amendments are often only
# submitted (filed, code 91000) and never brought up; only proposing one offers it.
AMENDMENT_OFFERED_CODES = {"71000", "93000"}
AMENDMENT_RESULT_CODES = {
    "72000": "AMENDMENT_ADOPTED",  # House amendment agreed to
    "76000": "AMENDMENT_ADOPTED",  # agreed to in Committee of the Whole
    "79000": "AMENDMENT_ADOPTED",  # agreed to by the House after the Committee of the Whole
    "94000": "AMENDMENT_ADOPTED",  # Senate amendment agreed to
    "73000": "AMENDMENT_FAILED",
    "77000": "AMENDMENT_FAILED",
    "80000": "AMENDMENT_FAILED",
    "95000": "AMENDMENT_FAILED",
}

# Roll call quoted in action text: House "(Roll no. 312)", Senate "Record Vote Number: 88".
ROLL_IN_TEXT = re.compile(r"Roll no\. (\d+)|Record Vote Number:? (\d+)", re.I)

ORDERED_REPORTED = re.compile(r"ordered to be reported", re.I)
SENATE_HEARING = re.compile(r"hearings held", re.I)
# Hearings that predate the bill are about the subject, not the measure.
HEARING_BEFORE_BILL = re.compile(r"prior to (introduction|measure being received)", re.I)


def _action_committee(action: Action) -> str | None:
    return action.committee_codes[0] if action.committee_codes else None


def _action_events(bill: Bill, action: Action) -> list[Event]:
    def event(event_type: str, chamber: str | None, committee: str | None = None) -> Event:
        return Event(
            bill_id=bill.bill_id,
            event_type=event_type,
            event_date=action.action_date,
            chamber=chamber,
            committee_code=committee,
            source=f"action:{action.source_name}:{action.action_code or '-'}",
            detail=action.text[:500],
        )

    source, code, text = action.source_name, action.action_code, action.text

    if source == LOC and code in LOC_CODES:
        event_type, chamber = LOC_CODES[code]
        return [event(event_type, chamber)]

    if source == HOUSE_FLOOR and code in HOUSE_FLOOR_CODES:
        return [event(HOUSE_FLOOR_CODES[code], "House")]

    if source == HOUSE_COMMITTEE and ORDERED_REPORTED.search(text):
        return [event("ORDERED_REPORTED", "House", _action_committee(action))]

    if source == SENATE and action.action_type == "Committee":
        if ORDERED_REPORTED.search(text):
            return [event("ORDERED_REPORTED", "Senate", _action_committee(action))]
        if SENATE_HEARING.search(text) and not HEARING_BEFORE_BILL.search(text):
            return [event("COMMITTEE_HEARING_HELD", "Senate", _action_committee(action))]
        return []

    if source == SENATE and action.action_type in ("Floor", "Calendars", "ResolvingDifferences"):
        for pattern, event_type in SENATE_FLOOR_PATTERNS:
            if pattern.search(text):
                return [event(event_type, "Senate")] if event_type else []

    return []


def _action_order(action: Action) -> tuple:
    """Same-day actions are not reliably in order in the feed; a later roll call is later."""
    match = ROLL_IN_TEXT.search(action.text)
    roll = int(match.group(1) or match.group(2)) if match else 0
    return (action.action_date, roll, action.seq)


def _amendment_events(bill: Bill, amendment: Amendment) -> list[Event]:
    """At most one offered event (the first) and one result (the last) per amendment.

    A House amendment's result is often recorded twice, in the Committee of the Whole
    and again by the House, and a close vote may be retaken; the last word stands.
    """
    loc = [a for a in amendment.actions if a.source_name == LOC]
    offered = next((a for a in loc if a.action_code in AMENDMENT_OFFERED_CODES), None)
    results = [a for a in loc if a.action_code in AMENDMENT_RESULT_CODES]
    result = max(results, key=_action_order, default=None)

    def event(event_type: str, action: Action) -> Event:
        return Event(
            bill_id=bill.bill_id,
            event_type=event_type,
            event_date=action.action_date,
            chamber=amendment.chamber,
            critter_id=amendment.sponsor_id,
            source=f"amendment:{action.source_name}:{action.action_code}",
            detail=action.text[:500],
            amendment_id=amendment.amendment_id,
        )

    events = []
    if offered:
        events.append(event("AMENDMENT_OFFERED", offered))
    if result:
        events.append(event(AMENDMENT_RESULT_CODES[result.action_code], result))
    return events


def normalize_bill(bill: Bill) -> list[Event]:
    events: list[Event] = []

    if bill.introduced_date and bill.sponsor_id:
        events.append(
            Event(
                bill_id=bill.bill_id,
                event_type="BILL_INTRODUCED",
                event_date=bill.introduced_date,
                chamber=bill.origin_chamber,
                critter_id=bill.sponsor_id,
                source="sponsors",
                detail="by_request" if bill.sponsor_by_request else None,
            )
        )

    for cosponsor in bill.cosponsors:
        if cosponsor.sponsorship_date:
            events.append(
                Event(
                    bill_id=bill.bill_id,
                    event_type="COSPONSOR_ADDED",
                    event_date=cosponsor.sponsorship_date,
                    chamber=bill.origin_chamber,
                    critter_id=cosponsor.bioguide_id,
                    source="cosponsors",
                    detail="original" if cosponsor.is_original else None,
                )
            )
        if cosponsor.withdrawn_date:
            events.append(
                Event(
                    bill_id=bill.bill_id,
                    event_type="COSPONSOR_WITHDRAWN",
                    event_date=cosponsor.withdrawn_date,
                    chamber=bill.origin_chamber,
                    critter_id=cosponsor.bioguide_id,
                    source="cosponsors",
                )
            )

    for activity in bill.committee_activities:
        event_type = COMMITTEE_ACTIVITIES.get(activity.activity.lower())
        if event_type and activity.activity_at:
            events.append(
                Event(
                    bill_id=bill.bill_id,
                    event_type=event_type,
                    event_date=activity.activity_at.date(),
                    chamber=activity.chamber,
                    committee_code=activity.committee_code,
                    source="committee_activity",
                    detail=activity.activity,
                )
            )

    for action in bill.actions:
        events.extend(_action_events(bill, action))

    for amendment in bill.amendments:
        events.extend(_amendment_events(bill, amendment))

    seen: set[tuple] = set()
    unique = []
    for event in events:
        if event.key not in seen:
            seen.add(event.key)
            unique.append(event)
    return unique
