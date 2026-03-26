"""Benchmark Arena - Evaluation and benchmarking framework."""

__version__ = "1.0.0"

from .arena import BenchmarkArena, ArenaResult
from .kofh import (
    Throne,
    Leaderboard,
    Tournament,
    ScoringEngine,
    Evaluator,
)

__all__ = [
    "BenchmarkArena",
    "ArenaResult",
    "Throne",
    "Leaderboard",
    "Tournament",
    "ScoringEngine",
    "Evaluator",
]
