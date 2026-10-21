"""Local dashboard for the same pipeline used by the command-line app."""

import json
import os
from pathlib import Path
from threading import Lock

import streamlit as st

from lesson_loop.memory import Memory
from lesson_loop.model import Gemini
from lesson_loop.pipeline import load_sources, run

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
DATABASE = ROOT / "data/memory.sqlite3"
EXAMPLE = ROOT / "examples/live-run"


@st.cache_data(ttl=60, show_spinner=False)
def adc_project():
    """Detect local ADC's project without refreshing or exposing credentials."""
    try:
        import google.auth
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return project or getattr(credentials, "quota_project_id", None) or ""
    except Exception:
        # Saved results must remain usable without an ADC login or auth packages.
        return ""


@st.cache_resource
def generation_lock():
    """One local generation at a time, including across browser sessions."""
    return Lock()


def saved_runs():
    folders = [EXAMPLE] + sorted(
        (path.parent for path in RUNS.glob("*/report.json")), reverse=True
    )
    records = {}
    for folder in folders:
        try:
            report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
            if report.get("status") not in ("passed", "exhausted", "error"):
                continue
            if not isinstance(report.get("attempts"), list):
                continue
        except (OSError, ValueError, AttributeError):
            continue
        records[str(folder)] = report
    return records


def show_memory(report):
    st.caption("Memory used by this run, followed by the state after it finished.")
    if report.get("demo_injection"):
        st.info("This was a deliberate-error demo. Demo runs do not update memory.")
    for label, key in (("Before this run", "memory_before"),
                       ("After this run", "memory_after")):
        snapshot = report.get(key, {})
        st.markdown(f"**{label}**")
        counts = snapshot.get("failure_counts", {})
        if counts:
            for check_id, count in counts.items():
                st.write(f"{check_id.replace('_', ' ').title()}: {count} observations")
        else:
            st.caption("No failure observations in this scope.")
        for advice in snapshot.get("active_guidance", []):
            st.success(advice["instruction"])
    st.caption("A check failing in two distinct runs activates writing guidance. The rubric stays fixed.")


def show_result(folder, report):
    attempts = report["attempts"]
    last_checks = attempts[-1].get("checks", []) if attempts else []
    passed = sum(c.get("passed") is True for c in last_checks)
    columns = st.columns(4)
    columns[0].metric("Result", report["status"].title())
    columns[1].metric("Attempts", len(attempts))
    columns[2].metric("Last draft checks", f"{passed}/{len(last_checks)}")
    columns[3].metric("Time", f"{report.get('seconds', 0):.1f}s")
    st.caption(f"Run {report.get('run_id', folder.name)} · {report.get('model', 'Unknown model')}")

    lesson_tab, review_tab, memory_tab, data_tab = st.tabs(
        ["Lesson", "Checks & retries", "Memory", "Run data"]
    )
    with lesson_tab:
        lesson_path = folder / "lesson.md"
        if report["status"] == "passed" and lesson_path.is_file():
            lesson = lesson_path.read_text(encoding="utf-8")
            st.download_button("Download lesson", lesson, "lesson.md", "text/markdown",
                               on_click="ignore", key="download_lesson")
            st.markdown(lesson)
        else:
            st.warning("No final lesson was released. Open Checks & retries to inspect the drafts.")
            if report.get("error"):
                st.error(report["error"])

    with review_tab:
        for attempt in attempts:
            checks = attempt.get("checks", [])
            count = sum(c.get("passed") is True for c in checks)
            number = attempt["number"]
            with st.expander(f"Attempt {number} · {count}/{len(checks)} checks passed",
                             expanded=number == 1):
                if attempt.get("injected_error"):
                    st.warning("A false RAG claim was deliberately inserted into this draft.")
                for check in checks:
                    icon = "✅" if check.get("passed") else "❌"
                    st.markdown(f"{icon} **{check['id'].replace('_', ' ').title()}**")
                    st.caption(check["reason"])
                if attempt.get("changes"):
                    st.markdown("**Writer-reported changes**")
                    for change in attempt["changes"]:
                        st.write(f"• {change}")
                draft_path = folder / f"attempt-{number}.md"
                if draft_path.is_file():
                    st.download_button("Download this draft", draft_path.read_text(encoding="utf-8"),
                                       f"attempt-{number}.md", "text/markdown", on_click="ignore",
                                       key=f"download_draft_{number}")
                # Use the expected generated name, never an arbitrary path from a report.
                diff_path = folder / f"attempt-{number}-changes.diff"
                if diff_path.is_file():
                    st.code(diff_path.read_text(encoding="utf-8"), language="diff")
        log_path = folder / "rejection-log.md"
        if log_path.is_file():
            st.download_button("Download rejection log", log_path.read_text(encoding="utf-8"),
                               "rejection-log.md", "text/markdown", on_click="ignore")

    with memory_tab:
        show_memory(report)

    with data_tab:
        st.caption("Full check results, extracted evidence, model usage and memory snapshots.")
        st.download_button("Download report", json.dumps(report, indent=2), "report.json",
                           "application/json", on_click="ignore")
        st.json(report, expanded=False)


