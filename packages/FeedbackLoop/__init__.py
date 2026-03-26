"""
FeedbackLoop
Capture human corrections to AI output and feed them back as learning signals.

Quick start:
    from FeedbackLoop import FeedbackLoop

    fl = FeedbackLoop(signal_store="corrections.jsonl")

    # Register an AI-generated output file
    fl.track("output.py", original_content=ai_code)

    # Start watching the file for changes
    fl.start(watch_dir=".")

    # Later — query collected signals
    signals = fl.get_signals()
"""
import threading
from pathlib import Path
from typing import Optional

from .watcher import OutputTracker, FeedbackWatcher
from .differ import compute_diff
from .signal import build_signal, SignalStore


class FeedbackLoop:
    """
    All-in-one orchestrator for FeedbackLoop.

    1. Track AI output files with track()
    2. Start file watching with start()
    3. Corrections are automatically captured and saved to signal_store
    """

    def __init__(
        self,
        signal_store: str = "feedback_signals.jsonl",
        min_change_ratio: float = 0.01,
    ):
        self.store = SignalStore(signal_store)
        self.min_change = min_change_ratio
        self._prompt_map = {}   # filepath → original_prompt

        def on_change(filepath: str, original: str, modified: str):
            diff = compute_diff(filepath, original, modified)
            if diff.is_meaningful and diff.change_ratio >= self.min_change:
                prompt = self._prompt_map.get(filepath, "")
                sig = build_signal(diff, original_prompt=prompt)
                self.store.save(sig)
                print(f"[FeedbackLoop] Correction captured ({filepath}) "
                      f"Δ={diff.change_ratio:.1%}")

        self.tracker = OutputTracker(on_change=on_change)
        self.watcher = FeedbackWatcher(self.tracker)

    def track(self, filepath: str, content: str, original_prompt: str = "") -> None:
        """Register an AI-generated output file to watch."""
        self.tracker.track(filepath, content)
        if original_prompt:
            self._prompt_map[filepath] = original_prompt

    def start(self, watch_dir: str = ".") -> None:
        """Start the file watcher (non-blocking)."""
        self.watcher.watch_dir(watch_dir)

    def stop(self) -> None:
        self.watcher.stop()

    def get_signals(self) -> list:
        return self.store.load_all()

    def signal_count(self) -> int:
        return self.store.count()


__version__ = "0.1.0"
__all__ = ["FeedbackLoop", "SignalStore", "build_signal", "compute_diff"]
