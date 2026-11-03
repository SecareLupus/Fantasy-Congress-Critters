"""Price critters for a session (Design-Economy §5.2).

Session Cost = projected points × price per point × market multiplier.

Projected points use only what is known on the session's first day:

- Power: the value of every seat and post held that day, times last session's roll-call
  participation (the chamber median for a member with none on record).
- Productivity: last session's productivity per full year served, pulled toward the
  chamber median by `productivity_shrink`.

The market multiplier moves the price away from projected value on purpose: donations
(cycle receipts, ranked within chamber and election status) and a re-election premium.

A new Congress seats its committees weeks after it convenes. Until then, committee seats
are projected (carried_seats): returning members keep the seats they held when the last
Congress ended, with chairs and ranking members swapped in a chamber whose majority changed,
and members new to their chamber get what that chamber's freshmen held last Congress. The
projection is discounted by `unposted_seat_discount`.

Every constant comes from the ruleset's [pricing] section.
"""

from dataclasses import dataclass
from statistics import median

# When a chamber's majority changes, chairs become ranking members and the reverse.
MAJORITY_SWAP = {"chair": "ranking_member", "ranking_member": "chair"}


@dataclass
class Member:
    bioguide_id: str
    chamber: str  # rep | sen
    seat_value: float  # seats and posts held on the session's first day, chamber factor applied
    participation: float | None  # last session's roll-call participation
    productivity_rate: float | None  # last session's productivity per full year served
    receipts: float | None  # FEC total receipts for the cycle; None if none on record
    up_for_election: bool  # current term ends with this session


@dataclass
class Price:
    bioguide_id: str
    chamber: str
    projected_power: float
    projected_productivity: float
    multiplier: float
    session_cost: int
    signing_fee: float
    weekly_fee: float

    @property
    def projected_points(self) -> float:
        return self.projected_power + self.projected_productivity


def percentiles(values: dict[str, float]) -> dict[str, float]:
    """Mid-rank percentile in (0, 1) of each value; ties share their mean rank."""
    ordered = sorted(values.items(), key=lambda kv: kv[1])
    out: dict[str, float] = {}
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        pct = ((i + j) / 2 + 0.5) / len(ordered)
        for key, _ in ordered[i:j + 1]:
            out[key] = pct
        i = j + 1
    return out


def market_multiplier(donations_pct: float, up_for_election: bool, cfg: dict) -> float:
    m = 1 + cfg["donations_band"] * (2 * donations_pct - 1)
    if up_for_election:
        m *= 1 + cfg["reelection_premium"]
    return min(max(m, cfg["multiplier_min"]), cfg["multiplier_max"])


def session_cost(projected_points: float, multiplier: float, cfg: dict) -> int:
    step = cfg["round_to"]
    return int(round(projected_points * cfg["price_per_point"] * multiplier / step) * step)


def fees(cost: int, cfg: dict) -> tuple[float, float]:
    """(signing fee, weekly fee) for a Session Cost."""
    signing = cost * cfg["signing_fee_share"]
    return signing, (cost - signing) / cfg["weeks"]


def charged(price: Price, weeks_owned: float) -> float:
    """What an owner pays: the signing fee plus the weekly fee for the weeks held."""
    return price.signing_fee + price.weekly_fee * weeks_owned


def price_session(members: list[Member], cfg: dict) -> list[Price]:
    prices = []
    for chamber in sorted({m.chamber for m in members}):
        group = [m for m in members if m.chamber == chamber]
        rates = [m.productivity_rate for m in group if m.productivity_rate is not None]
        med_rate = median(rates) if rates else 0.0
        parts = [m.participation for m in group if m.participation is not None]
        med_part = median(parts) if parts else 1.0
        # Members with no receipts on record (appointed, or elected after the cycle) rank
        # at the median rather than as the poorest fundraisers.
        pct: dict[str, float] = {m.bioguide_id: 0.5 for m in group}
        for up in (True, False):
            pct.update(percentiles({m.bioguide_id: m.receipts for m in group
                                    if m.up_for_election == up and m.receipts is not None}))
        for m in group:
            power = m.seat_value * (m.participation if m.participation is not None else med_part)
            rate = m.productivity_rate if m.productivity_rate is not None else med_rate
            productivity = med_rate + cfg["productivity_shrink"] * (rate - med_rate)
            mult = market_multiplier(pct[m.bioguide_id], m.up_for_election, cfg)
            cost = session_cost(power + productivity, mult, cfg)
            signing, weekly = fees(cost, cfg)
            prices.append(Price(m.bioguide_id, chamber, power, productivity, mult, cost, signing, weekly))
    return prices


@dataclass
class HeldSeat:
    bioguide_id: str
    chamber: str  # rep | sen
    category: str  # COMMITTEE_SEAT | SUBCOMMITTEE_SEAT
    role: str
    value: float  # per session, chamber factor applied


def carried_seats(held: list[HeldSeat], flipped: set[str], freshmen: set[str], positions: dict,
                  seated: dict[str, str], seated_before: dict[str, str]) -> dict[str, float]:
    """Projected committee seat value for each member seated in the new Congress (`seated`,
    bioguide -> chamber), from the seats `held` when the last Congress ended (when the
    members in `seated_before` sat). `flipped` holds the chambers whose majority changed.
    Members new to their chamber get the median of what last Congress's `freshmen` in that
    chamber held."""
    def role_mult(seat: HeldSeat, role: str) -> float:
        table = positions["committee_roles"] if seat.category == "COMMITTEE_SEAT" else positions["subcommittee_bonus"]
        return table.get(role, table["other"])

    carried: dict[str, float] = {}
    for seat in held:
        value = seat.value
        if seat.chamber in flipped and seat.role in MAJORITY_SWAP:
            value = value / role_mult(seat, seat.role) * role_mult(seat, MAJORITY_SWAP[seat.role])
        carried[seat.bioguide_id] = carried.get(seat.bioguide_id, 0.0) + value
    newcomer = {}
    for chamber in set(seated.values()):
        values = [carried.get(b, 0.0) for b, c in seated_before.items() if c == chamber and b in freshmen]
        newcomer[chamber] = median(values) if values else 0.0
    return {b: carried.get(b, 0.0) if seated_before.get(b) == chamber else newcomer[chamber]
            for b, chamber in seated.items()}