def main():
    st.set_page_config(page_title="Lesson Loop", page_icon="📘", layout="wide")
    st.title("Lesson Loop")
    st.caption("Write a beginner lesson. Check every requirement. Revise before release.")
    st.markdown("**Generate → Evaluate → Revise → Release** · All 12 checks must pass.")

    try:
        pack = load_sources(ROOT / "sources/rag.json")
    except (OSError, ValueError) as exc:
        st.error(f"Cannot read the source pack: {exc}")
        return

    with st.sidebar:
        st.subheader("Connection")
        backend = st.selectbox("Provider", ["vertex", "gemini"],
                               index=0 if os.getenv("LLM_BACKEND", "vertex") == "vertex" else 1,
                               key="backend")
        default_project = os.getenv("GOOGLE_CLOUD_PROJECT") or (adc_project() if backend == "vertex" else "")
        project = st.text_input("Google Cloud project", default_project,
                                placeholder="your-project-id", disabled=backend != "vertex",
                                key="project")
        locations = ["us", "global", "eu"]
        default_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us")
        location = st.selectbox("Vertex location", locations,
                               index=locations.index(default_location) if default_location in locations else 0,
                               key="location")
        st.caption("Model: gemini-3.8-flash")
        st.caption("Vertex uses this computer's default ADC credentials and detects their project automatically. You can override the project above. Gemini API uses GEMINI_API_KEY.")
        st.divider()
        st.subheader("Teaching references")
        for source in pack["sources"]:
            st.markdown(f"[{source['id']} · {source['title']}]({source['url']})")
        st.caption("The bundled sources and rubric cover introductory RAG.")

    with st.form("new_run"):
        topic = st.text_input("Lesson topic", pack["topic"], key="topic")
        left, right = st.columns([1, 2])
        retries = left.selectbox("Maximum retries", [2, 1, 0], key="retries")
        inject_error = right.checkbox("Insert a deliberate error in the first draft", key="inject_error",
                                        help="Test whether the real evaluator catches a false guarantee about RAG.")
        submitted = st.form_submit_button("Generate & evaluate", type="primary")

    if submitted:
        if not topic.strip():
            st.error("Enter a lesson topic.")
        elif backend == "vertex" and not project.strip():
            st.error("Enter your Google Cloud project in the sidebar before starting a live run.")
        else:
            lock = generation_lock()
            if not lock.acquire(blocking=False):
                st.warning("Another generation is in progress. Wait for it to finish before starting a new run.")
            else:
                memory = None
                status = st.status("Starting a live run…", expanded=True)
                try:
                    model = Gemini("gemini-3.8-flash", backend, project.strip(), location)
                    memory = Memory(DATABASE)
                    report, folder = run(model, memory, topic.strip(), pack, RUNS,
                                         max_retries=retries, inject_error=inject_error,
                                         on_event=status.write)
                    st.session_state["view_run"] = str(folder)
                    if report["status"] == "passed":
                        status.update(label="Every check passed. Lesson released.", state="complete", expanded=False)
                    else:
                        status.update(label="Run finished without releasing a lesson.", state="error", expanded=True)
                except (ValueError, RuntimeError, OSError) as exc:
                    status.update(label="Could not complete the run.", state="error")
                    st.error(str(exc))
                finally:
                    if memory:
                        memory.close()
                    lock.release()

    st.divider()
    records = saved_runs()
    if not records:
        st.info("No saved runs yet. Generate a lesson to see the results here.")
        return
    if st.session_state.get("view_run") not in records:
        st.session_state["view_run"] = next(iter(records))

    def label(path):
        if Path(path) == EXAMPLE:
            return "Saved example · passing deliberate-error demonstration"
        report = records[path]
        return f"{Path(path).name} · {report['status']}"

    selected = st.selectbox("View a run", list(records), format_func=label, key="view_run")
    if Path(selected) == EXAMPLE:
        st.info("Viewing a saved, real Vertex run. Start a new run above to make fresh model calls.")
    show_result(Path(selected), records[selected])


if __name__ == "__main__":
    main()
