# Seeded faults and red test output

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
