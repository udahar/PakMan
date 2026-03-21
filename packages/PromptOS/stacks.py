"""
Strategy Stacks - Pre-Tested Module Combinations
"""

from dataclasses import dataclass
from typing import List


@dataclass
class StrategyStack:
    """A pre-tested combination of modules."""
    name: str
    modules: List[str]
    best_for_models: List[str]
    best_for_tasks: List[str]
    avg_improvement: float
    description: str


STRATEGY_STACKS = {
    "baseline": StrategyStack(
        name="baseline",
        modules=[],
        best_for_models=["gpt-4o", "claude-opus"],
        best_for_tasks=["chat", "simple_qa"],
        avg_improvement=0.0,
        description="No special strategies - raw model capability"
    ),
    
    "scratchpad_only": StrategyStack(
        name="scratchpad_only",
        modules=["scratchpad"],
        best_for_models=["qwen2.5:3b", "qwen2.5:7b", "llama3.2:3b"],
        best_for_tasks=["reasoning", "math"],
        avg_improvement=0.15,
        description="Simple scratchpad for step-by-step reasoning"
    ),
    
    "scratchpad_verify": StrategyStack(
        name="scratchpad_verify",
        modules=["scratchpad", "verify"],
        best_for_models=["qwen2.5:3b", "gemma2:2b"],
        best_for_tasks=["reasoning", "math", "logic"],
        avg_improvement=0.25,
        description="Scratchpad reasoning with self-verification"
    ),
    
    "scratchpad_tools": StrategyStack(
        name="scratchpad_tools",
        modules=["scratchpad", "tools"],
        best_for_models=["qwen2.5:7b", "llama3.2:3b"],
        best_for_tasks=["tools", "coding"],
        avg_improvement=0.20,
        description="Scratchpad with tool planning"
    ),
    
    "planner_solver": StrategyStack(
        name="planner_solver",
        modules=["planner"],
        best_for_models=["codex", "claude-sonnet", "qwen2.5:7b"],
        best_for_tasks=["coding"],
        avg_improvement=0.30,
        description="Plan-then-solve pattern for coding"
    ),
    
    "full_hybrid": StrategyStack(
        name="full_hybrid",
        modules=["role", "decompose", "scratchpad", "tools", "verify"],
        best_for_models=["qwen2.5:7b", "llama3.2:3b"],
        best_for_tasks=["coding", "debugging", "complex_reasoning"],
        avg_improvement=0.35,
        description="Full hybrid reasoning pipeline"
    ),
    
    "strict_output": StrategyStack(
        name="strict_output",
        modules=["format"],
        best_for_models=["gpt-4o", "claude-sonnet"],
        best_for_tasks=["formatting", "extraction"],
        avg_improvement=0.10,
        description="Strict output formatting only"
    ),
    
    "few_shot_coding": StrategyStack(
        name="few_shot_coding",
        modules=["few_shot", "scratchpad"],
        best_for_models=["qwen2.5:3b", "qwen2.5:7b"],
        best_for_tasks=["coding"],
        avg_improvement=0.28,
        description="Examples + scratchpad for coding tasks"
    ),
}
