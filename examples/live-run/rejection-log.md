# Rejection log

Status: **passed**

Every check must pass. Drafts are kept for inspection.

## Attempt 1

A deliberately false statement was inserted for the demo:
> RAG always gives correct answers, even when its source notes are wrong.

- **accuracy**: Line 64 directly claims that RAG always gives correct answers even when its source notes are wrong, contradicting the sources and the rubric constraint.
- **flow**: Line 64 in the recap introduces a false claim that contradicts what was previously taught, and the recap appears after the practice section instead of before it.

Generator-reported changes (see the saved diff to verify):
- Wrote a beginner-friendly lesson following all 8 required headings exactly.
- Targeted class 12 Indian learner using simple vocabulary and an open-book exam analogy.
- Defined AI, language model, retrieval, augmented, and generation at first use without forbidden jargon.
- Distinguished retrieving notes at answer time from retraining/changing what the model learned.
- Included a clearly labelled fictional college example with exact notice and 'I do not know' behaviour.
- Kept word counts close to targets (total ~570 words) and sentence lengths under constraints.
- Added 3 practice questions with a matching answer key and correct factual citations.

## Attempt 2

All checks passed.

Generator-reported changes (see the saved diff to verify):
- Removed the false claim at the end of the previous lesson that stated RAG always gives correct answers even when notes are wrong.
- Ensured all 8 required headings match the exact required heading list, keeping 'Recap' as the eighth section as specified in the rubric.
- Clarified in 'Why it matters' and 'Recap' that looking up notes at answer time does not change what the model learned during training.
- Maintained short sentence lengths and everyday language accessible for a class 12 graduate with limited English.

Actual changes: `attempt-2-changes.diff`
