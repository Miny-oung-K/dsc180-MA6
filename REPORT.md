## Results

Validation scores from the pinned environment, before and after adding
`cnt_roll_3`. The test scores will be added after the team merges and runs
the final evaluation.

| Feature set | Model | Validation R² | Validation MAE |
| --- | --- | ---: | ---: |
| Before | Mean baseline | -0.9318 | 2002.2 |
| Before | Persistence | 0.4507 | 900.6 |
| Before | Ridge | 0.6475 | 832.9 |
| Before | HGB | 0.2185 | 1296.6 |
| With `cnt_roll_3` | Mean baseline | -0.9318 | 2002.2 |
| With `cnt_roll_3` | Persistence | 0.4507 | 900.6 |
| With `cnt_roll_3` | Ridge | 0.6439 | 836.5 |
| With `cnt_roll_3` | HGB | 0.1983 | 1311.6 |

## Headline finding

The three-day rolling mean reduced validation R² by 0.0036 for ridge and
0.0202 for HGB. Ridge also missed by 3.6 more rides per day on average.
The baseline validation scores were identical in both runs. We kept the
feature and its test as an experiment and selected the original feature
set for the final model inputs.

## Exercise 4: target transformation

In a validation-only experiment with the baseline feature set, I fit HGB
to `cnt / cnt_roll_7` on the 2011 training rows. I multiplied each
predicted ratio by that day's `cnt_roll_7` to recover a forecast in rides.
The resulting validation R² was 0.7454 and MAE was 687.2, compared with
0.2185 and 1296.6 for ordinary HGB and 0.6475 and 832.9 for ridge.
The scaling is defensible because the seven-day mean is positive in the
training and validation data and uses only preceding days. It gives HGB a
way to forecast against a recent demand level as ridership changes. The
comparison does not establish performance on the held-out test period.

## Exercise 5: ridge vs persistence

I would deploy persistence if the goal is to minimize the average number of rides by which the daily forecast is off. On the starter's H2 2012 test set, ridge raised R² from 0.5099 to 0.5833, an increase of 0.0734, but its MAE was 947.1 rides versus 840.1 for persistence. That is 107.0 more rides of absolute error per day on average. The higher R² means ridge reduced squared error, which gives large misses more weight. If those misses are especially costly, that gain is worth investigating. For a daily forecast judged by absolute error, yesterday's count is the better choice on these results.

The numbers above come from the assignment's starter results. Update this comparison against the final `reports/metrics.json` after the team's feature and validation work is complete.

## Attribution

Member B used DeepSeek V4.1 Flash 1017 through OpenRouter in Claude Code
at max effort for the fault experiments and branch audit. The attempted
Ollama setup ended before any model run. Codex assisted with implementation,
verification, and drafting.

- Agent-assisted files include `tests/test_contract.py`, the schema
  classifications in `src/config.py`, the Claude Code hook and
  `/seed-fault` skill, `docs/SEEDED_FAULTS.md`, and this report draft.
- Member B ran the verification workflow on the shared task definition,
  retaining the starter's date split and two baselines. The explicit raw
  header classification and response to unexpected weather labels are
  recorded in `docs/DECISIONS.md`.
