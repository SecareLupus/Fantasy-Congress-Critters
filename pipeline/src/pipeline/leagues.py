"""Leagues and their settings (Design-Rulesets §6A.4–6A.7).

A league is created by a game master: a GameMaker for official leagues, a commissioner
for private ones. Its competition rules (budget, roster, win condition, drop cost) are
settings on the league, resolved from a preset plus overrides when the league is created
and checked against SETTINGS. The league also freezes a copy of the ruleset it scores and
prices with. Nothing about a league can change once it has started.

This module holds the shape of the settings and their limits, not their values: values
come from presets and game masters.
"""

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import date

OFFICIAL_TYPES = ("session", "annual", "representative", "presidential", "senatorial")
PRIVATE_TYPES = ("standard_private", "flexible_private")
WIN_CONDITIONS = ("cumulative", "head_to_head")


@dataclass(frozen=True)
class Setting:
    path: str
    kind: type | tuple
    description: str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple | None = None
    nullable: bool = False


SETTINGS = [
    Setting("budget_rules.annual_budget", int, "play dollars per legislative year", minimum=1),
    Setting("roster_rules.roster_limit", int, "most critters a roster can hold", minimum=1, maximum=100),
    Setting("roster_rules.chamber_slots", dict, "most critters from each chamber, "
            "{house: n, senate: m}; null for no limit", nullable=True),
    Setting("win_condition", str, "how standings are decided", choices=WIN_CONDITIONS),
    Setting("drop_cost.extra_fee", int, "play dollars charged on a drop, on top of the "
            "signing fee that is never refunded", minimum=0),
    Setting("drop_cost.points_penalty", (int, float), "points deducted from the player's "
            "total on a drop (not floored at zero)", minimum=0),
]


def get_path(settings: dict, path: str):
    node = settings
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


def set_path(settings: dict, path: str, value) -> None:
    *parents, leaf = path.split(".")
    node = settings
    for part in parents:
        node = node.setdefault(part, {})
    node[leaf] = value


def _leaf_paths(settings: dict, prefix: str = "") -> list[str]:
    paths = []
    for key, value in settings.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and path not in {s.path for s in SETTINGS}:
            paths.extend(_leaf_paths(value, path + "."))
        else:
            paths.append(path)
    return paths


def validate(settings: dict) -> list[str]:
    """Problems with a complete set of league settings; empty when it is valid."""
    errors = []
    known = {s.path for s in SETTINGS}
    errors += [f"unknown setting {p}" for p in _leaf_paths(settings) if p not in known]
    for s in SETTINGS:
        try:
            value = get_path(settings, s.path)
        except KeyError:
            errors.append(f"{s.path} is missing")
            continue
        if value is None:
            if not s.nullable:
                errors.append(f"{s.path} can't be null")
            continue
        if isinstance(value, bool) or not isinstance(value, s.kind):
            errors.append(f"{s.path} must be {s.description}, not {value!r}")
            continue
        if s.choices and value not in s.choices:
            errors.append(f"{s.path} must be one of {', '.join(s.choices)}")
        if s.minimum is not None and value < s.minimum:
            errors.append(f"{s.path} must be at least {s.minimum:g}")
        if s.maximum is not None and value > s.maximum:
            errors.append(f"{s.path} must be at most {s.maximum:g}")
    errors += _check_slots(settings)
    return errors


def _check_slots(settings: dict) -> list[str]:
    try:
        slots = get_path(settings, "roster_rules.chamber_slots")
        limit = get_path(settings, "roster_rules.roster_limit")
    except KeyError:
        return []
    if not isinstance(slots, dict) or not isinstance(limit, int):
        return []
    errors = []
    if set(slots) != {"house", "senate"}:
        return ["roster_rules.chamber_slots needs exactly house and senate"]
    for chamber, n in slots.items():
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            errors.append(f"roster_rules.chamber_slots.{chamber} must be a whole number of at least 0")
        elif n > limit:
            errors.append(f"roster_rules.chamber_slots.{chamber} can't exceed the roster limit ({limit})")
    if not errors and slots["house"] + slots["senate"] < limit:
        errors.append(f"chamber slots ({slots['house']} + {slots['senate']}) can't fill a roster of {limit}")
    return errors


def parse_overrides(pairs: list[str]) -> list[tuple[str, object]]:
    """`path=value` pairs from the command line. Values are JSON (numbers, null, objects);
    anything that isn't JSON is a string."""
    out = []
    for pair in pairs:
        path, sep, raw = pair.partition("=")
        if not sep or not path:
            raise ValueError(f"expected path=value, got {pair!r}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        out.append((path.strip(), value))
    return out


def complete(settings: dict) -> dict:
    """Fill settings that may be null and were left out (TOML has no null)."""
    out = deepcopy(settings)
    for s in SETTINGS:
        if s.nullable:
            try:
                get_path(out, s.path)
            except KeyError:
                set_path(out, s.path, None)
    return out


def resolve(preset: dict, overrides: list[tuple[str, object]]) -> dict:
    settings = deepcopy(preset)
    for path, value in overrides:
        set_path(settings, path, value)
    return settings


def league_dates(league_type: str, *, congress: int | None = None, session: int | None = None,
                 year: int | None = None, start: date | None = None,
                 end: date | None = None) -> tuple[date, date]:
    """Start and end (exclusive) of a league. Official timings follow the real calendar:
    a session or a Congress runs from January 3; a presidential term from January 20 of
    the year after a presidential election; a senatorial league spans a six-year class term."""
    def need(**values):
        missing = [k for k, v in values.items() if v is None]
        if missing:
            raise ValueError(f"a {league_type} league needs --{' and --'.join(missing)}")

    if league_type == "session":
        need(congress=congress, session=session)
        first = 1787 + 2 * congress + (session - 1)
        return date(first, 1, 3), date(first + 1, 1, 3)
    if league_type == "annual":
        need(year=year)
        return date(year, 1, 1), date(year + 1, 1, 1)
    if league_type == "representative":
        need(congress=congress)
        first = 1787 + 2 * congress
        return date(first, 1, 3), date(first + 2, 1, 3)
    if league_type == "presidential":
        need(year=year)
        if year % 4 != 1:
            raise ValueError("a presidential term starts in the year after a presidential election (2025, 2029, ...)")
        return date(year, 1, 20), date(year + 4, 1, 20)
    if league_type == "senatorial":
        need(year=year)
        if year % 2 != 1:
            raise ValueError("a Senate class term starts in an odd year (2025, 2027, ...)")
        return date(year, 1, 3), date(year + 6, 1, 3)
    if league_type == "flexible_private":
        need(start=start, end=end)
        if start >= end:
            raise ValueError("the league must end after it starts")
        return start, end
    raise ValueError(f"unknown league type {league_type!r}")


def can_change(start_date: date, today: date) -> bool:
    """Settings and ruleset are frozen once a league starts."""
    return today < start_date
