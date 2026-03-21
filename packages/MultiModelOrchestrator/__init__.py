# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Frank Multi-Model Orchestrator Module
Coordinates multiple Ollama models in parallel for complex tasks
Custom written based on FRANK_2_FEATURES.md ideas
"""


def create_orchestrator(
    base_url: str = "http://127.0.0.1:11434",
    temperature: float = 0.7,
    models: dict = None,
):
    """Factory function to create orchestrator."""
    from .orchestrator import MultiModelOrchestrator

    return MultiModelOrchestrator(
        base_url=base_url, temperature=temperature, default_roles=models
    )


def get_default_roles():
    """Get default roles."""
    from .roles import get_default_roles as _get

    return _get()


__all__ = [
    "create_orchestrator",
    "get_default_roles",
]
