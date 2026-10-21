# Actual Vertex run

This folder contains a real run of `gemini-3.8-flash` through Vertex ADC, using the US multi-region endpoint and rubric 1.1. No model judgments or drafts in this folder were hand-written.

- Run ID: `20261021T140721Z-eec8e0a7`
- Mode: deliberate-error demo; first draft was corrupted before review.
- First draft: rejected for accuracy and flow.
- Second draft: all 12 checks passed; 666 words before the source list.
- Final status: `passed`.

Open `rejection-log.md` to follow the decision, `report.json` for the complete checks and extracted evidence, and `attempt-2-changes.diff` for the real revision. The passing lesson is `lesson.md`, also copied to `docs/final-lesson.md`.

The first raw draft is intentionally wrong. It is saved as evidence, not offered as a lesson to study. Fault-injection runs are excluded from persistent failure memory.
