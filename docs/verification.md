# Verification

Verified on 21 October 2026 with Python 3.12 on Windows.

## Offline checks

`python -m unittest discover -s tests -v` passes all 28 tests. Tests use explicit fake responses to verify control flow, retry bounds, failure handling, citation validation, evidence references and persistent memory. These are software tests, not a measure of model accuracy.

With `requirements-ui.txt` installed, four additional Streamlit AppTest cases check the saved-example view without model calls, missing-project validation, pipeline invocation with the selected retry/demo settings, failed-run presentation, and authentication-error handling. Opening or reviewing the dashboard does not itself start generation.

## Live end-to-end run

The saved `examples/live-run` uses real `gemini-3.8-flash` calls through Vertex ADC in the US multi-region. The initial candidate included the demo's false claim. The evaluator rejected accuracy and flow. The revised candidate passed all 12 checks.

The release contains the actual input, drafts, model judgments, text diff, source/rubric snapshots and report. No successful verdict was substituted for a failed call. The final lesson contains 666 words before its source list.

## Live evaluator calibration

The seven cases in `examples/calibration/summary.json` met their expected outcomes under rubric 1.1:

- Reference lesson: all semantic checks passed.
- False guarantee: accuracy failed.
- Unexplained dense-retrieval terms: jargon failed.
- Missing practice: practice failed.
- Prompt injection plus a false retraining claim: accuracy failed.
- False certainty about wrong sources: accuracy failed.
- Unexplained query/parameters wording: jargon failed.

Some cases also failed additional checks; those actual verdicts remain in the artifacts. This small, constructed set tests known behaviours. It does not establish a production accuracy rate or real learner comprehension.
