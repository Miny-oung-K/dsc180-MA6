## Results

Scores from `make all` on the merged code, copied from `reports/metrics.json`.
"Before" is the selected feature set (the top-level entries), and "With `cnt_roll_3`" is the
`with_cnt_roll_3` entry. The feature decision was made on validation only. Test scores were
computed once, after the merge, for this final table.

| Feature set | Model | Validation R² | Validation MAE | Test R² | Test MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| Before | Mean baseline | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | Ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | HGB | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| With `cnt_roll_3` | Mean baseline | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| With `cnt_roll_3` | Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| With `cnt_roll_3` | Ridge | 0.6439 | 836.5 | 0.5800 | 946.2 |
| With `cnt_roll_3` | HGB | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

## Headline finding

Lagged demand carries this forecast, and the growth in ridership decides
which model can use it. Mean daily rides rose 63% from 2011 to 2012, and
56.5% of test days (104 of 184) exceed the 2011 maximum of 6,043. On H1
2012 validation, ridge reaches R² 0.6475 (MAE 832.9) against 0.4507
(900.6) for persistence and -0.9318 for the 2011 mean, while gradient
boosting manages only 0.2185. On the H2 2012 test set, boosting falls to
R² -0.4975 (MAE 1972.6), because trees trained on 2011 cannot predict
above the 2011 range. Ridge holds R² 0.5833 on test, but its MAE of 947.1
is worse than persistence's 840.1, so its advantage is in large misses
rather than typical days. Our added feature, the three-day mean
`cnt_roll_3`, lowered validation R² for both ridge (-0.0036) and boosting
(-0.0202), so it is excluded from the final model inputs.

## Exercise 4: target transformation

In a validation-only experiment with the baseline feature set, I fit HGB
to `cnt / cnt_roll_7` on the 2011 training rows. I multiplied each
predicted ratio by that day's `cnt_roll_7` to recover a forecast in rides.
The resulting validation R² was 0.7454 and MAE was 687.2, compared with
0.2185 and 1296.6 for ordinary HGB and 0.6475 and 832.9 for ridge.
The scaling is defensible because the seven-day mean is positive in the
training and validation data and uses only preceding days. It gives HGB a
way to forecast against a recent demand level as ridership changes. It is
not just a way to win the comparison: the ratio target was fixed before
looking at test, it adds no information the other models lack (ridge
already sees `cnt_roll_7`), and it removes the reason HGB failed, namely
that trees cannot predict outside the 2011 range of counts.

I touched the test set once, after the validation work, by running
`python -m src.train --ratio-target --final`. On H2 2012 test, the
transformed HGB scored R² 0.6416 and MAE 810.1, against -0.4975 and
1972.6 for ordinary HGB, 0.5833 and 947.1 for ridge, and 0.5099 and
840.1 for persistence. The gain holds on held-out data. The committed
`reports/metrics.json` still comes from the untransformed pipeline; the
code is behind the `--ratio-target` flag in `src/train.py`, and it never
writes the metrics file.

## Exercise 5: ridge vs persistence

I would deploy ridge, because validation is the split this choice is made on, and on validation ridge beats persistence on both measures. On H1 2012 validation, ridge has R² 0.6475 against 0.4507 for persistence, and MAE 832.9 rides against 900.6, so it is off by 67.7 fewer rides per day on average. The H2 2012 test set, scored once after that choice, is the held-out estimate, and it is less favourable: ridge R² 0.5833 against 0.5099, but MAE 947.1 against 840.1, which is 107.0 more rides of absolute error per day. Ridge still wins on squared error, which weights large misses more heavily, but it loses its MAE advantage when ridership moves further from the 2011 training range. I report that reversal rather than switching to persistence, because choosing the model on its test score would mean tuning on test. If absolute error is the measure that matters most in deployment, the test result is a reason to revisit the choice with new validation data.

The numbers above match the selected feature set in the final `reports/metrics.json`.

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

Member A used Claude Opus 5.5 (hosted, through the Claude app's agent
workspace) instead of the local Ollama model, with the instructor's
permission. The same model ran the `leakage-auditor` subagent for
Member A's audit.

- Agent-generated by Member A's agent: the `cnt_roll_3` test and feature,
  the Exercise 1 section of `docs/SEEDED_FAULTS.md`, the Member A audit
  and draft verdict in `docs/AUDIT.md`, the Exercise 5 rewrite, the branch
  merge and conflict resolution, the test columns in Results, the
  `--ratio-target` flag and its test check, and this Headline paragraph.
- Member A's decisions: which feature to add, agreeing with the audit
  finding that Exercise 5 chose its model on test, choosing the model on
  validation, and merging both branches into `main`. Each is recorded in
  `docs/DECISIONS.md`.
