"""Claw — Thin CLI wrapper for Alfred AI platform."""

from .claw import ClawClient, submit_task, wait_for_result
from .claw import claw_ask, claw_bench, claw_models, claw_arena, claw_crown

__all__ = [
    "ClawClient",
    "submit_task",
    "wait_for_result",
    "claw_ask",
    "claw_bench",
    "claw_models",
    "claw_arena",
    "claw_crown",
]
