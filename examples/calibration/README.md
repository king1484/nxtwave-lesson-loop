# Live evaluator calibration

These are seven real evaluator calls using `gemini-3.8-flash` through Vertex ADC in the US multi-region, under rubric 1.1.

`reference.md` is a prepared reference lesson. The other candidates intentionally contain mistakes or missing content. They are test inputs, not teaching material to study.

`summary.json` records the expected failure and actual failure IDs for each case. Each `*-judge.json` contains the raw model verdict and evidence line references into its corresponding Markdown candidate. All seven expectations were met in this run.

These are constructed cases. They are useful regression probes, not an estimate of general evaluator accuracy or learner success.
