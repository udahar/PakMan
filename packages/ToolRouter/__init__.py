"""
tool_router — semantic tool name resolution for multi-model AI systems.

Maps the natural vocabulary different models reach for (e.g. "snapshot_repo",
"vector_search", "audit_log") to your actual tool/API names.

Seeded from benchmark data: 153 responses across 80 models revealing per-family
vocabulary patterns. Extend by adding more intents to data/semantic_tools_map.json
or by running targeted ToolVocab benchmark tests.

Quick start:
    from tool_router import ToolRouter
    router = ToolRouter()
    router.resolve("snapshot_repo", model="codex/gpt-5.3-codex")  # → "bridge.read"
    router.resolve("vector_search")                                # → "qdrant:similarity"
    router.aliases_for_intent("safe_code_mutation_sequence")       # → {family: [terms]}
"""

from .router import ToolRouter

__all__ = ["ToolRouter"]
__version__ = "0.1.0"
