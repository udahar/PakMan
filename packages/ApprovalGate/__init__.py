"""
ApprovalGate
Human-in-the-loop safety interlock for AI agents.

Quick start:
    from ApprovalGate import ApprovalGate, require_approval

    gate = ApprovalGate()

    # Inline check
    if gate.request_approval("rm -rf /tmp/project"):
        shutil.rmtree("/tmp/project")

    # Decorator pattern
    @require_approval("deploy to production")
    def deploy(): ...

    # Telegram alerts
    from ApprovalGate.notifiers import TelegramNotifier
    gate = ApprovalGate(notifier=TelegramNotifier())

    # CI/automation — skip all prompts
    gate = ApprovalGate(auto_approve=True)
"""
from .gate import ApprovalGate, require_approval, get_gate
from .registry import FlaggedOperationRegistry
from .notifiers import CLINotifier, TelegramNotifier

__version__ = "0.1.0"
__all__ = [
    "ApprovalGate",
    "require_approval",
    "get_gate",
    "FlaggedOperationRegistry",
    "CLINotifier",
    "TelegramNotifier",
]
