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

I would deploy ridge, because validation is the split this choice is made on, and on validation ridge beats persistence on both measures. On H1 2012 validation, ridge has R² 0.6475 against 0.4507 for persistence, and MAE 832.9 rides against 900.6, so it is off by 67.7 fewer rides per day on average. The H2 2012 test set, scored once after that choice, is the held-out estimate, and it is less favourable: ridge R² 0.5833 against 0.5099, but MAE 947.1 against 840.1, which is 107.0 more rides of absolute error per day. Ridge still wins on squared error, which weights large misses more heavily, but it loses its MAE advantage when ridership moves further from the 2011 training range. I report that reversal rather than switching to persistence, because choosing the model on its test score would mean tuning on test. If absolute error is the measure that matters most in deployment, the test result is a reason to revisit the choice with new validation data.

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
