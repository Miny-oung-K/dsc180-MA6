# Seeded faults

The first three faults ran in disposable copies through Claude Code, using
`deepseek/deepseek-v4.1-flash-1017` via OpenRouter with effort set to max.
The standalone pytest output and the live PostToolUse hook stderr are shown
for each fault. After each repair, the source matched its original contents
and all 16 tests passed.

## Forbidden count in the model input

```diff
--- a/src/features.py
+++ b/src/features.py
@@ -82,5 +82,5 @@
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN or c == TARGET]
 
 
```

```text
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_leakage.py::test_no_forbidden_features
F                                                                        [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'cnt'}
E       assert not ({'atemp', 'cnt', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'dayofweek', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed in 0.58s
[exit 1]
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_leakage.py::test_no_forbidden_features
.                                                                        [100%]
1 passed in 0.30s
[exit 0]
```

Claude Code repair used one user prompt and reported 2 model turns in its session result. The live Edit event reported `test_no_forbidden_features`.

Hook stderr from the live Claude Code Edit event

```text
.......F........                                                         [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'cnt'}
E       assert not ({'atemp', 'cnt', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'dayofweek', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 15 passed in 1.90s
[hook exit 2]
```

On merged commit `d9cdcc4`, we reapplied the diff in a disposable copy, invoked the hook with an Edit payload, restored the original source, and ran `make test`.

```text
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
[hook exit 2]
17 passed in 1.51s
```

## Rolling mean includes the current day

```diff
--- a/src/features.py
+++ b/src/features.py
@@ -74,5 +74,5 @@
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
 
     return out.dropna().reset_index(drop=True)
```

```text
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_leakage.py::test_rolling_mean_excludes_today
F                                                                        [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1531.428571
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1789.857143

[714 rows x 28 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed in 0.35s
[exit 1]
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_leakage.py::test_rolling_mean_excludes_today
.                                                                        [100%]
1 passed in 0.34s
[exit 0]
```

Claude Code repair used one user prompt and reported 2 model turns in its session result. The live Edit event reported `test_rolling_mean_excludes_today`.

Hook stderr from the live Claude Code Edit event

```text
..........F.....                                                         [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1531.428571
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1789.857143

[714 rows x 28 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 15 passed in 1.35s
[hook exit 2]
```

On merged commit `d9cdcc4`, we reapplied the diff in a disposable copy, invoked the hook with an Edit payload, restored the original source, and ran `make test`.

```text
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
[hook exit 2]
17 passed in 1.43s
```

## Weather encoder silently accepts unknown labels

```diff
--- a/src/features.py
+++ b/src/features.py
@@ -25,8 +25,4 @@
     error and no warning.
     """
-    known = series.dropna()
-    unknown = set(known.unique()) - set(WEATHER_ORDER)
-    if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
     return series.map(WEATHER_ORDER).astype(float)
 
```

```text
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_contract.py::test_weather_encoder_rejects_unknown_labels
F                                                                        [100%]
=================================== FAILURES ===================================
_________________ test_weather_encoder_rejects_unknown_labels __________________

    def test_weather_encoder_rejects_unknown_labels():
>       with pytest.raises(ValueError, match="unmapped weather labels.*UNKNOWN"):
E       Failed: DID NOT RAISE <class 'ValueError'>

tests/test_contract.py:37: Failed
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed in 1.40s
[exit 1]
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_contract.py::test_weather_encoder_rejects_unknown_labels
.                                                                        [100%]
1 passed in 1.07s
[exit 0]
```

Claude Code repair used one user prompt and reported 2 model turns in its session result. The live Edit event reported `test_weather_encoder_rejects_unknown_labels`.

Hook stderr from the live Claude Code Edit event

```text
.F..............                                                         [100%]
=================================== FAILURES ===================================
_________________ test_weather_encoder_rejects_unknown_labels __________________

    def test_weather_encoder_rejects_unknown_labels():
>       with pytest.raises(ValueError, match="unmapped weather labels.*UNKNOWN"):
E       Failed: DID NOT RAISE <class 'ValueError'>

tests/test_contract.py:37: Failed
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed, 15 passed in 1.22s
[hook exit 2]
```

On merged commit `d9cdcc4`, we reapplied the diff in a disposable copy, invoked the hook with an Edit payload, restored the original source, and ran `make test`.

```text
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
[hook exit 2]
17 passed in 1.45s
```

## Raw CSV overwritten from Bash

This copy ran in the temporary checkout. The assignment's PostToolUse matcher
is Edit|Write, so a Bash copy is outside its trigger. The header test caught
the unexpected column when run explicitly. A checksum check in `make data`
would also catch changes to the values when the header stays the same.

```text
$ cp -v extra-column.csv data/raw/bike_daily.csv
extra-column.csv -> data/raw/bike_daily.csv
[exit 0]
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests/test_contract.py::test_all_raw_columns_are_classified
F                                                                        [100%]
=================================== FAILURES ===================================
_____________________ test_all_raw_columns_are_classified ______________________

    def test_all_raw_columns_are_classified():
        raw_columns = set(pd.read_csv(RAW, nrows=0).columns)
        classified = FORBIDDEN | RAW_FEATURE_INPUTS | UNUSED_RAW_COLS | {"dteday"}
        unclassified = raw_columns - classified
>       assert not unclassified, f"unclassified raw columns: {sorted(unclassified)}"
E       AssertionError: unclassified raw columns: ['unexpected_metric']
E       assert not {'unexpected_metric'}

tests/test_contract.py:33: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_all_raw_columns_are_classified - Assertio...
1 failed in 1.15s
[exit 1]
$ /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q --color=no tests
................                                                         [100%]
16 passed in 1.14s
[exit 0]
```

## Exercise 1: failing feature test (before implementation)

Feature: `cnt_roll_3`, the mean ridership over the three calendar days before date *d*.
Test: `tests/test_leakage.py::test_roll_3_is_mean_of_three_preceding_days` (2011-06-15, expected (4460 + 5020 + 4891) / 3 = 4790.33).
Committed before `src/features.py` was changed. It fails because the column does not exist yet, which is the right reason.

Actual `make test` output:

```
python -m pytest tests/ -q
...........F...                                                          [100%]
=================================== FAILURES ===================================
_________________ test_roll_3_is_mean_of_three_preceding_days __________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

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
>       assert row.cnt_roll_3 == pytest.approx((4460 + 5020 + 4891) / 3)
               ^^^^^^^^^^^^^^

tests/test_leakage.py:81: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = instant                   166.0
season                   SPRING
yr                       2011.0
mnth                  ...        4891.0
cnt_lag_7                4401.0
cnt_roll_7          4605.571429
Name: 2011-06-15 00:00:00, dtype: object
name = 'cnt_roll_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'Series' object has no attribute 'cnt_roll_3'. Did you mean: 'cnt_roll_7'?

../../venv/lib/python3.12/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_roll_3_is_mean_of_three_preceding_days - A...
1 failed, 14 passed in 1.56s
make: *** [Makefile:16: test] Error 1
```
