"""Guard rails on the ingest contract and the trained model's behaviour."""
import pandas as pd
import pytest
from sklearn.metrics import r2_score

from src.config import (
    FORBIDDEN,
    LAG_WARMUP,
    RAW,
    RAW_FEATURE_INPUTS,
    TARGET,
    UNUSED_RAW_COLS,
)
from src.features import build_features, encode_weather, feature_columns, reindex_to_calendar
from src.ingest import check_raw_checksum, load_raw
from src.train import MODELS, temporal_split


@pytest.fixture(scope="module")
def raw():
    return load_raw().sort_values("dteday").reset_index(drop=True)


@pytest.fixture(scope="module")
def feats(raw):
    return build_features(raw)


def test_all_raw_columns_are_classified():
    raw_columns = set(pd.read_csv(RAW, nrows=0).columns)
    classified = FORBIDDEN | RAW_FEATURE_INPUTS | UNUSED_RAW_COLS | {"dteday"}
    unclassified = raw_columns - classified
    assert not unclassified, f"unclassified raw columns: {sorted(unclassified)}"


def test_weather_encoder_rejects_unknown_labels():
    with pytest.raises(ValueError, match="unmapped weather labels.*UNKNOWN"):
        encode_weather(pd.Series(["GOOD", "UNKNOWN"]))


def test_calendar_is_complete_before_lagging(raw):
    """The reindexed frame must have no gaps, or the lags are wrong."""
    grid = reindex_to_calendar(raw)
    assert set(grid.dteday.diff().dropna().dt.days.unique()) == {1}


def test_only_expected_rows_are_dropped(raw, feats):
    """Rows may only vanish for the lag warm-up or downstream of a genuinely
    absent day -- never because an encoder produced a silent NaN.

    Accounting: the first LAG_WARMUP days have no complete history. Each
    absent calendar day m costs the LAG_WARMUP rows after it (cnt_lag_1 is
    NaN on m+1, cnt_roll_7 is NaN on m+1..m+7, cnt_lag_7 on m+7; their
    union is 7 rows). Day m itself was never in `raw`, so it is not a loss.
    The bound is exact for the current feature set; add a longer lag and
    LAG_WARMUP in src/config.py must grow with it.
    """
    full = pd.date_range(raw.dteday.min(), raw.dteday.max(), freq="D")
    missing_days = len(full) - len(raw)
    allowed_loss = LAG_WARMUP + LAG_WARMUP * missing_days
    lost = len(raw) - len(feats)
    assert lost <= allowed_loss, f"lost {lost} rows; expected at most {allowed_loss}"


def test_beats_the_mean_baseline(feats):
    """A model that cannot beat predicting the training mean is not a result."""
    cols = feature_columns(feats)
    train, _, test = temporal_split(feats)
    ridge = MODELS["ridge"]
    ridge.fit(train[cols], train[TARGET])
    assert r2_score(test[TARGET], ridge.predict(test[cols])) > 0.4


def test_persistence_baseline_is_reported():
    """The baseline that matters for a lag-driven model is 'yesterday again'.
    It must be in the comparison, whatever its score."""
    assert "baseline_persistence" in MODELS


def test_raw_checksum_matches_pinned_file():
    assert check_raw_checksum(RAW).startswith("a6bed1577f6e4de5")


def test_raw_checksum_rejects_modified_copy(tmp_path):
    """A one-byte change to the raw file must be refused."""
    copy = tmp_path / "bike_daily.csv"
    copy.write_bytes(RAW.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        check_raw_checksum(copy)
