# Design notes

## What I wanted to prove

The assessment asks for more than a good explanation of RAG. The system needs to decide whether a lesson deserves to be released. My first design decision was therefore to define the gate before trusting the writer.

The learner is a class-12 graduate with limited English. That affects both content and evaluation: a correct explanation can still fail if it starts with words like “dense embeddings” without explaining them. A familiar college notice is a better first example than a production architecture diagram.

## Plan

1. Define the learner and the minimum teaching outcome: explain RAG, follow its basic steps, and recognise missing evidence.
2. Assemble a small, reviewed source pack with stable IDs.
3. Turn quality expectations into binary checks.
4. Build separate writer and reviewer calls, joined by Python control flow.
5. Save failures, feedback and real text differences.
6. Add bounded memory adaptation and test the stop conditions.
7. Run a deliberate-error demonstration and a small live evaluator calibration set.

## Components and their responsibilities

The generator produces Markdown plus a list of changes. It does not decide whether it passed. The evaluator sees the candidate, source notes and fixed rubric in a fresh call. It does not see the writer's self-assessment, earlier verdicts or memory guidance.

The Python controller owns the release decision. It combines four mechanical checks with eight semantic checks and requires all of them to pass. No model-produced overall status can override a failed check. The reviewer references numbered lesson lines; Python validates those references and extracts the original excerpts. This preserves traceable evidence without relying on the model to copy text exactly.

The source pack is a factual boundary, not just a list of links. Both calls receive its notes. The app does not fetch those links during execution. This makes the demo reproducible and avoids treating search snippets as reliable teaching material. A human still needs to maintain the pack.

SQLite stores failure observations. JSON and Markdown files store the audit trail. I kept them separate: the database answers “what has repeatedly gone wrong?”, while a run folder explains what happened in one specific execution.

## Why these checks

Accuracy and completeness protect against teaching the wrong idea. Language and jargon checks protect access for the intended learner. The worked example makes the process visible, while the practice questions test whether the learner can use it. The limitations check makes uncertainty part of the lesson.

The mechanical checks cover things Python can measure directly. They are intentionally separate from the model's judgment. The word and sentence limits are practical editorial choices, not claims about a scientifically validated reading level. The evaluator still reviews actual vocabulary and teaching clarity.

All checks are mandatory because some failures should never be averaged away. A short, friendly lesson that says RAG guarantees truth is still unsuitable.

## Retry policy

The first attempt plus at most two revisions is enough to show useful repair without allowing an endless loop. Every retry receives the entire previous candidate and the failed check objects, including the reasons and evidence. It also receives the unchanged rubric.

The writer's change list is a useful summary, but it is not proof. The controller also saves a unified diff, and every revised lesson goes through the full gate again.

If the final attempt still fails, status becomes `exhausted`. If the API or judge contract fails, status becomes `error`. In both cases the run has no `lesson.md`. This makes “nothing safe to release” a normal outcome the caller can handle.

## What self-evolution means here

Repeated failures activate additional writing guidance. The mapping from failure ID to advice is small and reviewable. An issue must occur in two distinct runs, or equivalent human feedback observations, before it influences a new run.

This is deliberately conservative. An evaluator could be mistaken, so one failed attempt should not permanently rewrite the prompt. The system does not automatically loosen its rubric until everything passes. It adapts its generation instructions within a fixed quality bar.

Memory is scoped by topic, source-pack hash and rubric version. Editing reference material starts a new scope rather than carrying over potentially irrelevant failure patterns. Demo fault injection is excluded from memory.

## Authentication and operational choices

The model is `gemini-3.8-flash`. The client can call Vertex with ADC or the Gemini Developer API with a key. Vertex supports the global and US/EU multi-region endpoints. Access tokens and API keys are used only in HTTP headers and are never saved in reports.

The application sends source notes and drafts to the configured Google model service. The bundled content is public or fictional. A real deployment would need access controls and appropriate handling for private curriculum material.

HTTP retries are separate from content retries: network capacity is not a teaching failure. Each logical call has at most three HTTP attempts. The run report records successful call latency, usage and model version. Failed calls are represented by the run's error; their token use cannot be inferred from a missing response.

## What I would not claim

Separate calls to the same model do not give independent expertise. They can share blind spots. A source ID and a matching quote do not prove factual entailment. The seven-case calibration set is too small to estimate production accuracy.

The workflow's instructions discourage prompt injection; they do not make arbitrary user documents safe by themselves. The local database is meant for a single process. The lesson is in simple English, but I have not established comprehension through learner studies.

Before scaling, I would collect human-labelled good and bad lessons, measure false acceptance and rejection, compare a second evaluator, and test lessons with actual learners. Only then would I add a larger source index or more orchestration infrastructure.
