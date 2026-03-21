# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Frank Recursive Context Module
Long context processing using RLM-style approach
Inspired by RLM paper (Recursive Language Models) - custom implementation
"""

from .wrapper import RecursiveLM, create_rlm
from .manager import ContextManager, create_context_manager

__all__ = [
    "RecursiveLM",
    "create_rlm",
    "ContextManager",
    "create_context_manager",
]
