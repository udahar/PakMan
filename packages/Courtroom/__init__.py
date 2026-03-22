"""
The Courtroom - AI Code Review Architecture

A structured disagreement system where AI agents argue about code quality.
"""

from .scribe import Scribe
from .critic import Critic, LokiCritic
from .judge import Judge, JudgeDecision
from .harness import Harness, HarnessVerdict
from .session import CourtroomSession

__version__ = "0.1.0"
__all__ = [
    "Scribe",
    "Critic",
    "LokiCritic",
    "Judge",
    "JudgeDecision",
    "Harness",
    "HarnessVerdict",
    "CourtroomSession",
]
