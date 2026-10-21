"""Local, auditable memory. Raw evaluator text never becomes a system instruction."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .rubric import ADVICE, VERSION


class Memory:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS failures (
                scope TEXT, rubric TEXT, check_id TEXT, run_id TEXT,
                origin TEXT, created_at TEXT,
                UNIQUE(scope, rubric, check_id, run_id)
            );
        """)

    def record(self, scope, run_id, ids, origin="evaluation"):
        rows = [(scope, VERSION, cid, run_id, origin,
                 datetime.now(timezone.utc).isoformat())
                for cid in set(ids) if cid in ADVICE]
        with self.db:
            self.db.executemany("INSERT OR IGNORE INTO failures VALUES (?, ?, ?, ?, ?, ?)", rows)

    def snapshot(self, scope):
        rows = self.db.execute("""
            SELECT check_id, COUNT(DISTINCT run_id) FROM failures
            WHERE scope=? AND rubric=? GROUP BY check_id ORDER BY check_id
        """, (scope, VERSION)).fetchall()
        return {"failure_counts": dict(rows), "active_guidance": [
            {"check_id": cid, "failed_runs": count, "instruction": ADVICE[cid]}
            for cid, count in rows if count >= 2
        ]}

    def close(self):
        self.db.close()
