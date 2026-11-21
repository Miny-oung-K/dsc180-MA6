"""Stage 1: fetch the raw dataset and assert its shape.

Run: python -m src.ingest
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

import pandas as pd

from src.config import DATA_URL, RAW, RAW_SHA256_PREFIX

EXPECTED_MIN_ROWS = 700
REQUIRED_COLS = {"dteday", "cnt", "casual", "registered", "temp", "hum", "windspeed"}


def download(force: bool = False) -> None:
    if RAW.exists() and not force:
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DATA_URL, RAW)


def check_raw_checksum(path: Path = RAW) -> str:
    """Fail loudly if the raw CSV is not the pinned file."""
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if not digest.startswith(RAW_SHA256_PREFIX):
        raise ValueError(
            f"raw data checksum mismatch: {Path(path).name} sha256 {digest[:16]}..., "
            f"expected {RAW_SHA256_PREFIX}... -- data/raw/ must not change"
        )
    return digest


def load_raw() -> pd.DataFrame:
    check_raw_checksum()
    df = pd.read_csv(RAW, parse_dates=["dteday"])
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"raw data is missing required columns: {sorted(missing)}")
    if len(df) < EXPECTED_MIN_ROWS:
        raise ValueError(f"raw data has only {len(df)} rows; expected >= {EXPECTED_MIN_ROWS}")
    return df


if __name__ == "__main__":
    download(force="--force" in sys.argv)
    df = load_raw()
    print(f"OK ingest: {len(df)} rows, {df.dteday.min().date()} -> {df.dteday.max().date()}")
