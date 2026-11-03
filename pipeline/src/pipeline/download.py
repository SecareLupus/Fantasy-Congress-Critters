"""Fetch raw source files into data/raw. Files already on disk are skipped unless force=True."""

import shutil
import time
import urllib.request
from pathlib import Path

from .config import BILL_TYPES, RAW_DIR

GOVINFO_BILLSTATUS = "https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{bill_type}/BILLSTATUS-{congress}-{bill_type}.zip"
HOUSE_ROLL_CALL = "https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"
VOTEVIEW = "https://voteview.com/static/data/out/{kind}/S{congress}_{kind}.csv"
VOTEVIEW_KINDS = ["rollcalls", "votes", "members"]
LEGISLATORS = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/{name}"
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
        fetched = _fetch(LEGISLATORS.format(name=name), dest, force)
        print(f"{'fetched' if fetched else 'cached '} {dest.relative_to(RAW_DIR)}")
        paths.append(dest)
    return paths


def session_year(congress: int, session: int) -> int:
    return 1787 + 2 * congress + (session - 1)


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
