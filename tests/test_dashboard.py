"""Check UI behaviour without spending model tokens or needing credentials."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

if importlib.util.find_spec("streamlit"):
    from streamlit.testing.v1 import AppTest
else:
    AppTest = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(AppTest is None, "Install requirements-ui.txt to run dashboard tests.")
class DashboardTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=15)

    def test_initial_view_uses_saved_evidence_without_a_model_call(self):
        with patch("lesson_loop.model.Gemini") as model:
            app = self.app().run()
        self.assertEqual(list(app.exception), [])
        model.assert_not_called()
        self.assertEqual(app.metric[0].value, "Passed")
        self.assertEqual(app.metric[2].value, "12/12")
        self.assertTrue(any("saved, real Vertex run" in message.value for message in app.info))

    def test_missing_project_does_not_start_generation(self):
        with patch("lesson_loop.model.Gemini") as model:
            app = self.app().run()
            app.text_input(key="project").set_value("")
            app.button[0].click().run()
        self.assertEqual(list(app.exception), [])
        model.assert_not_called()
        self.assertTrue(any("Enter your Google Cloud project" in message.value for message in app.error))

    def test_new_run_uses_same_pipeline_and_does_not_rerun_on_review(self):
        (ROOT / "runs").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
            result = {"run_id": "ui-test", "status": "exhausted", "model": "test",
                      "attempts": [], "seconds": 1, "demo_injection": True}
            folder = Path(tmp)
            (folder / "report.json").write_text(json.dumps(result), encoding="utf-8")
            with patch("lesson_loop.model.Gemini") as model, \
                    patch("lesson_loop.memory.Memory") as memory, \
                    patch("lesson_loop.pipeline.run", return_value=(result, folder)) as pipeline:
                app = self.app().run()
                app.text_input(key="project").set_value("test-project")
                app.checkbox(key="inject_error").check()
                app.selectbox(key="retries").select(1)
                app.button[0].click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.metric[0].value, "Exhausted")
                self.assertTrue(any("No final lesson was released" in message.value for message in app.warning))
                pipeline.assert_called_once()
                self.assertEqual(pipeline.call_args.kwargs["max_retries"], 1)
                self.assertTrue(pipeline.call_args.kwargs["inject_error"])
                model.assert_called_once_with("gemini-3.8-flash", "vertex", "test-project", "us")
                memory.return_value.close.assert_called_once()
                app.run()
                pipeline.assert_called_once()

    def test_connection_error_is_shown_and_no_generation_is_started(self):
        with patch("lesson_loop.model.Gemini", side_effect=ValueError("ADC unavailable")), \
                patch("lesson_loop.pipeline.run") as pipeline:
            app = self.app().run()
            app.text_input(key="project").set_value("test-project")
            app.button[0].click().run()
        self.assertEqual(list(app.exception), [])
        pipeline.assert_not_called()
        self.assertTrue(any("ADC unavailable" in message.value for message in app.error))


if __name__ == "__main__":
    unittest.main()
