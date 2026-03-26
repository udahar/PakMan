"""
ApprovalGate - notifiers.py
Pluggable notification backends. CLI blocks inline; Telegram is async.
"""
import os
import sys
import time
import threading
from abc import ABC, abstractmethod
from typing import Optional


class BaseNotifier(ABC):
    @abstractmethod
    def notify_and_wait(
        self, action: str, context: Optional[str],
        agent_id: str, timeout: float
    ) -> bool:
        """Send notification and return True if approved."""


class CLINotifier(BaseNotifier):
    """
    Blocks the current thread, printing to stdout and waiting for y/n.
    Works in any terminal environment.
    """

    def notify_and_wait(
        self, action: str, context: Optional[str],
        agent_id: str, timeout: float
    ) -> bool:
        print("\n" + "=" * 55)
        print("⚠️  APPROVAL REQUIRED")
        print("=" * 55)
        print(f"  Agent:   {agent_id}")
        print(f"  Action:  {action}")
        if context:
            print(f"  Context: {context}")
        print(f"  Timeout: {int(timeout)}s")
        print("=" * 55)

        answer = _timed_input("  Approve? [y/n]: ", timeout)
        approved = answer.strip().lower() in ("y", "yes")
        print(f"  → {'✅ Approved' if approved else '❌ Denied'}\n")
        return approved


class TelegramNotifier(BaseNotifier):
    """
    Sends a Telegram message and polls for a reply.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def notify_and_wait(
        self, action: str, context: Optional[str],
        agent_id: str, timeout: float
    ) -> bool:
        if not self.token or not self.chat_id:
            print("[ApprovalGate/Telegram] Missing credentials — falling back to CLI")
            return CLINotifier().notify_and_wait(action, context, agent_id, timeout)

        import requests  # Only required for Telegram mode

        text = (
            f"⚠️ *APPROVAL REQUIRED*\n"
            f"Agent: `{agent_id}`\n"
            f"Action: `{action}`\n"
            + (f"Context: {context}\n" if context else "")
            + "Reply *y* to approve or *n* to deny."
        )
        self._send(text, requests)

        deadline = time.monotonic() + timeout
        last_update_id = None

        while time.monotonic() < deadline:
            updates = self._get_updates(requests, last_update_id)
            for upd in updates:
                last_update_id = upd.get("update_id", last_update_id)
                msg = upd.get("message", {}).get("text", "").strip().lower()
                if msg in ("y", "yes", "n", "no"):
                    return msg in ("y", "yes")
            time.sleep(1.5)

        self._send("⏰ Approval timed out — action denied.", requests)
        return False

    def _send(self, text: str, requests) -> None:
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"[Telegram] Send failed: {e}")

    def _get_updates(self, requests, offset) -> list:
        try:
            params = {"timeout": 1, "allowed_updates": ["message"]}
            if offset is not None:
                params["offset"] = offset + 1
            r = requests.get(
                f"https://api.telegram.org/bot{self.token}/getUpdates",
                params=params,
                timeout=5,
            )
            return r.json().get("result", [])
        except Exception:
            return []


# ── helpers ───────────────────────────────────────────────────────────────────

def _timed_input(prompt: str, timeout: float) -> str:
    """Read a line from stdin with a timeout (cross-platform)."""
    result = [""]

    def reader():
        try:
            result[0] = input(prompt)
        except Exception:
            result[0] = "n"

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        print(f"\n  [Timeout reached — defaulting to deny]")
        return "n"
    return result[0]
