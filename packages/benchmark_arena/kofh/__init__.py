"""
King-of-the-Hill Tournament System

A competitive model tournament where AI models fight for council seats.
"""

from kofh.tournament import TournamentSystem
from kofh.throne import ThroneManager, ThroneHolder
from kofh.scoring import ScoreCalculator, ScoreBreakdown
from kofh.leaderboard import Leaderboard

__version__ = "0.1.0"
__all__ = [
    "TournamentSystem",
    "ThroneManager",
    "ThroneHolder",
    "ScoreCalculator",
    "ScoreBreakdown",
    "Leaderboard",
]
