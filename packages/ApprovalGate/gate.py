"""
ApprovalGate - gate.py
Core interceptor that checks operations against a flagged registry
and pauses execution until human approval is received.

Usage:
    from ApprovalGate import gate, require_approval

    @require_approval("delete files")
    def delete_project(path):
        shutil.rmtree(path)

    # Or inline:
    if gate.request_approval("git push origin main"):
        subprocess.run(["git", "push"])
"""
import os
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional

from .notifiers import CLINotifier, BaseNotifier
from .registry import FlaggedOperationRegistry


class ApprovalGate:
    """
    Central approval interceptor.

    Agents call `request_approval(action)` before performing
    any sensitive operation. This class:
      1. Checks if the action is flagged
      2. Sends a notification to the configured notifier
      3. Blocks until a human responds y/n (or timeout)
    """

    def __init__(
        self,
        notifier: Optional[BaseNotifier] = None,
        auto_approve: bool = False,
        timeout: float = 300.0,
        audit_log_path: Optional[str] = None,
    ):
        self.registry = FlaggedOperationRegistry()
        self.notifier = notifier or CLINotifier()
        self.auto_approve = auto_approve
        self.timeout = timeout
        self._lock = threading.Lock()
        self._audit: List[dict] = []
        self._audit_path = audit_log_path

    # ── Public API ────────────────────────────────────────────────────────────

    def request_approval(
        self,
        action: str,
        context: Optional[str] = None,
        agent_id: str = "unknown",
    ) -> bool:
        """
        Request human approval for an action.

        Args:
            action:   Human-readable description of the action (e.g. "rm -rf /data")
            context:  Optional extra context surfaced to the approver
            agent_id: Which agent is requesting

        Returns:
            True if approved, False if denied or timed out.
        """
        if self.auto_approve:
            self._log(action, agent_id, approved=True, auto=True)
            return True

        if not self.registry.is_flagged(action):
            return True  # Not a sensitive action — allow freely

        approved = self.notifier.notify_and_wait(
            action=action,
            context=context,
            agent_id=agent_id,
            timeout=self.timeout,
        )
        self._log(action, agent_id, approved=approved)
        return approved

    def add_flag_pattern(self, pattern: str) -> None:
        """Register a new pattern as requiring approval."""
        self.registry.add(pattern)

    def get_audit_log(self) -> List[dict]:
        return list(self._audit)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _log(self, action: str, agent_id: str, approved: bool, auto: bool = False):
        import json
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "approved": approved,
            "auto": auto,
        }
        self._audit.append(entry)
        if self._audit_path:
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")


# ── Decorator ─────────────────────────────────────────────────────────────────

_default_gate: Optional[ApprovalGate] = None


def get_gate() -> ApprovalGate:
    global _default_gate
    if _default_gate is None:
        _default_gate = ApprovalGate()
    return _default_gate


def require_approval(action_label: str, gate: Optional[ApprovalGate] = None):
    """
    Decorator that pauses a function and requests human approval.

    @require_approval("delete project files")
    def delete_all(path): ...
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            g = gate or get_gate()
            if not g.request_approval(action_label):
                raise PermissionError(
                    f"ApprovalGate: Action denied — '{action_label}'"
                )
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
