"""The tests that make the agent honest.

test_no_forbidden_features is the single most valuable test in this repo:
casual + registered == cnt exactly, so any model handed those columns
scores R^2 = 1.0 and looks brilliant while having learned nothing.
"""
import pandas as pd
import pytest

from src.config import FORBIDDEN, TARGET
from src.features import build_features, feature_columns
from src.ingest import load_raw


@pytest.fixture(scope="module")
def feats():
    return build_features(load_raw())


def test_leakage_identity_holds(feats):
    """Documents *why* casual and registered are forbidden."""
    assert (feats.casual + feats.registered == feats[TARGET]).all()


def test_no_forbidden_features(feats):
    """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
    construction, so this cannot discover a *new* leaky column. What it
    catches is someone editing feature_columns() or FORBIDDEN -- which is
    exactly the fault the Step 7 hook demonstrates."""
    cols = set(feature_columns(feats))
    assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"


def test_lags_are_true_calendar_lags(feats):
    """cnt_lag_1 for date d must equal cnt on d-1, in calendar days."""
    by_date = feats.set_index("dteday")[TARGET]
    checked = 0
    for date, lag in feats.set_index("dteday").cnt_lag_1.items():
        prev = date - pd.Timedelta(days=1)
        if prev in by_date.index:
            assert lag == pytest.approx(by_date[prev]), f"bad lag at {date.date()}"
            checked += 1
    assert checked > 600, "too few rows actually verified"


def test_lag_is_not_the_target(feats):
    assert not (feats.cnt_lag_1 == feats[TARGET]).all()


def test_rolling_mean_excludes_today(feats):
    """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
    by_date = feats.set_index("dteday")[TARGET]
    date = feats.dteday.iloc[200]
    window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
    if all(d in by_date.index for d in window):
        expected = sum(by_date[d] for d in window) / 7
        assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)


def test_no_missing_values(feats):
    assert feats[feature_columns(feats)].isna().sum().sum() == 0


def test_dates_are_sorted_and_unique(feats):
    assert feats.dteday.is_monotonic_increasing
    assert feats.dteday.is_unique


def test_roll_3_is_mean_of_three_preceding_days(feats):
    """cnt_roll_3 on 2011-06-15 must be the mean of cnt on the three calendar
    days *before* it, never including the day itself.

    Hand-computed from data/raw/bike_daily.csv:
      2011-06-12  cnt = 4460
      2011-06-13  cnt = 5020
      2011-06-14  cnt = 4891
      mean = 14371 / 3 = 4790.333...
    (Including 2011-06-15 itself, cnt = 5180, would give 5030.333 -- leakage.)
    """
    row = feats.set_index("dteday").loc[pd.Timestamp("2011-06-15")]
    assert row.cnt_roll_3 == pytest.approx((4460 + 5020 + 4891) / 3)


# Every target-derived feature and the calendar days it must average.
TARGET_LAGS = {
    "cnt_lag_1": [1],
    "cnt_lag_7": [7],
    "cnt_roll_7": list(range(1, 8)),
    "cnt_roll_3": list(range(1, 4)),
}


def test_all_target_lags_match_calendar_days(feats):
    """Every lag and rolling feature, on every row, equals the mean of cnt on
    the exact calendar days it claims -- and none of those days may be the
    missing 2011-03-10. This fails if reindex_to_calendar is skipped (rows
    after the gap would silently use the wrong day) or if any shift is off
    by one."""
    raw = load_raw().set_index("dteday")[TARGET]
    by_date = feats.set_index("dteday")
    for col, offsets in TARGET_LAGS.items():
        assert col in by_date.columns, f"{col} missing from features"
        for date, value in by_date[col].items():
            days = [date - pd.Timedelta(days=k) for k in offsets]
            missing = [d.date() for d in days if d not in raw.index]
            assert not missing, f"{col} on {date.date()} relies on missing day(s) {missing}"
            assert value == pytest.approx(raw[days].mean()), f"{col} wrong on {date.date()}"


@pytest.mark.parametrize("day", ["2011-06-15", "2012-03-01", "2012-10-29"])
def test_no_feature_changes_when_same_day_target_changes(day):
    """Catches same-day leakage under any column name. Change cnt (and its
    components, keeping casual + registered == cnt) on one date only: every
    model input on that date must stay the same, because nothing about
    today's rides is known when today is forecast."""
    raw = load_raw()
    date = pd.Timestamp(day)
    bumped = raw.copy()
    on_day = bumped.dteday == date
    for col in ["casual", "registered", "cnt"]:
        bumped.loc[on_day, col] = bumped.loc[on_day, col] * 2 + 500
    before = build_features(raw)
    after = build_features(bumped)
    cols = feature_columns(before)
    row_before = before.set_index("dteday").loc[date, cols].astype(float)
    row_after = after.set_index("dteday").loc[date, cols].astype(float)
    changed = row_before.index[(row_before - row_after).abs() > 1e-9].tolist()
    assert not changed, f"features that move with same-day cnt on {day}: {changed}"
