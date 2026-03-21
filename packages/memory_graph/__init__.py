"""
Memory Graph - Knowledge Graph + Vector Hybrid

Combines:
- Vector search (Qdrant) for semantic similarity
- Knowledge graph (NetworkX) for relationships
- Hybrid queries for both

Usage:
    from memory_graph import MemoryGraph

    mg = MemoryGraph()

    # Add entities
    mg.add_entity("file1", "file", "auth.py", "Authentication module")
    mg.add_relationship("file1", "func1", "contains")

    # Hybrid query
    results = mg.hybrid_query("login vulnerability", relationships=["calls", "imports"])
"""

__version__ = "0.1.0"

from .memory_graph import (
    MemoryGraph,
    GraphEntity,
    get_memory_graph,
    add_entity,
    add_relationship,
    similar_to,
    hybrid_query,
    get_stats,
)

__all__ = [
    "MemoryGraph",
    "GraphEntity",
    "get_memory_graph",
    "add_entity",
    "add_relationship",
    "similar_to",
    "hybrid_query",
    "get_stats",
]
