# Branch audit

## Member B review of Member A's feature branch

- Branch [feature](https://github.com/Miny-oung-K/dsc180-MA6/tree/feature)
- Audited commit [3307161af5f63e38f48cca952b09d7763d726e3e](https://github.com/Miny-oung-K/dsc180-MA6/commit/3307161af5f63e38f48cca952b09d7763d726e3e)
- Red-test commit [6723b38](https://github.com/Miny-oung-K/dsc180-MA6/commit/6723b38)
- Claude Code agent `leakage-auditor`, DeepSeek V4.1 Flash 1017 via OpenRouter, effort set to max

The first tool-enabled run timed out. The successful run used
`claude --agent leakage-auditor` with the feature, config, training and
leakage-test sources from the audited commit and the local results below.

## Local verification

- The feature checkout passed all 15 tests.
- An independent lookup matched `cnt_roll_3` to the previous three calendar
  days on all 714 modeled rows. The fitted split counts were 348, 182 and 184.
- The pinned environment reproduced the branch's ridge validation R² of
  0.6439 and HGB validation R² of 0.1983 with the feature, versus 0.6475
  and 0.2185 with the starter inputs.

## Claude Code output

````text
## Verdict

**No issue found that changes a reported score or invalidates a conclusion.** The feature set is target-clean, the split and preprocessing are temporally correct, and both baselines are scored on the same rows. Two scope caveats are noted below; neither is a demonstrated defect.

## What I verified (static read of the excerpts)

1. **Model inputs contain no same-day target or restatement.**
   `feature_columns` returns all numeric columns minus `FORBIDDEN` (`src/features.py:84-87`), and `FORBIDDEN` covers `cnt`, `casual`, `registered` (`src/config.py:31`), `instant`, `yr`, `days_since_2011` (`src/config.py:37`), and `cnt_2d_bfr` (`src/config.py:43`, combined at `:46`). Enumerating the remaining numeric columns from the documented mirror schema yields only calendar/weather columns and the four explicit lags. The target and both arithmetic components are absent; `tests/test_leakage.py:22` documents and checks the `casual + registered == cnt` identity.

2. **All target-derived features are shifted before aggregation.**
   `cnt_lag_1 = shift(1)`, `cnt_lag_7 = shift(7)`, `cnt_roll_7 = shift(1).rolling(7)`, `cnt_roll_3 = shift(1).rolling(3)` (`src/features.py:74-79`). `LAG_WARMUP=7` (`src/config.py:55`) is used consistently. The new predictor `cnt_roll_3` only uses d−3..d−1, so it is available at prediction time.

3. **Calendar alignment is sound.**
   `reindex_to_calendar` builds a complete daily index before any shift/rolling (`src/features.py:44-50`). The inserted 2011-03-10 row carries NaN, which propagates through the shift/rolling windows and is removed by `dropna` (`src/features.py:81`), so the gap cannot silently create a mislabelled lag. The resulting row count reconciles: 729 calendar days − first 7 warm-up − the gap row − 7 post-gap rows contaminated by that NaN = **714**, matching the operator's count.

4. **Split and fitting are temporally clean.**
   Train ≤ 2011-12-31, valid = H1 2012, test = H2 2012 (`src/train.py:56-62`; `src/config.py:49-50`). `StandardScaler` is inside the ridge pipeline (`src/train.py:51`) and is fit only on `train[cols]` in `model.fit` (`src/train.py:78`). No scaler, imputer, or other statistic is fit on validation/test. `dropna` (`src/features.py:81`) removes rows but fits nothing.

5. **Both baselines accompany the models on identical rows.**
   `baseline_mean` and `baseline_persistence` are in `MODELS` (`src/train.py:48-52`) and are evaluated over the same `valid`/`test` frames as ridge and HGB (`src/train.py:77-85`). Persistence uses `cnt_lag_1`, which is present in the audited feature list.

6. **Seeds are fixed.**
   `HistGradientBoostingRegressor(random_state=0)` (`src/train.py:52`); ridge and both baselines are deterministic. With ~350 training rows, HGB's default `early_stopping="auto"` does not engage (threshold is 10,000 samples), so there is no unseeded validation-based stopping.

A validation R² drop from 0.6475→0.6439 (ridge) and 0.2185→0.1983 (HGB) is consistent with adding collinear lag/rolling features; a leakage defect would instead push scores toward 1.0. The scores staying at 0.64/0.20 corroborate that today's count is not in the rolling windows.

## Execution checks — operator-attributed, not mine

I could not execute anything in this session: tool access was denied, so `make test`, `make train`, and any dataframe inspection were **not run by me**. The following are the operator's results and I did not independently reproduce them:
- 15 passing tests (note: only 8 test functions appear in the provided `tests/test_leakage.py`; the other 7 are in files not included in the excerpts);
- verification of the rolling features against all 714 calendar-aligned rows;
- the ridge/HGB validation R² figures above.

The in-repo coverage alone is weaker than that claim: `test_rolling_mean_excludes_today` samples a single row (`tests/test_leakage.py:50-57`) and `test_lags_are_true_calendar_lags` checks only `cnt_lag_1` (`:34-43`), so the exhaustive 714-row verification rests entirely on the operator's run.

## Non-blocking notes (no reported number changes)

- **Same-day weather availability:** `temp`/`atemp`/`hum`/`windspeed` (not shown in the excerpt but present in the mirror) and `weather_severity` (`src/features.py:68-69`) are same-day observations treated as known at time t. This is an explicit modeling assumption, not target leakage, but it would inflate skill under a true day-ahead forecast protocol. It does not affect the ridge-vs-HGB comparison or the leakage verdict.
- **Dtype-driven feature gate:** `feature_columns` (`src/features.py:86-87`) admits any future numeric column not listed in `FORBIDDEN`. The current schema is clean, but a new numeric target restatement added to the mirror would silently enter the model. Also, `src/ingest.py`, the raw CSV headers, `tests/test_contract.py`, the `Makefile`, and `requirements.txt` were not in the excerpts, so full column enumeration and command/version reproduction could not be confirmed.
````

## Member B verdict

I found no leakage in the three-day mean and no error that changes the
reported validation scores. I agree with the auditor about calendar
alignment and training-only fitting. The direct check against all 714
dates supports the leakage verdict. A drop in validation R² by itself
cannot rule out leakage. I recommend excluding the feature from the
final model inputs because ridge and HGB both lost validation R², while
keeping the feature and its test as the record of the experiment. The
same-day weather caveat limits how far the results generalize to a
day-ahead deployment. Verification's explicit CSV schema test addresses
the separate risk that a newly added numeric column enters the model.

## Member A review of Member B's verification branch

| Field | Value |
|---|---|
| Teammate repository | https://github.com/Miny-oung-K/dsc180-MA6, branch `verification` (commit `04e5cb1`, author brianzliu) |
| Auditor | `leakage-auditor` subagent (`.claude/agents/leakage-auditor.md` on that branch) |
| Model used for this run | Claude Opus 5.5, not the local `bikeshare-coder` (Ollama was not available to the run) |
| Date | 2026-11-20 |

### Auditor output (verbatim)

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

### Which findings I agree with

- **Finding 1 (REPORT.md picks the model on test): agree.** I reran `make train` myself and got the same validation numbers: ridge R² 0.6475 / MAE 832.9, persistence 0.4507 / 900.6. Choosing persistence because of its test MAE (840.1 vs 947.1) means the test set decided the model, which CLAUDE.md rules out. This changes the Exercise 5 conclusion, not any metric.
- **Hook skips edits under `tests/`: agree it is real, but it changes no number.** I am noting it and not counting it as a finding.

### Verdict

The `verification` branch is clean on everything that produces a number. No forbidden or target-derived column reaches the model. The split is by date, and every fit uses training rows only. The lags and the 7-day rolling mean line up with real calendar dates on all 714 rows. Both baselines are scored on the same rows as the models. `make all` reproduces `reports/metrics.json` byte-for-byte, and all 16 tests pass. The new contract tests, config sets and hook add guards without loosening any. The one problem is in the write-up: REPORT.md's Exercise 5 recommends persistence based on test-set MAE, while validation ranks ridge ahead on both R² and MAE. The model choice should be made and argued on validation, with test reported once as the held-out estimate. If Exercise 5 explicitly asks for the test-set comparison, the paragraph should still say that validation gives the opposite ranking.
