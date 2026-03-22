"""
The Council - Multi-Mind AI Architecture

A distributed decision-making system where specialized AI models
serve different roles in a checks-and-balances architecture.
"""

from .roles import CouncilRole, Planner, Engineer, Scientist, Governor, Archivist
from .decision import CouncilDecision, DecisionStatus
from .session import CouncilSession

__version__ = "0.1.0"
__all__ = [
    "CouncilRole",
    "Planner",
    "Engineer",
    "Scientist",
    "Governor",
    "Archivist",
    "CouncilDecision",
    "DecisionStatus",
    "CouncilSession",
]
