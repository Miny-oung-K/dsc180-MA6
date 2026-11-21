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
