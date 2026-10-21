"""Fixed binary rubric and independent, deterministic checks."""

import re

VERSION = "1.1"
SECTIONS = ["Start here", "What it is", "Why it matters", "How it works",
            "A worked example", "What can go wrong", "Check yourself", "Recap"]

# These are requirements, not model-generated scores.
RUBRIC = {
    "accuracy": "Every technical claim agrees with the source notes. Do not turn a possibility into certainty: neither 'RAG always gives correct answers' nor 'wrong source notes always make the answer wrong' is supported. No claim that RAG always searches the internet or necessarily retrains the model. Avoid unsupported claims about a computer's understanding. Clearly labelled fictional examples and everyday analogies are allowed and need no research citation.",
    "coverage": "Explain what the topic is, why someone would use it, and its complete basic process. For RAG: expand RAG; explain finding relevant document pieces, adding those pieces to the question, then generating an answer. Distinguish looking up information from retraining.",
    "language": "Use everyday English for a learner who has finished class 12 in India and has limited English. No advanced vocabulary where a familiar word works; simple, respectful sentences without assuming coding knowledge.",
    "jargon": "Explain each technical term at its FIRST use, including AI, language model/LLM, retrieval, context, embedding, parameters, query, database and vector database IF used. In particular, 'learned parameters' without an explanation FAILS, as does 'query' without explaining it means a question. The full RAG expansion can be followed immediately by plain-language definitions, including augmented. Omit unnecessary jargon.",
    "example": "Include one explicitly fictional, familiar Indian learning example: a question, exact short source note, what is retrieved, and an answer supported by that note. Also show how guessing without the note can go wrong. No unexplained jump between steps.",
    "limitations": "Explain that missing, wrong or outdated source material can lead to wrong answers; RAG can still make mistakes. Show an explicit 'I do not know' or equivalent response when the supplied notes do not contain the answer.",
    "flow": "Motivation comes before the detailed process. Define concepts before relying on them; each step connects to the next. The recap matches what was taught, without introducing new concepts.",
    "practice": "Include exactly 3 numbered learner questions plus a separate answer key. One tests meaning, one applies the process to a NEW question, and one tests missing evidence. Answers must be correct and supported by the lesson.",
}

ADVICE = {
    "accuracy": "Compare every claim with the source notes. Looking up notes is not retraining, and RAG does not guarantee correct answers.",
    "coverage": "Cover meaning, need and all basic steps. Explain lookup versus retraining.",
    "language": "Replace difficult words with familiar words. Keep one main idea per sentence.",
    "jargon": "Explain technical words immediately on first use, or remove them.",
    "example": "Walk through one fictional college-notice question, its exact source, retrieved text and supported answer.",
    "limitations": "Show both a supported answer and an honest 'I do not know' when notes are missing.",
    "flow": "Start with a learner's problem, define the idea, explain steps, then practise.",
    "practice": "Write three questions: meaning, a new application and missing evidence. Add a correct answer key.",
    "length": "Keep the lesson between 500 and 900 words, aiming for 650.",
    "structure": "Use all eight required headings in their given order.",
    "sentence_length": "Split long sentences. Keep average sentence length at most 18 words and each at most 35.",
    "citations": "Use only source IDs present in the source pack, and cite at least one source inline as [S1].",
}


def check(check_id, passed, reason, evidence="", source_ids=None):
    return {"id": check_id, "passed": passed, "reason": reason,
            "evidence": evidence, "source_ids": source_ids or []}


def deterministic_checks(lesson, source_ids):
    # Ignore headings and the references list for the prose sentence metric.
    body = lesson.split("\n## Sources")[0]
    words = re.findall(r"\b[\w'-]+\b", body)
    headings = re.findall(r"^## (.+?)\s*$", body, flags=re.M)
    paragraphs = "\n".join(line for line in body.splitlines()
                          if line.strip() and not line.startswith("#"))
    sentences = [re.findall(r"\b[\w'-]+\b", s)
                 for s in re.split(r"[.!?]+(?:\s|$)|\n", paragraphs)]
    lengths = [len(s) for s in sentences if s]
    average = sum(lengths) / len(lengths) if lengths else 0
    longest = max(lengths, default=0)
    brackets = re.findall(r"\[([^\]\n]+)\]", body)
    cited = {sid for group in brackets for sid in re.findall(r"\bS\d+\b", group)}
    return [
        check("length", 500 <= len(words) <= 900, f"{len(words)} words; required 500–900."),
        check("structure", headings == SECTIONS, "Required headings must appear once, in order."),
        check("sentence_length", bool(lengths) and average <= 18 and longest <= 35,
              f"Average {average:.1f} words, longest {longest}; limits 18 and 35."),
        check("citations", bool(cited) and cited <= set(source_ids),
              "At least one inline source ID; all IDs must exist in the source pack."),
    ]


def validate_judgment(value, lesson, source_ids):
    """Validate verdicts; resolve evidence from original lines, never model quotations."""
    if not isinstance(value, dict) or not isinstance(value.get("checks"), list):
        raise ValueError("Evaluator response needs a checks array.")
    checks = value["checks"]
    if len(checks) != len(RUBRIC):
        raise ValueError("Evaluator must return every rubric check exactly once.")
    ids = [c.get("id") for c in checks if isinstance(c, dict)]
    if len(ids) != len(checks) or set(ids) != set(RUBRIC):
        raise ValueError("Evaluator check IDs are missing, duplicated or unknown.")
    lines = lesson.splitlines()
    for c in checks:
        if type(c.get("passed")) is not bool:
            raise ValueError("Evaluator pass/fail must be a JSON boolean.")
        if not isinstance(c.get("reason"), str) or not c["reason"].strip():
            raise ValueError("Each evaluator check needs a reason.")
        indices = c.get("evidence_lines")
        if (not isinstance(indices, list) or
                any(type(i) is not int or not 1 <= i <= len(lines) or
                    not lines[i - 1].strip() for i in indices)):
            raise ValueError("Evaluator evidence must reference valid, nonempty lesson lines.")
        if c["passed"] and not indices:
            raise ValueError("A passing check needs evidence from the lesson.")
        c["evidence"] = [lines[i - 1] for i in indices]
        refs = c.get("source_ids")
        if not isinstance(refs, list) or any(not isinstance(s, str) or s not in source_ids for s in refs):
            raise ValueError("Evaluator cited an unknown source ID.")
        if c["id"] == "accuracy" and c["passed"] and not refs:
            raise ValueError("An accuracy pass needs source support.")
    return checks


LESSON_SCHEMA = {
    "type": "object", "properties": {
        "lesson": {"type": "string"},
        "changes": {"type": "array", "items": {"type": "string"}},
    }, "required": ["lesson", "changes"], "additionalProperties": False,
}
JUDGE_SCHEMA = {
    "type": "object", "properties": {"checks": {
        "type": "array", "items": {
            "type": "object", "properties": {
                "id": {"type": "string", "enum": list(RUBRIC)},
                "passed": {"type": "boolean"},
                "reason": {"type": "string"},
                "evidence_lines": {"type": "array", "items": {"type": "integer"}},
                "source_ids": {"type": "array", "items": {"type": "string"}},
            }, "required": ["id", "passed", "reason", "evidence_lines", "source_ids"],
            "additionalProperties": False,
        },
    }}, "required": ["checks"], "additionalProperties": False,
}
