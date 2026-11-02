"""Fetch raw source files into data/raw. Files already on disk are skipped unless force=True."""

import shutil
import urllib.request
from pathlib import Path

from .config import BILL_TYPES, RAW_DIR

GOVINFO_BILLSTATUS = "https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{bill_type}/BILLSTATUS-{congress}-{bill_type}.zip"
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
