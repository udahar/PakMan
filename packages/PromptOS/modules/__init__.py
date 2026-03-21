"""
PromptOS Modules
=================

Self-improvement modules for Alfred/Frank cognitive architecture.

Modules:
- reflection_loop: Self-critique agent that watches execution
- tool_use_miner: Auto-discovers skills from execution logs
"""

from .reflection_loop import (
    ReflectionLoop,
    ReflectionMode,
    ReflectionSession,
    ExecutionStep,
    Critique,
    StrategyEffectiveness,
    create_reflection_loop,
)

from .tool_use_miner import (
    ToolUseMiner,
    ToolPattern,
    DiscoveredSkill,
    SkillRegistrar,
    LogEntry,
    PatternConfidence,
    SkillSource,
    create_tool_use_miner,
)

__all__ = [
    # Reflection Loop
    "ReflectionLoop",
    "ReflectionMode",
    "ReflectionSession",
    "ExecutionStep",
    "Critique",
    "StrategyEffectiveness",
    "create_reflection_loop",
    # Tool Use Mining
    "ToolUseMiner",
    "ToolPattern",
    "DiscoveredSkill",
    "SkillRegistrar",
    "LogEntry",
    "PatternConfidence",
    "SkillSource",
    "create_tool_use_miner",
]
