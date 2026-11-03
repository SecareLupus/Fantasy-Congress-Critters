"""Price critters for a session (Design-Economy §5.2).

Session Cost = projected points × price per point × market multiplier.

Projected points use only what is known on the session's first day:

- Power: the value of every seat and post held that day, times last session's roll-call
  participation (the chamber median for a member with none on record).
- Productivity: last session's productivity per full year served, pulled toward the
  chamber median by `productivity_shrink`.

The market multiplier moves the price away from projected value on purpose: donations
(cycle receipts, ranked within chamber and election status) and a re-election premium.

Every constant comes from the ruleset's [pricing] section.
"""

from dataclasses import dataclass
from statistics import median


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
