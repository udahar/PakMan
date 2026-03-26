"""
AutoDistiller - miner.py
Mines high-scoring AI runs from PromptForge history and returns
clean training example dicts.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


def _load_jsonl(path: str) -> List[dict]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def mine_from_promptforge_db(
    db_path: str,
    min_score: float = 0.8,
    table: str = "promptforge_experiments",
) -> List[dict]:
    """
    Mine training examples from a PromptForge SQLite experiment log.

    Args:
        db_path:   Path to the PromptForge SQLite database.
        min_score: Minimum quality score to include (0–1).
        table:     Table containing experiment results.

    Returns:
        List of raw example dicts with keys: prompt, response, score, task_type.
    """
    if not Path(db_path).exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(f"""
            SELECT prompt, response, score, task_type
            FROM {table}
            WHERE score >= ?
            ORDER BY score DESC
        """, (min_score,)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[AutoDistiller/mine] DB query failed: {e}")
        return []
    finally:
        conn.close()


def mine_from_jsonl(jsonl_path: str, min_score: float = 0.8) -> List[dict]:
    """
    Mine from a JSONL log file exported from PromptForge.
    Each line: {"prompt": "...", "response": "...", "score": 0.9, "task_type": "..."}
    """
    rows = _load_jsonl(jsonl_path)
    return [r for r in rows if r.get("score", 0) >= min_score]


def deduplicate(examples: List[dict], sim_threshold: float = 0.95) -> List[dict]:
    """
    Remove near-duplicate prompts via simple normalized Jaccard similarity.
    Full semantic dedup (embedding-based) is opt-in via SemanticCache.
    """
    seen: List[set] = []
    unique = []
    for ex in examples:
        tokens = set(str(ex.get("prompt", "")).lower().split())
        if not tokens:
            continue
        is_dup = any(
            len(tokens & s) / max(len(tokens | s), 1) >= sim_threshold
            for s in seen
        )
        if not is_dup:
            unique.append(ex)
            seen.append(tokens)
    return unique
