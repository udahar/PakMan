"""
FeedbackLoop - signal.py
Converts a DiffResult into a structured correction signal and persists it.
Signals can be consumed by PromptOS genome or stored in a JSONL log.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .differ import DiffResult


def build_signal(diff: DiffResult, original_prompt: str = "") -> dict:
    """
    Converts a diff into a reinforcement signal dict.

    Returns:
        {
            "filepath", "timestamp", "signal", "change_ratio",
            "original_prompt", "removed", "added", "correction"
        }
    """
    correction = "\n".join(diff.added)
    wrong = "\n".join(diff.removed)

    return {
        "filepath": diff.filepath,
        "timestamp": datetime.utcnow().isoformat(),
        "signal": "negative",          # Always negative — human corrected us
        "change_ratio": round(diff.change_ratio, 4),
        "original_prompt": original_prompt,
        "removed": wrong,
        "added": correction,
        "correction": correction,
    }


class SignalStore:
    """
    Persists correction signals to a JSONL log for replay or training.
    Thread-safe. Compatible with AutoDistiller (mine_from_jsonl).
    """

    def __init__(self, store_path: str = "feedback_signals.jsonl"):
        self.store_path = Path(store_path)
        self.store_path.touch(exist_ok=True)

    def save(self, signal: dict) -> None:
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal, ensure_ascii=False) + "\n")

    def load_all(self) -> list:
        lines = self.store_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(l) for l in lines if l.strip()]

    def count(self) -> int:
        return len(self.load_all())
