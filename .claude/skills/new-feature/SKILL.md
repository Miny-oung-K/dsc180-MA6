---
name: new-feature
description: Add a bikeshare predictor with a failing test first and measure its validation impact.
---

Add the feature described by $ARGUMENTS.

1. Explain when each input is available and stop if an input is unavailable at
   prediction time.
2. Record baseline validation R². Add a test in `tests/test_leakage.py` that
   checks a hand-computed value on a named date. Run it and record the expected
   failure in `docs/SEEDED_FAULTS.md`. Pause for the user to commit the test
   before implementing the feature.
3. Build the feature after calendar reindexing. Shift target values before any
   aggregation and update `LAG_WARMUP` if more history is needed.
4. Rebuild features, run the tests, and compare validation R² using the same
   time split and models. Keep the final test comparison for the end.
5. Record the availability argument and validation delta in
   `docs/DECISIONS.md`. If the validation R² gain is under 0.01, recommend
   dropping the feature and let the user decide.
