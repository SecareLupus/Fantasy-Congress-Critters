"""Fetch raw source files into data/raw. Files already on disk are skipped unless force=True."""

import json
import shutil
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

from .config import BILL_TYPES, RAW_DIR

GOVINFO_BILLSTATUS = "https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{bill_type}/BILLSTATUS-{congress}-{bill_type}.zip"
HOUSE_ROLL_CALL = "https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"
HOUSE_MEMBER_DATA = "https://clerk.house.gov/xml/lists/MemberData.xml"
SENATE_COMMITTEE = "https://www.senate.gov/general/committee_membership/committee_memberships_{code}.xml"
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


class NotPublished(Exception):
    """The source has no file at this address yet (a new Congress's first days)."""


RETRY_WAITS = (5, 30)  # seconds before the second and third attempts


def _open(req: urllib.request.Request, timeout: int):
    """urlopen, retrying timeouts, dropped connections and 5xx responses."""
    for wait in (*RETRY_WAITS, None):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code < 500 or wait is None:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if wait is None:
                raise
        time.sleep(wait)


def _fetch(url: str, dest: Path, force: bool) -> bool:
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "critters-pipeline"})
    with _open(req, 120) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.rename(dest)
    return True


def refresh(url: str, dest: Path) -> bool:
    """Fetch `url` into `dest` if it changed; True if the file on disk is new.

    Sends the ETag and Last-Modified saved from the last fetch (in dest.meta.json), and
    compares bytes as well, since not every server honors them.
    """
    meta_path = dest.with_suffix(dest.suffix + ".meta.json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() and dest.exists() else {}
    headers = {"User-Agent": "critters-pipeline"}
    if meta.get("etag"):
        headers["If-None-Match"] = meta["etag"]
    if meta.get("last_modified"):
        headers["If-Modified-Since"] = meta["last_modified"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with _open(urllib.request.Request(url, headers=headers), 120) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out)
            meta = {"etag": resp.headers.get("ETag"), "last_modified": resp.headers.get("Last-Modified")}
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return False
        if e.code == 404:
            raise NotPublished(url) from e
        raise
    changed = not dest.exists() or tmp.read_bytes() != dest.read_bytes()
    tmp.rename(dest)
    meta_path.write_text(json.dumps(meta))
    return changed


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


def refresh_billstatus(congress: int) -> list[str]:
    """Bill types whose BILLSTATUS zip changed; GovInfo rebuilds them daily. A new Congress
    has no zip for a bill type until its first bill of that type."""
    changed = []
    for t in BILL_TYPES:
        try:
            if refresh(GOVINFO_BILLSTATUS.format(congress=congress, bill_type=t), billstatus_path(congress, t)):
                changed.append(t)
        except NotPublished:
            pass
    return changed


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


def refresh_legislators() -> list[str]:
    return [name for name in LEGISLATOR_FILES if refresh(LEGISLATORS.format(ref="main", name=name),
                                                         legislators_path(name))]


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


def official_rosters_dir(congress: int) -> Path:
    """Roster snapshots built from the chambers' own committee lists, one per change."""
    return RAW_DIR / "rosters" / "official" / str(congress)


def fetch_official_rosters(senate_codes: list[str]) -> tuple[bytes, dict[str, bytes]]:
    """The House Clerk's MemberData.xml and senate.gov's membership file for each Senate
    or joint committee. All or nothing: a missing committee would end its seats."""
    def get(url: str) -> bytes:
        with _open(urllib.request.Request(url, headers={"User-Agent": "critters-pipeline"}), 60) as resp:
            return resp.read()
    house = get(HOUSE_MEMBER_DATA)
    senate = {code: get(SENATE_COMMITTEE.format(code=code)) for code in senate_codes}
    return house, senate


def house_votes_dir(congress: int, session: int) -> Path:
    return RAW_DIR / "votes" / "house" / f"{congress}-{session}"


def download_house_votes(congress: int, force: bool = False, sessions: tuple[int, ...] = (1, 2)) -> int:
    """Fetch every House roll call for the sessions; the Clerk numbers them from 1 each year.

    Past the last roll call the Clerk answers 200 with a short error document, not 404,
    so each file is checked and the first invalid one (after a retry) ends the session.
    """
    total = 0
    for session in sessions:
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


def refresh_senate_votes(congress: int) -> bool:
    """True if any of Voteview's three files for the Congress changed; NotPublished before
    its first Senate vote."""
    return any([refresh(VOTEVIEW.format(kind=kind, congress=congress), voteview_path(congress, kind))
                for kind in VOTEVIEW_KINDS])


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
