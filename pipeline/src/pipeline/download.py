"""Fetch raw source files into data/raw. Files already on disk are skipped unless force=True."""

import json
import shutil
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

from .config import BILL_TYPES, RAW_DIR

GOVINFO_BILLSTATUS = "https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{bill_type}/BILLSTATUS-{congress}-{bill_type}.zip"
HOUSE_ROLL_CALL = "https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"
VOTEVIEW = "https://voteview.com/static/data/out/{kind}/S{congress}_{kind}.csv"
VOTEVIEW_KINDS = ["rollcalls", "votes", "members"]
FEC_SUMMARY = "https://www.fec.gov/files/bulk-downloads/{cycle}/weball{yy}.zip"
LEGISLATORS = "https://raw.githubusercontent.com/unitedstates/congress-legislators/{ref}/{name}"
LEGISLATORS_COMMITS = (
    "https://api.github.com/repos/unitedstates/congress-legislators/commits"
    "?path={name}&since={since}&until={until}&per_page=100"
)
LEGISLATOR_FILES = [
    "legislators-current.yaml",
    "legislators-historical.yaml",
    "committees-current.yaml",
    "committees-historical.yaml",
    "committee-membership-current.yaml",
]


def _fetch(url: str, dest: Path, force: bool) -> bool:
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "critters-pipeline"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.rename(dest)
    return True


def billstatus_path(congress: int, bill_type: str) -> Path:
    return RAW_DIR / "billstatus" / str(congress) / f"{bill_type}.zip"


def download_billstatus(congress: int, force: bool = False) -> list[Path]:
    paths = []
    for bill_type in BILL_TYPES:
        dest = billstatus_path(congress, bill_type)
        url = GOVINFO_BILLSTATUS.format(congress=congress, bill_type=bill_type)
        fetched = _fetch(url, dest, force)
        print(f"{'fetched' if fetched else 'cached '} {dest.relative_to(RAW_DIR)}")
        paths.append(dest)
    return paths


def legislators_path(name: str) -> Path:
    return RAW_DIR / "legislators" / name


def download_legislators(force: bool = False) -> list[Path]:
    paths = []
    for name in LEGISLATOR_FILES:
        dest = legislators_path(name)
        fetched = _fetch(LEGISLATORS.format(ref="main", name=name), dest, force)
        print(f"{'fetched' if fetched else 'cached '} {dest.relative_to(RAW_DIR)}")
        paths.append(dest)
    return paths


def session_year(congress: int, session: int) -> int:
    return 1787 + 2 * congress + (session - 1)


def congress_dates(congress: int) -> tuple[date, date]:
    """A Congress runs from noon on January 3 to noon on January 3 two years later."""
    start = session_year(congress, 1)
    return date(start, 1, 3), date(start + 2, 1, 3)


def roster_history_dir(congress: int) -> Path:
    return RAW_DIR / "legislators" / "committee-membership-history" / str(congress)


def download_roster_history(congress: int, force: bool = False) -> list[Path]:
    """Every version of committee-membership-current.yaml committed during the Congress.

    Each file is named for its commit time (when the change reached the main branch),
    which is the date the roster builder treats it as observed.
    """
    start, end = congress_dates(congress)
    name = "committee-membership-current.yaml"
    url = LEGISLATORS_COMMITS.format(name=name, since=f"{start}T00:00:00Z", until=f"{end}T00:00:00Z")
    req = urllib.request.Request(url, headers={"User-Agent": "critters-pipeline"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        commits = json.load(resp)
    paths = []
    for commit in commits:
        committed = datetime.fromisoformat(commit["commit"]["committer"]["date"])
        dest = roster_history_dir(congress) / f"{committed:%Y%m%dT%H%M%S}_{commit['sha'][:10]}.yaml"
        _fetch(LEGISLATORS.format(ref=commit["sha"], name=name), dest, force)
        paths.append(dest)
    print(f"roster history {congress}: {len(paths)} snapshots")
    return sorted(paths)


def house_votes_dir(congress: int, session: int) -> Path:
    return RAW_DIR / "votes" / "house" / f"{congress}-{session}"


def download_house_votes(congress: int, force: bool = False) -> int:
    """Fetch every House roll call for both sessions; the Clerk numbers them from 1 each year.

    Past the last roll call the Clerk answers 200 with a short error document, not 404,
    so each file is checked and the first invalid one (after a retry) ends the session.
    """
    total = 0
    for session in (1, 2):
        year = session_year(congress, session)
        dest_dir = house_votes_dir(congress, session)
        roll, fetched = 1, 0
        while True:
            url = HOUSE_ROLL_CALL.format(year=year, roll=roll)
            dest = dest_dir / f"roll{roll:03d}.xml"
            for attempt in range(2):
                new = _fetch(url, dest, force)
                if b"<rollcall-vote>" in dest.read_bytes():
                    fetched += new
                    break
                dest.unlink()
                time.sleep(2)
            else:
                break
            roll += 1
        print(f"house {congress}-{session}: {roll - 1} roll calls ({fetched} fetched)")
        total += roll - 1
    return total


def voteview_path(congress: int, kind: str) -> Path:
    return RAW_DIR / "votes" / "senate" / f"S{congress}_{kind}.csv"


def download_senate_votes(congress: int, force: bool = False) -> list[Path]:
    """Senate roll calls from Voteview; senate.gov blocks automated downloads."""
    paths = []
    for kind in VOTEVIEW_KINDS:
        dest = voteview_path(congress, kind)
        fetched = _fetch(VOTEVIEW.format(kind=kind, congress=congress), dest, force)
        print(f"{'fetched' if fetched else 'cached '} {dest.relative_to(RAW_DIR)}")
        paths.append(dest)
    return paths


def fec_summary_path(cycle: int) -> Path:
    return RAW_DIR / "fec" / f"weball{cycle % 100:02d}.zip"


def download_fec_summary(cycle: int, force: bool = False) -> Path:
    """FEC all-candidates summary: total receipts per candidate for a two-year cycle."""
    dest = fec_summary_path(cycle)
    fetched = _fetch(FEC_SUMMARY.format(cycle=cycle, yy=f"{cycle % 100:02d}"), dest, force)
    print(f"{'fetched' if fetched else 'cached '} {dest.relative_to(RAW_DIR)}")
    return dest


def pricing_cycle(congress: int, session: int) -> int:
    """The last FEC cycle complete when the session opens."""
    year = session_year(congress, session)
    return year - 1 if (year - 1) % 2 == 0 else year - 2
