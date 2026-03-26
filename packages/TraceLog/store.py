"""
TraceLog - store.py
Persistence backends for completed traces.
Supports: in-memory, JSONL file, SQLite.
"""
import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional
from .spans import Trace


class InMemoryStore:
    """Volatile store. Fast for testing and single-session use."""

    def __init__(self, max_traces: int = 500):
        self._traces: List[Trace] = []
        self._max = max_traces
        self._lock = threading.Lock()

    def save(self, trace: Trace) -> None:
        with self._lock:
            self._traces.append(trace)
            if len(self._traces) > self._max:
                self._traces.pop(0)

    def get_all(self) -> List[Trace]:
        return list(self._traces)

    def get_errors(self) -> List[Trace]:
        return [t for t in self._traces if t.errors()]

    def clear(self) -> None:
        with self._lock:
            self._traces.clear()


class JSONLStore:
    """Append-only JSONL file store. Easy to grep/tail."""

    def __init__(self, path: str = "tracelog.jsonl"):
        self.path = Path(path)
        self.path.touch(exist_ok=True)

    def save(self, trace: Trace) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")

    def load_all(self) -> List[dict]:
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(l) for l in lines if l.strip()]

    def last_n(self, n: int = 20) -> List[dict]:
        return self.load_all()[-n:]


class SQLiteStore:
    """SQLite store. Queryable, durable, zero external deps."""

    def __init__(self, db_path: str = "tracelog.db"):
        self.db_path = db_path
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id    TEXT PRIMARY KEY,
                name        TEXT,
                created_at  TEXT,
                duration_ms REAL,
                span_count  INTEGER,
                error_count INTEGER,
                data        TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save(self, trace: Trace) -> None:
        d = trace.to_dict()
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO traces
            (trace_id, name, created_at, duration_ms, span_count, error_count, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            d["trace_id"], d["name"], d["created_at"],
            d["total_duration_ms"], d["span_count"], d["error_count"],
            json.dumps(d),
        ))
        conn.commit()
        conn.close()

    def get_errors(self) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT data FROM traces WHERE error_count > 0 ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]

    def last_n(self, n: int = 20) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT data FROM traces ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
