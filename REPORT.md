## Results

Scores from `make all` on the merged code, copied from `reports/metrics.json`.
"Before" is the selected feature set (the top-level entries), and "With `cnt_roll_3`" is the
`with_cnt_roll_3` entry. Validation scores determined whether to keep the
feature. The merged `make all` run generated the final count-target test
scores for this table.

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

Mean daily rides in the raw data rose 63% from 2011 to 2012. On H1 2012
validation, ridge reached R² 0.6475 and MAE 832.9, ahead of persistence
at 0.4507 and 900.6 and the 2011 mean at -0.9318 and 2002.2. On H2 2012
test, 104 of 184 days exceeded the training maximum of 6,043 rides,
while the fitted count-target HGB model's highest forecast was about
5,537. Its test R² of -0.4975 and MAE of 1972.6 still beat the mean
baseline's -2.1441 and 2847.7. Ridge achieved a higher test R² than
persistence (0.5833 vs 0.5099), with higher MAE (947.1 vs 840.1).
The three-day mean `cnt_roll_3` lowered validation R² for ridge by
0.0036 and for HGB by 0.0202, so we kept it for comparison and excluded it
from the selected model inputs.

## Exercise 4: target transformation

In a validation-only experiment with the baseline feature set, we fit HGB
to `cnt / cnt_roll_7` on the 2011 training rows. We multiplied each
predicted ratio by that day's `cnt_roll_7` to recover a forecast in rides.
The resulting validation R² was 0.7454 and MAE was 687.2, compared with
0.2185 and 1296.6 for ordinary HGB and 0.6475 and 832.9 for ridge.
The scaling is defensible because the seven-day mean is positive in the
training and validation data and uses only preceding days. It gives HGB a
way to forecast against a recent demand level as ridership changes.
Ridge already uses `cnt_roll_7`, so the transformation uses information
already available to the other models. Multiplying by the recent demand
level allows the forecasts in rides to scale as demand grows.

After fixing the ratio target based on validation, we evaluated the
transformed model on H2 2012 in a separate final run using
`python -m src.train --ratio-target --final`. On that split, the
transformed HGB scored R² 0.6416 and MAE 810.1, against -0.4975 and
1972.6 for ordinary HGB, 0.5833 and 947.1 for ridge, and 0.5099 and
840.1 for persistence. The gain holds on held-out data. The committed
`reports/metrics.json` still comes from the untransformed pipeline; the
code is behind the `--ratio-target` flag in `src/train.py`, and it never
writes the metrics file.

## Exercise 5: ridge vs persistence

We recommend ridge on the basis of H1 2012 validation. Ridge achieved R²
0.6475 versus 0.4507 for persistence and an MAE of 832.9 rides versus
900.6, a reduction of 67.7 rides per day. An earlier draft recommended
persistence using the starter's test MAE. Minyoung's pre-merge audit
reproduced the test scores and showed that the recommendation had used
the wrong split, so we revised it using validation. On H2 2012, ridge
still reduced squared error (R² 0.5833 vs 0.5099), but it averaged 107.0
more rides of absolute error per day (MAE 947.1 vs 840.1). If deployment
is judged primarily on MAE, we would revisit the choice with new
validation data.

The numbers above match the selected feature set in the final `reports/metrics.json`.

## Attribution

Minyoung used hosted Claude Opus 5.5 in the Claude app's agent workspace
with instructor permission; Anthropic does not publish its parameter
count. Brian used DeepSeek V4.1 Flash 1017 through
OpenRouter in Claude Code at max effort, as a hosted model; we did not
record a parameter count for it. Brian switched the planned
provider from Ollama before running any local model and also used Codex
for implementation, verification, and drafting. The merged repo's
`agent/audit.py` run used DeepSeek V4.1 Flash 1017 via OpenRouter and
reported no leakage or findings, both before and after the final test
and checksum changes.

**Agent-generated or agent-assisted work**

- Minyoung's agent wrote the three-day feature and test, the Exercise 1
  red-test evidence, Minyoung's audit and draft verdict, the ratio-target
  implementation and evaluation, and parts of the report. It also
  assisted with the branch merge and conflict resolution, wrote the raw
  CSV checksum check, the calendar-lag and same-day perturbation tests,
  and the three seeded-fault and fix commits.
- Brian's agents wrote the raw-header and weather contract tests, the
  schema classifications, the hook and `/seed-fault` skill, the fault
  evidence, Brian's audit and draft verdict, the separate feature
  comparison in `src/train.py`, and parts of the report.

**Human decisions**

- Minyoung chose the three-day rolling mean for the feature experiment,
  accepted the audit finding about Exercise 5, and revised the model
  recommendation to use validation. Minyoung merged the two audited
  branches.
- Brian approved keeping the three-day feature and test for comparison
  and excluding the feature from the selected model inputs based on the
  validation decline.
- The team retained the starter's daily ride-count target, leakage
  exclusions, chronological split, and two baselines.

The rationale and outcomes are recorded in [the decision log](docs/DECISIONS.md).
