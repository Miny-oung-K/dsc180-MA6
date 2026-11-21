# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

### Verification decisions

- 2026-11-20: Classify raw headers explicitly so a new column fails the data contract, even if its name looks harmless.
- 2026-11-20: Run both contract and leakage tests in the Edit/Write hook so removing the unknown-weather guard is caught.
- 2026-11-20: Add `/seed-fault` to `CLAUDE.md` so each fault run records what broke, the live hook stderr, and whether the repair restored the source.
- 2026-11-20: Try predicting `cnt / cnt_roll_7` with HGB in validation and invert with the same prior-only mean. On the baseline features, validation R² rose from 0.2185 to 0.7454 and MAE fell from 1296.6 to 687.2 rides. The prior seven days provide a known scale before the forecast day. The committed pipeline metrics use untransformed counts.
- 2026-11-20: Keep the three-day rolling mean and its test as an experiment. Exclude it from the selected model inputs because ridge and HGB both lost validation R². Report the comparison under `with_cnt_roll_3` when the feature is present.
- 2026-11-20: Exercise 5 deployment choice made on validation, not test (per Member A's audit in docs/AUDIT.md). Ridge beats persistence on validation R^2 (0.6475 vs 0.4507) and MAE (832.9 vs 900.6), so ridge is recommended. The test MAE reversal (947.1 vs 840.1) is reported as a caveat, not used to pick the model.
