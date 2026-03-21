"""
The Courtroom - AI Code Review Architecture

A structured disagreement system where AI agents argue about code quality.
"""

from courtroom.scribe import Scribe
from courtroom.critic import Critic, LokiCritic
from courtroom.judge import Judge, JudgeDecision
from courtroom.harness import Harness, HarnessVerdict
from courtroom.session import CourtroomSession

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
