"""
Context Manager - Smart Context Window

Automatically manage what AI remembers.
"""

__version__ = "1.0.0"

from .manager import ContextManager
from .relevance import RelevanceScorer
from .layers import MemoryLayers
from .selectors import TaskSelector
from .distiller import ContextDistiller

__all__ = [
    "ContextManager",
    "RelevanceScorer",
    "MemoryLayers",
    "TaskSelector",
    "ContextDistiller",
]
