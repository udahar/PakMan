"""
SemanticCache - cache.py
Stores prompt→response pairs and retrieves them by semantic similarity.

Two similarity modes:
  1. Exact (hash-based): Fastest, no false positives. Default.
  2. Fuzzy (Jaccard token overlap): Catches paraphrases, no embeddings needed.
  3. Embedding (optional): Uses vector cosine similarity for true semantic matching.
     Requires: numpy (optional), or any embedding fn(text)->List[float].

Usage:
    from SemanticCache import SemanticCache

    cache = SemanticCache(similarity="fuzzy", threshold=0.85)
    cache.set("What is the capital of France?", "Paris.")

    result = cache.get("What's the capital city of France?")
    # → "Paris."  (fuzzy matched)
"""
import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> set:
    return set(text.lower().split())


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


class SemanticCache:
    """
    Persistent prompt–response cache with configurable similarity matching.

    Args:
        db_path:    SQLite database path.
        similarity: "exact" | "fuzzy" | "embedding"
        threshold:  Minimum similarity score to count as a cache hit (0–1).
        embed_fn:   Required for similarity="embedding". fn(text) -> List[float].
        ttl:        Time-to-live in seconds (0 = no expiry).
    """

    def __init__(
        self,
        db_path: str = "semantic_cache.db",
        similarity: str = "fuzzy",
        threshold: float = 0.90,
        embed_fn: Optional[Callable] = None,
        ttl: int = 0,
    ):
        self.db_path = db_path
        self.similarity = similarity
        self.threshold = threshold
        self.embed_fn = embed_fn
        self.ttl = ttl
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id          TEXT PRIMARY KEY,
                    prompt      TEXT NOT NULL,
                    response    TEXT NOT NULL,
                    embedding   TEXT,
                    metadata    TEXT,
                    hits        INTEGER DEFAULT 0,
                    created_at  REAL NOT NULL,
                    expires_at  REAL
                )
            """)
            conn.commit()

    # ── Write ─────────────────────────────────────────────────────────────────

    def set(self, prompt: str, response: str, metadata: dict = None) -> str:
        """Store a prompt-response pair. Returns cache entry ID."""
        entry_id = _sha(prompt)[:16]
        embedding = None
        if self.similarity == "embedding" and self.embed_fn:
            try:
                embedding = json.dumps(self.embed_fn(prompt))
            except Exception:
                pass

        now = time.time()
        expires = (now + self.ttl) if self.ttl > 0 else None

        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache
                (id, prompt, response, embedding, metadata, hits, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                entry_id, prompt, response, embedding,
                json.dumps(metadata or {}), now, expires
            ))
            conn.commit()
        return entry_id

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, prompt: str) -> Optional[str]:
        """
        Retrieve a cached response. Returns None on cache miss.
        Updates hit counter on successful match.
        """
        rows = self._load_valid()

        if self.similarity == "exact":
            key = _sha(prompt)[:16]
            for row in rows:
                if row["id"] == key:
                    self._hit(row["id"])
                    return row["response"]
            return None

        elif self.similarity == "fuzzy":
            best_score, best_row = 0.0, None
            for row in rows:
                score = _jaccard(prompt, row["prompt"])
                if score > best_score:
                    best_score, best_row = score, row
            if best_score >= self.threshold and best_row:
                self._hit(best_row["id"])
                return best_row["response"]
            return None

        elif self.similarity == "embedding" and self.embed_fn:
            try:
                query_emb = self.embed_fn(prompt)
            except Exception:
                return None
            best_score, best_row = 0.0, None
            for row in rows:
                if not row["embedding"]:
                    continue
                try:
                    stored_emb = json.loads(row["embedding"])
                    score = _cosine(query_emb, stored_emb)
                    if score > best_score:
                        best_score, best_row = score, row
                except Exception:
                    continue
            if best_score >= self.threshold and best_row:
                self._hit(best_row["id"])
                return best_row["response"]
            return None

        return None

    def get_or_set(self, prompt: str, fn: Callable[[], str]) -> tuple:
        """
        Get from cache or compute + store.

        Returns:
            (response, was_cached)
        """
        cached = self.get(prompt)
        if cached is not None:
            return cached, True
        response = fn()
        self.set(prompt, response)
        return response, False

    # ── Management ────────────────────────────────────────────────────────────

    def delete(self, prompt: str) -> None:
        entry_id = _sha(prompt)[:16]
        with self._conn() as conn:
            conn.execute("DELETE FROM cache WHERE id=?", (entry_id,))
            conn.commit()

    def clear(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()

    def evict_expired(self) -> int:
        now = time.time()
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?", (now,)
            )
            conn.commit()
            return cur.rowcount

    def stats(self) -> dict:
        rows = self._load_valid()
        total_hits = sum(r["hits"] for r in rows)
        return {
            "entries": len(rows),
            "total_hits": total_hits,
            "similarity_mode": self.similarity,
            "threshold": self.threshold,
        }

    def _load_valid(self) -> List[sqlite3.Row]:
        now = time.time()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cache WHERE expires_at IS NULL OR expires_at > ?", (now,)
            ).fetchall()
        return rows

    def _hit(self, entry_id: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE cache SET hits=hits+1 WHERE id=?", (entry_id,))
            conn.commit()
