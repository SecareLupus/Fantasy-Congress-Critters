"""Rosters, purchases, drops and points in a league (Design-Economy §5.2, §6).

Each legislative year (session) has its own budget, the league's annual_budget, with no
carryover. Time moves in settlement weeks (scoring.week_bounds), and only weeks that start
inside the league count: a league that starts mid-session reserves and scores its own weeks.

- A purchase spends its signing fee at once and reserves the weekly fee for every league week
  left in the session. Made before the session, it is held from week 1; made during a week,
  from the next one, so no one buys a week whose points are already known.
- A week's fee is charged when the week starts. Available balance = budget − spent − reserved.
- A drop made during a week takes effect the next week: the critter scores through the week
  already paid for, and the later weeks' reservation returns. The signing fee is never
  refunded; the league's drop_cost adds an extra fee and a points penalty.
- A critter whose service ends mid-session leaves the roster: weeks starting after that are
  not charged, their reservation returns, and the slot frees without a drop cost.
- Points count for the weeks held, once each week has ended.
"""

from dataclasses import dataclass, replace
from datetime import date

from .scoring import Session, week_bounds, week_of

# Allow for float sums of fees when comparing against a balance.
CENTS = 0.005


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Calendar:
    """The settlement weeks of one session, and which of them (1-based) are league weeks."""
    session: Session
    bounds: tuple[tuple[date, date], ...]
    weeks: tuple[int, ...]

    @classmethod
    def build(cls, session: Session, weeks: int, league_start: date, league_end: date) -> "Calendar":
        bounds = tuple(week_bounds(session, weeks))
        return cls(session, bounds, tuple(w + 1 for w, (a, _) in enumerate(bounds) if league_start <= a < league_end))

    def start(self, week: int) -> date:
        return self.bounds[week - 1][0]

    def end(self, week: int) -> date:
        return self.bounds[week - 1][1]

    def next_week(self, day: date) -> int | None:
        """The first league week a transaction made on `day` affects."""
        first = 1 if day < self.session.start else week_of(self.session, day, len(self.bounds)) + 1
        return next((w for w in self.weeks if w >= first), None)

    def settled(self, as_of: date) -> list[int]:
        return [w for w in self.weeks if self.end(w) <= as_of]


@dataclass
class Holding:
    """A purchase, and its drop if there is one."""
    bioguide_id: str
    chamber: str  # rep | sen
    made_on: date
    first_week: int
    last_week: int
    session_cost: int
    signing_fee: float
    weekly_fee: float
    left_office: date | None = None  # service ends within the session
    dropped_on: date | None = None
    drop_week: int | None = None  # first week no longer held
    extra_fee: int = 0
    points_penalty: float = 0.0
    txn_id: int | None = None

    def dropped(self, as_of: date) -> bool:
        return self.dropped_on is not None and self.dropped_on <= as_of

    def departed(self, as_of: date) -> bool:
        return self.left_office is not None and self.left_office <= as_of

    def active(self, as_of: date) -> bool:
        """On the roster and taking a slot on `as_of`."""
        return self.made_on <= as_of and not self.dropped(as_of) and not self.departed(as_of)

    def held_weeks(self, cal: Calendar, as_of: date) -> list[int]:
        """League weeks the critter is on the roster, as known on `as_of`."""
        stop = self.drop_week if self.dropped(as_of) else self.last_week + 1
        weeks = [w for w in cal.weeks if self.first_week <= w < stop]
        if self.departed(as_of):
            weeks = [w for w in weeks if cal.start(w) < self.left_office]
        return weeks


@dataclass
class Budget:
    budget: int
    spent: float
    reserved: float

    @property
    def available(self) -> float:
        return self.budget - self.spent - self.reserved


def budget(holdings: list[Holding], cal: Calendar, annual_budget: int, as_of: date) -> Budget:
    spent = reserved = 0.0
    for h in holdings:
        if h.made_on > as_of:
            continue
        spent += h.signing_fee + (h.extra_fee if h.dropped(as_of) else 0)
        for w in h.held_weeks(cal, as_of):
            if cal.start(w) <= as_of:
                spent += h.weekly_fee
            else:
                reserved += h.weekly_fee
    return Budget(annual_budget, spent, reserved)


def purchase(holdings: list[Holding], cal: Calendar, settings: dict, day: date, *, bioguide_id: str,
             chamber: str, session_cost: int, signing_fee: float, weekly_fee: float,
             left_office: date | None) -> Holding:
    """The holding a purchase on `day` makes, or Refused with the reason."""
    first = cal.next_week(day)
    if first is None:
        raise Refused("no league weeks are left in the session")
    if left_office is not None and left_office <= cal.start(first):
        raise Refused(f"leaves office on {left_office}, before week {first}")
    held = [h for h in holdings if h.active(day)]
    if any(h.bioguide_id == bioguide_id for h in held):
        raise Refused("already on the roster")
    rules = settings["roster_rules"]
    if len(held) >= rules["roster_limit"]:
        raise Refused(f"the roster is full ({rules['roster_limit']} critters)")
    if rules["chamber_slots"]:
        side = "senate" if chamber == "sen" else "house"
        if sum(h.chamber == chamber for h in held) >= rules["chamber_slots"][side]:
            raise Refused(f"the {side} slots are full ({rules['chamber_slots'][side]})")
    weeks = [w for w in cal.weeks if w >= first]
    cost = signing_fee + weekly_fee * len(weeks)
    available = budget(holdings, cal, settings["budget_rules"]["annual_budget"], day).available
    if cost > available + CENTS:
        raise Refused(f"costs ${cost:,.2f} (signing ${signing_fee:,.2f} + {len(weeks)} weeks at "
                      f"${weekly_fee:,.2f}), more than the ${available:,.2f} available")
    return Holding(bioguide_id, chamber, day, first, weeks[-1], session_cost, signing_fee, weekly_fee, left_office)


def drop(holdings: list[Holding], cal: Calendar, settings: dict, day: date, bioguide_id: str) -> Holding:
    """The holding with the drop on `day` applied, or Refused with the reason."""
    h = next((h for h in holdings if h.bioguide_id == bioguide_id and h.active(day)), None)
    if h is None:
        raise Refused("not on the roster")
    week = max(cal.next_week(day) or h.last_week + 1, h.first_week)
    cost = settings["drop_cost"]
    dropped = replace(h, dropped_on=day, drop_week=week, extra_fee=cost["extra_fee"],
                      points_penalty=cost["points_penalty"])
    after = budget([dropped if x is h else x for x in holdings], cal,
                   settings["budget_rules"]["annual_budget"], day)
    if after.available < -CENTS:
        raise Refused(f"the ${cost['extra_fee']:,} drop fee is more than the balance available after the drop")
    return dropped


def points(h: Holding, cal: Calendar, weekly: dict[tuple[str, int], tuple[float, float]],
           as_of: date) -> tuple[float, float]:
    """(power, productivity) the holding has earned in weeks ended by `as_of`."""
    power = productivity = 0.0
    settled = set(cal.settled(as_of))
    for w in h.held_weeks(cal, as_of):
        if w in settled:
            p, q = weekly.get((h.bioguide_id, w), (0.0, 0.0))
            power, productivity = power + p, productivity + q
    return power, productivity


def penalties(holdings: list[Holding], as_of: date) -> float:
    return sum(h.points_penalty for h in holdings if h.dropped(as_of))
