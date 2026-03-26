"""Claw - Thin CLI wrapper for Alfred AI platform."""

import os

__version__ = "0.1.0"
__author__ = os.environ.get("PACKAGE_AUTHOR", "Richard")
__email__ = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com")

try:
    from .core import ClawClient, submit_task, wait_for_result
    from .core import claw_ask, claw_bench, claw_models, claw_arena, claw_crown
    from .cli import main
    __all__ = [
        "ClawClient",
        "submit_task",
        "wait_for_result",
        "claw_ask",
        "claw_bench",
        "claw_models",
        "claw_arena",
        "claw_crown",
        "main",
    ]
except ImportError:
    __all__ = []
