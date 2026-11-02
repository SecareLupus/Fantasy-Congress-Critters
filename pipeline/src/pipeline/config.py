import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CRITTERS_DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://critters:critters@localhost:5432/critters"
)

BILL_TYPES = ["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"]
