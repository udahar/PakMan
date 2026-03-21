# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Frank Skills Framework Module
Execute skills as LangChain tools - nanoclaw-style
Inspired by nanoclaw's skill system - custom Python implementation
"""


def create_skill_executor(
    model: str = "qwen2.5:7b",
    base_url: str = "http://127.0.0.1:11434",
    temperature: float = 0.7,
):
    """Factory function to create skill executor."""
    from .executor import SkillExecutor

    return SkillExecutor(model, base_url, temperature)


def create_skill_loader():
    """Factory function to create skill loader."""
    from .loader import SkillLoader

    return SkillLoader()


__all__ = [
    "create_skill_executor",
    "create_skill_loader",
]
