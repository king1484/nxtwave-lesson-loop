import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from .memory import Memory
from .model import Gemini
from .pipeline import load_sources, memory_scope, run
from .rubric import ADVICE


def main():
    # Windows terminals otherwise vary with the machine's legacy code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Write a beginner lesson. Ship only if every check passes.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "memory", "feedback"):
        command = sub.add_parser(name)
        command.add_argument("--sources", default="sources/rag.json")
        command.add_argument("--topic", default=None, help="Defaults to the source pack's topic.")
        command.add_argument("--db", default="data/memory.sqlite3")
        if name == "generate":
            command.add_argument("--backend", choices=["gemini", "vertex"],
                                 default=os.getenv("LLM_BACKEND", "gemini"))
            command.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT"))
            command.add_argument("--location", choices=["global", "us", "eu"],
                                 default=os.getenv("GOOGLE_CLOUD_LOCATION", "global"))
            command.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
            command.add_argument("--max-retries", type=int, choices=range(3), default=2)
            command.add_argument("--output", default="runs")
            command.add_argument("--inject-error", action="store_true",
                                 help="Demo only: corrupt first draft; exclude this run from memory.")
        if name == "feedback":
            command.add_argument("--check", choices=sorted(ADVICE), required=True)
            command.add_argument("--note", required=True, help="Human explanation saved in feedback.jsonl.")
    args = parser.parse_args()
    memory = None
    try:
        pack = load_sources(args.sources)
        topic = args.topic or pack["topic"]
        if not topic.strip():
            raise ValueError("Topic cannot be empty.")
        memory = Memory(args.db)
        scope = memory_scope(topic, pack)
        if args.command == "memory":
            print(json.dumps(memory.snapshot(scope), indent=2))
        elif args.command == "feedback":
            event_id = "human-" + uuid4().hex
            feedback_path = Path(args.db).parent / "feedback.jsonl"
            with feedback_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event_id": event_id, "scope": scope,
                                         "check": args.check, "note": args.note}) + "\n")
            memory.record(scope, event_id, [args.check], origin="human")
            print("Feedback saved. Only the known check ID can influence future prompts.")
        else:
            model = Gemini(args.model, args.backend, args.project, args.location)
            report, output = run(model, memory, topic, pack, args.output,
                                 args.max_retries, args.inject_error)
            print(f"\nArtifacts: {output.resolve()}")
            return 0 if report["status"] == "passed" else 2
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Cannot run: {exc}", file=sys.stderr)
        return 2
    finally:
        if memory:
            memory.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
