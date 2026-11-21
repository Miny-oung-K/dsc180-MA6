# Audit of teammate's branch (Exercise 3)

| Field | Value |
|---|---|
| Teammate repository | https://github.com/Miny-oung-K/dsc180-MA6, branch `verification` (commit `04e5cb1`, author brianzliu) |
| Auditor | `leakage-auditor` subagent (`.claude/agents/leakage-auditor.md` on that branch) |
| Model used for this run | Claude Opus 5.5, not the local `bikeshare-coder` (Ollama was not available to the run) |
| Date | 2026-11-20 |

## Auditor output (verbatim)

```
# Leakage audit: `verification` branch (`1db8010..04e5cb1`)

## Findings

**1. REPORT.md:3 chooses the model to deploy using the test split. The validation split ranks the two models the other way.**
- **Affected result:** the Exercise 5 conclusion, "I would deploy persistence ... yesterday's count is the better choice."
- **Evidence:** the R² and MAE in REPORT.md are the H2 2012 test numbers. They match what I reproduced: ridge 0.5833 / 947.1, persistence 0.5099 / 840.1. The branch never compares the models on validation, which is the split meant for this decision (CLAUDE.md: "Never tune on test"). On validation (H1 2012), in the same `reports/metrics.json`, ridge beats persistence on both metrics:
  - R² 0.6475 vs 0.4507
  - MAE 832.9 vs 900.6
- **Impact:** if the model is picked on validation, ridge wins under the MAE criterion the report itself uses. Persistence only wins on MAE in the test split. The test numbers can be reported as the final held-out estimate for whichever model validation selects, but they should not be the basis for the choice. As written, "deploy persistence" is a decision fitted to the test set, and validation contradicts it.
- **Not affected:** every number in REPORT.md is copied and computed correctly (0.5833 − 0.5099 = 0.0734; 947.1 − 840.1 = 107.0).

I found no other issues that change a number or invalidate a conclusion. In particular, none of the branch's code or config changes (`src/config.py`, `tests/test_contract.py`, `.claude/hooks/check_leakage.sh`, `.claude/settings.json`) changes a metric or weakens an existing guard.

## Checks run

**Data**
- `data/raw/bike_daily.csv` sha256 is `a6bed1577f6e4de56dcf...`, which matches the expected prefix. It was unchanged after `make all`.
- 728 rows from 2011-01-03 to 2012-12-31. The only missing calendar day is 2011-03-10.

**Model inputs (rule 1)**
- `feature_columns` returns 14 columns: temp, atemp, hum, windspeed, dayofweek, is_weekend, is_holiday, is_workday, month_sin, month_cos, weather_severity, cnt_lag_1, cnt_lag_7, cnt_roll_7.
- None of `casual`, `registered`, `cnt`, `cnt_2d_bfr`, `instant`, `yr` or `days_since_2011` is among them.
- The highest absolute correlation of any feature with `cnt` is 0.849 (`cnt_roll_7`). An OLS fit of `cnt` on all features over all rows, in-sample, gives R² 0.8285. Neither suggests the target is restated under another name.
- `season`, `mnth` and `weekday` are strings in this mirror, so they never enter the numeric feature set.

**Split and fitting (rule 2)**
- `temporal_split` (`src/train.py:56-62`) gives:
  - train: 2011-01-10 to 2011-12-31, 348 rows
  - valid: 2012-01-01 to 2012-06-30, 182 rows
  - test: 2012-07-01 to 2012-12-31, 184 rows
- All models are fit only on train rows (`src/train.py:78`).
- `StandardScaler.mean_` equals the train-row means. The `DummyRegressor` constant (3493.45) equals the train-row mean of `cnt`.
- Hurricane Sandy (2012-10-29, 22 rides) is in the test split.

**Calendar alignment (rule 3)**
- I recomputed `cnt_lag_1`, `cnt_lag_7` and `cnt_roll_7` for every one of the 714 rows by looking up actual calendar dates in the raw data, independently of the repo's code. There were 0 mismatches for each.
- The rolling mean shifts before it aggregates (`src/features.py:76`).
- The rows lost are 728 − 714 = 14, which is 7 warm-up rows plus 7 rows after the gap. That is the expected number.
- The branch adds no new predictor.

**Baselines (rule 4)**
- The mean and persistence baselines are scored on the same valid and test rows as ridge and HGB (`src/train.py:77-86`).
- The negative R² values are reported as they are: mean baseline −2.1441 on test, HGB −0.4975 on test.

**Reproducibility (rule 5)**
- `make features`, `make train` and `make all` all run.
- A second `make train` produced a byte-identical `reports/metrics.json`. HGB uses `random_state=0`, and the other models are deterministic.
- `make test`: 16 passed.

**Branch changes**
- `src/config.py`: adds `RAW_FEATURE_INPUTS` and `UNUSED_RAW_COLS`. Neither is used by `features.py` or `train.py`, and `FORBIDDEN` is unchanged, so no number changes.
- `tests/test_contract.py`: the two new tests (every raw column is classified; the weather encoder rejects unknown labels) add guards and remove none.
- `.claude/hooks/check_leakage.sh`: I ran it by hand with simulated JSON on stdin.
  - Edit to `src/features.py`: it ran pytest and exited 0.
  - Edit to `tests/`: it skipped. That is by design, since the hook only covers edits under `src/`, so test edits get no automatic run. This is a coverage limit of a new check, not a weakening of an existing one.
- `.claude/settings.json`: it denies writes to `data/raw/**` and only changes agent configuration, so it does not affect any number.

## Checks that could not run
- **The real hook in Claude Code:** I could not trigger the PostToolUse event here. I only checked the script's behaviour on simulated input, not that Claude Code wires it up or that its exit code 2 reaches the agent.
- **Ollama and the `bikeshare-coder` model** (`make model`, `make check-model`, `.claude/settings.json` model and endpoint): Ollama is not installed.
- **`docs/SEEDED_FAULTS.md`:** I did not re-run the recorded fault-injection transcripts, because that would mean editing tracked source files.
- **The "starter results" REPORT.md cites:** I could not check them separately from the current pipeline. They do match the metrics reproduced from this branch.
```

## Which findings I agree with

- **Finding 1 (REPORT.md picks the model on test): agree.** I reran `make train` myself and got the same validation numbers: ridge R² 0.6475 / MAE 832.9, persistence 0.4507 / 900.6. Choosing persistence because of its test MAE (840.1 vs 947.1) means the test set decided the model, which CLAUDE.md rules out. This changes the Exercise 5 conclusion, not any metric.
- **Hook skips edits under `tests/`: agree it is real, but it changes no number.** I am noting it and not counting it as a finding.

## Verdict

The `verification` branch is clean on everything that produces a number. No forbidden or target-derived column reaches the model. The split is by date, and every fit uses training rows only. The lags and the 7-day rolling mean line up with real calendar dates on all 714 rows. Both baselines are scored on the same rows as the models. `make all` reproduces `reports/metrics.json` byte-for-byte, and all 16 tests pass. The new contract tests, config sets and hook add guards without loosening any. The one problem is in the write-up: REPORT.md's Exercise 5 recommends persistence based on test-set MAE, while validation ranks ridge ahead on both R² and MAE. The model choice should be made and argued on validation, with test reported once as the held-out estimate. If Exercise 5 explicitly asks for the test-set comparison, the paragraph should still say that validation gives the opposite ranking.
