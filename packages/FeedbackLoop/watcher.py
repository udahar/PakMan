"""
FeedbackLoop - watcher.py
File-system watcher daemon. Detects when humans edit AI-generated output
and triggers diff capture + signal saving.

Requires: pip install watchdog
"""
import hashlib
import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class OutputTracker:
    """
    Tracks AI-generated outputs by fingerprinting them at creation time.
    Detected modifications are passed to a callback for diff analysis.
    """

    def __init__(self, on_change: Callable[[str, str, str], None]):
        """
        Args:
            on_change: Called with (filepath, original_content, new_content)
                       whenever a tracked file is changed.
        """
        self._registry: Dict[str, str] = {}   # path → original content
        self._hashes: Dict[str, str] = {}     # path → sha256 of original
        self._on_change = on_change
        self._lock = threading.Lock()

    def track(self, filepath: str, content: str) -> None:
        """Register a file as AI-generated output to watch."""
        with self._lock:
            self._registry[filepath] = content
            self._hashes[filepath] = _sha(content)

    def untrack(self, filepath: str) -> None:
        with self._lock:
            self._registry.pop(filepath, None)
            self._hashes.pop(filepath, None)

    def check(self, filepath: str) -> None:
        """Manually check if a file has been modified."""
        with self._lock:
            original = self._registry.get(filepath)
            if original is None:
                return
            try:
                current = Path(filepath).read_text(encoding="utf-8", errors="replace")
            except OSError:
                return
            if _sha(current) != self._hashes.get(filepath):
                self._on_change(filepath, original, current)
                # Update reference so we don't fire twice for the same edit
                self._hashes[filepath] = _sha(current)
                self._registry[filepath] = current

    def tracked_paths(self) -> List[str]:
        with self._lock:
            return list(self._registry.keys())


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


# ── Watchdog integration ──────────────────────────────────────────────────────

class _WatchdogHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    def __init__(self, tracker: OutputTracker):
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self._tracker = tracker

    def on_modified(self, event):
        if not event.is_directory:
            self._tracker.check(event.src_path)


class FeedbackWatcher:
    """
    High-level watcher that combines OutputTracker + watchdog Observer.
    Call `watch_dir(path)` to monitor a folder for changes to tracked files.
    """

    def __init__(self, tracker: OutputTracker):
        self.tracker = tracker
        self._observer: Optional[object] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def watch_dir(self, path: str) -> None:
        """Start watching a directory (uses watchdog if available, else polling)."""
        if WATCHDOG_AVAILABLE:
            self._observer = Observer()
            self._observer.schedule(_WatchdogHandler(self.tracker), path, recursive=True)
            self._observer.start()
            print(f"[FeedbackLoop] Watching (watchdog): {path}")
        else:
            self._start_poll_fallback()
            print(f"[FeedbackLoop] Watching (poll): {path}")

    def _start_poll_fallback(self, interval: float = 2.0) -> None:
        def poll():
            while not self._stop.is_set():
                for fp in self.tracker.tracked_paths():
                    self.tracker.check(fp)
                time.sleep(interval)
        self._poll_thread = threading.Thread(target=poll, daemon=True)
        self._poll_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._observer:
            self._observer.stop()
            self._observer.join()
