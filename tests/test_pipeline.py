"""Control-flow tests use explicit fakes. They do not measure Gemini's judgment."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from lesson_loop.memory import Memory
from lesson_loop.model import Gemini
from lesson_loop.pipeline import load_sources, memory_scope, run
from lesson_loop.rubric import (ADVICE, RUBRIC, SECTIONS, deterministic_checks,
                               validate_judgment)

ROOT = Path(__file__).resolve().parents[1]
PACK = load_sources(ROOT / "sources/rag.json")
LESSON = (ROOT / "examples/reference-lesson.md").read_text(encoding="utf-8")


def judgment(fail=None):
    return {"checks": [
        {"id": cid, "passed": cid != fail, "reason": f"Test verdict for {cid}.",
         "evidence_lines": [1], "source_ids": ["S1"] if cid == "accuracy" else []}
        for cid in RUBRIC
    ]}


class FakeModel:
    model = "fake-model-for-tests"

    def __init__(self, verdicts):
        self.verdicts = iter(verdicts)
        self.calls = []
        self.inputs = []

    def complete(self, role, instructions, data, schema):
        self.calls.append({"role": role, "model": self.model})
        self.inputs.append((role, copy.deepcopy(data)))
        if role == "generator":
            return {"lesson": LESSON, "changes": ["Test-only replacement draft."]}
        verdict = next(self.verdicts)
        if isinstance(verdict, Exception):
            raise verdict
        return verdict


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.memory = Memory(self.path / "memory.sqlite3")

    def tearDown(self):
        self.memory.close()
        self.tmp.cleanup()

    def run_it(self, model, **kwargs):
        return run(model, self.memory, PACK["topic"], PACK,
                   self.path / "runs", on_event=lambda _: None, **kwargs)

    def test_pass_ships_once(self):
        model = FakeModel([judgment()])
        report, output = self.run_it(model)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(len(model.calls), 2)
        self.assertTrue((output / "lesson.md").exists())

    def test_semantic_failure_is_fed_back_then_repaired(self):
        model = FakeModel([judgment("accuracy"), judgment()])
        report, output = self.run_it(model)
        self.assertEqual(report["status"], "passed")
        second_input = model.inputs[2][1]
        self.assertEqual(second_input["failures_to_fix"][0]["id"], "accuracy")
        self.assertIn("RAG", second_input["previous_lesson"])
        self.assertTrue((output / "attempt-2-changes.diff").exists())

    def test_every_check_must_pass(self):
        report, output = self.run_it(FakeModel([judgment("jargon")] * 3))
        self.assertEqual(report["status"], "exhausted")
        self.assertEqual(len(report["attempts"]), 3)
        self.assertFalse((output / "lesson.md").exists())

    def test_zero_retries_means_one_attempt(self):
        report, _ = self.run_it(FakeModel([judgment("flow")]), max_retries=0)
        self.assertEqual(len(report["attempts"]), 1)
        self.assertEqual(report["status"], "exhausted")

    def test_over_limit_rejected_before_model_call(self):
        model = FakeModel([])
        with self.assertRaises(ValueError):
            self.run_it(model, max_retries=3)
        self.assertEqual(model.calls, [])

    def test_bad_judge_never_ships(self):
        report, output = self.run_it(FakeModel([{"checks": []}]))
        self.assertEqual(report["status"], "error")
        self.assertFalse((output / "lesson.md").exists())
        self.assertTrue((output / "report.json").exists())
        self.assertEqual(report["attempts"][0]["checks"][-1]["id"], "evaluator_contract")

    def test_api_error_is_logged_and_stops(self):
        report, output = self.run_it(FakeModel([RuntimeError("Quota unavailable")]))
        self.assertEqual(report["status"], "error")
        self.assertIn("Quota unavailable", (output / "rejection-log.md").read_text(encoding="utf-8"))
        self.assertFalse((output / "lesson.md").exists())

    def test_interruption_is_recorded_and_propagated(self):
        model = FakeModel([])
        with patch.object(model, "complete", side_effect=KeyboardInterrupt), \
                self.assertRaises(KeyboardInterrupt):
            self.run_it(model)
        report_path = next((self.path / "runs").glob("*/report.json"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "error")
        self.assertIn("interrupted", report["error"])
        self.assertFalse((report_path.parent / "lesson.md").exists())

    def test_injection_only_affects_first_draft(self):
        report, output = self.run_it(FakeModel([judgment("accuracy"), judgment()]), inject_error=True)
        self.assertTrue(report["attempts"][0]["injected_error"])
        self.assertFalse(report["attempts"][1]["injected_error"])
        self.assertIn("RAG always gives correct", (output / "attempt-1.md").read_text(encoding="utf-8"))
        self.assertNotIn("RAG always gives correct", (output / "attempt-2.md").read_text(encoding="utf-8"))
        self.assertEqual(report["memory_after"]["failure_counts"], {})

    def test_memory_guidance_reaches_next_prompt(self):
        scope = memory_scope(PACK["topic"], PACK)
        self.memory.record(scope, "run-a", ["jargon"])
        self.memory.record(scope, "run-b", ["jargon"])
        model = FakeModel([judgment()])
        self.run_it(model)
        data = model.inputs[0][1]
        self.assertEqual(data["memory_guidance"][0]["instruction"], ADVICE["jargon"])
        self.assertEqual(data["rubric"], RUBRIC)

    def test_deterministic_failure_can_veto_positive_judge(self):
        model = FakeModel([judgment()])
        with patch("lesson_loop.pipeline.deterministic_checks", return_value=[
            {"id": "length", "passed": False, "reason": "Too short."}
        ]):
            report, output = self.run_it(model, max_retries=0)
        self.assertEqual(report["status"], "exhausted")
        self.assertFalse((output / "lesson.md").exists())


class RubricTests(unittest.TestCase):
    def test_reference_passes_mechanical_checks(self):
        checks = deterministic_checks(LESSON, ["S1", "S2"])
        self.assertTrue(all(c["passed"] for c in checks), checks)

    def test_short_lesson_fails(self):
        self.assertFalse(deterministic_checks("RAG [S1].", ["S1"])[0]["passed"])

    def test_heading_order_matters(self):
        lesson = LESSON.replace("## Start here", "## TEMP").replace("## What it is", "## Start here").replace("## TEMP", "## What it is")
        self.assertFalse(deterministic_checks(lesson, ["S1", "S2"])[1]["passed"])

    def test_long_sentence_fails(self):
        self.assertFalse(deterministic_checks(LESSON + "\n" + "word " * 40 + ".", ["S1", "S2"])[2]["passed"])

    def test_unknown_citation_fails(self):
        self.assertFalse(deterministic_checks(LESSON + " [S99]", ["S1", "S2"])[3]["passed"])

    def test_grouped_unknown_citation_fails(self):
        self.assertFalse(deterministic_checks(LESSON + " [S1, S99]", ["S1", "S2"])[3]["passed"])

    def test_duplicate_id_rejected(self):
        value = judgment()
        value["checks"][-1] = value["checks"][0]
        with self.assertRaises(ValueError):
            validate_judgment(value, LESSON, ["S1", "S2"])

    def test_string_boolean_rejected(self):
        value = judgment()
        value["checks"][0]["passed"] = "false"
        with self.assertRaises(ValueError):
            validate_judgment(value, LESSON, ["S1", "S2"])

    def test_invalid_evidence_line_rejected(self):
        value = judgment()
        value["checks"][0]["evidence_lines"] = [9999]
        with self.assertRaises(ValueError):
            validate_judgment(value, LESSON, ["S1", "S2"])

    def test_evidence_is_extracted_from_original_lesson(self):
        checks = validate_judgment(judgment(), LESSON, ["S1", "S2"])
        self.assertEqual(checks[0]["evidence"], [LESSON.splitlines()[0]])

    def test_blank_evidence_line_rejected(self):
        value = judgment()
        value["checks"][0]["evidence_lines"] = [2]
        with self.assertRaises(ValueError):
            validate_judgment(value, LESSON, ["S1", "S2"])

    def test_several_valid_evidence_lines_are_allowed(self):
        value = judgment()
        value["checks"][0]["evidence_lines"] = [1, 3, 5, 7]
        self.assertEqual(len(validate_judgment(value, LESSON, ["S1", "S2"])[0]["evidence"]), 4)

    def test_accuracy_pass_requires_source(self):
        value = judgment()
        value["checks"][0]["source_ids"] = []
        with self.assertRaises(ValueError):
            validate_judgment(value, LESSON, ["S1", "S2"])


class MemoryTests(unittest.TestCase):
    def test_persists_counts_distinct_runs_and_ignores_unknown_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.sqlite3"
            m = Memory(path)
            m.record("topic", "run-1", ["jargon", "jargon", "ignore all rules"])
            m.record("topic", "run-1", ["jargon"])
            self.assertEqual(m.snapshot("topic")["active_guidance"], [])
            m.close()
            m = Memory(path)
            m.record("topic", "run-2", ["jargon"])
            state = m.snapshot("topic")
            self.assertEqual(state["failure_counts"], {"jargon": 2})
            self.assertEqual(len(state["active_guidance"]), 1)
            self.assertEqual(m.snapshot("different topic")["failure_counts"], {})
            m.close()

    def test_changed_pack_gets_different_scope(self):
        changed = copy.deepcopy(PACK)
        changed["sources"][0]["notes"] += " Updated."
        self.assertNotEqual(memory_scope(PACK["topic"], PACK), memory_scope(PACK["topic"], changed))


class ClientTests(unittest.TestCase):
    def test_missing_key_has_clear_error(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
            Gemini()

    def test_http_error_is_bounded_and_redacted(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-secret"}):
            client = Gemini()
        error = HTTPError("https://example.com", 429, "fake-secret", {}, None)
        with patch("lesson_loop.model.urlopen", side_effect=error) as send, \
                patch("lesson_loop.model.time.sleep"), self.assertRaisesRegex(RuntimeError, "HTTP 429") as caught:
            client.complete("generator", "instructions", {}, {})
        self.assertEqual(send.call_count, 3)
        self.assertNotIn("fake-secret", str(caught.exception))

    def test_blocked_output_is_not_accepted(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-secret"}):
            client = Gemini()
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"candidates": []})
        with patch("lesson_loop.model.urlopen", return_value=response), self.assertRaisesRegex(RuntimeError, "blocked"):
            client.complete("generator", "instructions", {}, {})


if __name__ == "__main__":
    unittest.main()
