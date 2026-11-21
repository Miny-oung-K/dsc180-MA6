# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

The five lines above are from the starter. The dated entries record when
this team actually used the test scores.

- 2026-11-20: Add `cnt_roll_3` (mean cnt over d-3..d-1). Availability: all three days are observed before d, built with shift(1) before rolling(3). Validation R^2 ridge 0.6475 -> 0.6439 (-0.0036), hgb 0.2185 -> 0.1983 (-0.0202); MAE ridge 832.9 -> 836.5. Below the +0.01 bar and negative: recommend dropping. It overlaps with `cnt_lag_1` and `cnt_roll_7`.

### Verification decisions

- 2026-11-20: Classify raw headers explicitly so a new column fails the data contract, even if its name looks harmless.
- 2026-11-20: Run both contract and leakage tests in the Edit/Write hook so removing the unknown-weather guard is caught.
- 2026-11-20: Add `/seed-fault` to `CLAUDE.md` so each fault run records what broke, the live hook stderr, and whether the repair restored the source.
- 2026-11-20: Try predicting `cnt / cnt_roll_7` with HGB in validation and invert with the same prior-only mean. On the baseline features, validation R² rose from 0.2185 to 0.7454 and MAE fell from 1296.6 to 687.2 rides. The prior seven days provide a known scale before the forecast day. The committed pipeline metrics use untransformed counts.
- 2026-11-20: Brian kept the three-day rolling mean and its test for comparison. Both models lost validation R², so the feature was excluded from the selected inputs. The comparison appears under `with_cnt_roll_3`.
- 2026-11-20: Minyoung's pre-merge audit reproduced the starter test metrics and found that the Exercise 5 draft had used test MAE to recommend persistence. Minyoung revised the recommendation using validation, where ridge has R² 0.6475 vs 0.4507 and MAE 832.9 vs 900.6. The higher ridge test MAE remains a deployment caveat.
- 2026-11-20: Minyoung merged `feature` and `verification` after the branch audits. The merged `make all` run generated the final count-target metrics for `REPORT.md`.
- 2026-11-20: Exercise 4 final check used `--ratio-target --final` after choosing the ratio target on validation. The separate run reproduced validation R² 0.7454 and MAE 687.2 and scored test R² 0.6416 and MAE 810.1. The committed metrics use untransformed counts.
- 2026-11-20: The headline compares ridge and HGB with the baselines. Mean daily rides in the raw data rose 63%, and 104 of 184 test days exceeded the training maximum. Minyoung used hosted Claude Opus 5.5 with instructor permission.
- 2026-11-20: Audit run: `agent/audit.py` on the merged repo with DeepSeek V4.1 Flash 1017 via OpenRouter. Result in `reports/audit.jsonl`: leakage none, temporal_ok, baseline_reported and reproducible all true, no findings, confidence high. Nothing to fix.
- 2026-11-20: Keep the starter's daily ride-count target and leakage exclusions, chronological split, and mean and persistence baselines. These choices keep the comparisons on the same task and dates.
- 2026-11-20: Implement the fourth-fault catch: `load_raw()` checks the raw CSV sha256 against `RAW_SHA256_PREFIX` in `src/config.py`, so a Bash copy into `data/raw/` fails `make data`, `make features` and `make test`. Two contract tests added (19 pass); metrics unchanged.
- 2026-11-20: Brian's three fault-verification commits (forbidden count, same-day rolling, unknown weather) recorded the live hook evidence in `docs/SEEDED_FAULTS.md`; no code changed.
- 2026-11-20: Close two test gaps found in the final review. (1) Every lag and rolling feature is checked against exact calendar days on every row, so skipping `reindex_to_calendar` or an off-by-one shift now fails. (2) A perturbation test changes same-day `cnt` and requires every model input on that day to stay unchanged, so a renamed copy of today's count (found by Brian's agent) fails and the hook exits 2. 23 tests pass.
- 2026-11-20: Seeded fault 1 (forbidden target column in feature_columns) committed on purpose so the history shows it; `make test` goes red: 4 failed, 19 passed in 2.40s.
- 2026-11-20: Fixed seeded fault 1 by restoring the original source; `make test`: 23 passed in 2.37s.
