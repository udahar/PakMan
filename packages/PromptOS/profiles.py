"""
Model Profiles - Learned Strategy Preferences Per Model
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModelProfile:
    """Learned preferences for a specific model."""
    model_name: str
    preferred_strategies: Dict[str, List[str]]  # task_type → strategy_stack
    avoided_modules: List[str]
    token_efficiency: float
    reasoning_capability: float
    code_capability: float


MODEL_PROFILES = {
    "qwen2.5:3b": ModelProfile(
        model_name="qwen2.5:3b",
        preferred_strategies={
            "reasoning": ["scratchpad_only"],
            "coding": ["scratchpad_verify"],
            "debugging": ["scratchpad_verify"],
            "chat": ["baseline"],
        },
        avoided_modules=["format", "planner"],
        token_efficiency=0.7,
        reasoning_capability=0.5,
        code_capability=0.6,
    ),
    
    "qwen2.5:7b": ModelProfile(
        model_name="qwen2.5:7b",
        preferred_strategies={
            "reasoning": ["scratchpad_verify"],
            "coding": ["planner_solver"],
            "debugging": ["full_hybrid"],
            "tools": ["scratchpad_tools"],
            "chat": ["baseline"],
        },
        avoided_modules=["format"],
        token_efficiency=0.8,
        reasoning_capability=0.7,
        code_capability=0.8,
    ),
    
    "llama3.2:3b": ModelProfile(
        model_name="llama3.2:3b",
        preferred_strategies={
            "reasoning": ["scratchpad_only"],
            "coding": ["scratchpad_verify"],
            "chat": ["baseline"],
        },
        avoided_modules=["format", "planner", "tools"],
        token_efficiency=0.75,
        reasoning_capability=0.55,
        code_capability=0.5,
    ),
    
    "gpt-4o": ModelProfile(
        model_name="gpt-4o",
        preferred_strategies={
            "reasoning": ["baseline"],
            "coding": ["planner_solver"],
            "chat": ["baseline"],
            "formatting": ["strict_output"],
        },
        avoided_modules=["decompose", "scratchpad"],
        token_efficiency=0.95,
        reasoning_capability=0.95,
        code_capability=0.9,
    ),
}
