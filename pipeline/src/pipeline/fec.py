"""Read FEC bulk files."""

import zipfile
from pathlib import Path

# weball{yy}.txt columns (FEC "all candidates" file description)
CAND_ID, TTL_RECEIPTS = 0, 5


def receipts(path: Path) -> dict[str, float]:
    """FEC candidate id -> total receipts for the cycle."""
    out: dict[str, float] = {}
    with zipfile.ZipFile(path) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".txt"))
        for line in zf.read(name).decode("latin-1").splitlines():
            f = line.split("|")
            if len(f) > TTL_RECEIPTS:
                out[f[CAND_ID]] = float(f[TTL_RECEIPTS] or 0)
    return out
