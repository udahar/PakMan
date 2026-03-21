# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Strategies
Strategy definitions for prompt_library
Integrates with PromptOS strategy research
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class StrategyType(Enum):
    """Types of prompt strategies."""

    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    ROLE_PLAY = "role_play"
    TASK_DECOMPOSITION = "task_decomposition"
    SELF_REFLECTION = "self_reflection"
    ITERATIVE = "iterative"
    PARALLEL = "parallel"
    TREE_OF_THOUGHT = "tree_of_thought"
    SCoT = "self_consistent_cot"
    REACT = "react"
    REFLEXION = "reflexion"
    META_PROMPTING = "meta_prompting"
    PERSONA_STACK = "persona_stack"
    CONTRASTIVE = "contrastive"
    CHUNKING = "chunking"


@dataclass
class PromptStrategy:
    """A prompt strategy with templates."""

    strategy_id: str
    name: str
    description: str
    strategy_type: StrategyType
    templates: List[str]
    best_for: List[str]
    effectiveness: float = 0.0


class PromptStrategies:
    """
    Pre-defined strategies for prompt optimization.

    These integrate with PromptOS strategy research engine.
    """

    STRATEGIES = [
        PromptStrategy(
            strategy_id="cot_basic",
            name="Chain of Thought (Basic)",
            description="Think step by step through the problem",
            strategy_type=StrategyType.CHAIN_OF_THOUGHT,
            templates=[
                "Let's think step by step: {task}",
                "Break this down into steps: {task}",
            ],
            best_for=["reasoning", "analysis", "problem_solving"],
            effectiveness=0.85,
        ),
        PromptStrategy(
            strategy_id="cot_detailed",
            name="Chain of Thought (Detailed)",
            description="Detailed step-by-step reasoning with explanations",
            strategy_type=StrategyType.CHAIN_OF_THOUGHT,
            templates=[
                "Solve this step by step, explaining each step:\n{task}",
            ],
            best_for=["complex_reasoning", "math", "logic"],
            effectiveness=0.90,
        ),
        PromptStrategy(
            strategy_id="few_shot_3",
            name="Few-Shot (3 examples)",
            description="Provide 3 examples before asking",
            strategy_type=StrategyType.FEW_SHOT,
            templates=[
                """Example 1: {example1}
Example 2: {example2}
Example 3: {example3}

Now do this: {task}""",
            ],
            best_for=["classification", "formatting", "translation"],
            effectiveness=0.88,
        ),
        PromptStrategy(
            strategy_id="role_expert",
            name="Expert Role",
            description="Act as an expert in the field",
            strategy_type=StrategyType.ROLE_PLAY,
            templates=[
                "You are an expert {field}. {task}",
                "Act as a {level} {field} specialist. {task}",
            ],
            best_for=["domain_specific", "technical", "advice"],
            effectiveness=0.82,
        ),
        PromptStrategy(
            strategy_id="decompose",
            name="Task Decomposition",
            description="Break complex tasks into subtasks",
            strategy_type=StrategyType.TASK_DECOMPOSITION,
            templates=[
                "Break this into subtasks: {task}",
                "First, identify the components. Then solve each: {task}",
            ],
            best_for=["complex_tasks", "planning", "multi_step"],
            effectiveness=0.87,
        ),
        PromptStrategy(
            strategy_id="reflect",
            name="Self-Reflection",
            description="Review and improve your own output",
            strategy_type=StrategyType.SELF_REFLECTION,
            templates=[
                "{task}\n\nAfter answering, review your response and improve it.",
            ],
            best_for=["writing", "coding", "analysis"],
            effectiveness=0.80,
        ),
        PromptStrategy(
            strategy_id="iterate",
            name="Iterative Refinement",
            description="Improve through iterations",
            strategy_type=StrategyType.ITERATIVE,
            templates=[
                "Draft 1: {task}\n\nRefine based on feedback: {feedback}",
            ],
            best_for=["creative", "writing", "optimization"],
            effectiveness=0.85,
        ),
        PromptStrategy(
            strategy_id="parallel_experts",
            name="Parallel Expert Opinion",
            description="Get multiple expert perspectives",
            strategy_type=StrategyType.PARALLEL,
            templates=[
                "Expert 1 perspective: {task}\nExpert 2 perspective: {task}\nSynthesize:",
            ],
            best_for=["decision_making", "comprehensive_analysis"],
            effectiveness=0.83,
        ),
        PromptStrategy(
            strategy_id="tot",
            name="Tree of Thought",
            description="Explore multiple reasoning paths",
            strategy_type=StrategyType.TREE_OF_THOUGHT,
            templates=[
                "Explore 3 different approaches to: {task}\nCompare and choose the best.",
            ],
            best_for=["creative_problem_solving", "strategic_planning"],
            effectiveness=0.89,
        ),
        PromptStrategy(
            strategy_id="scot",
            name="Self-Consistent Chain of Thought",
            description="Generate multiple reasoning paths, select most consistent",
            strategy_type=StrategyType.SCoT,
            templates=[
                "Solve {task} using 3 different approaches. Identify which answer appears most consistently.",
            ],
            best_for=["reasoning", "math", "logic"],
            effectiveness=0.91,
        ),
        PromptStrategy(
            strategy_id="react",
            name="ReAct (Reasoning + Acting)",
            description="Interleave reasoning with action steps",
            strategy_type=StrategyType.REACT,
            templates=[
                "For {task}: Think step by step, then take action. Observe result, reason again, repeat.",
            ],
            best_for=["tool_use", "complex_tasks", "research"],
            effectiveness=0.88,
        ),
        PromptStrategy(
            strategy_id="reflexion",
            name="Reflexion",
            description="Learn from past errors, reflect and improve",
            strategy_type=StrategyType.REFLEXION,
            templates=[
                "Complete this task: {task}\nAfter: Reflect on your answer. What worked? What didn't?",
            ],
            best_for=["learning", "improvement", "self_correction"],
            effectiveness=0.87,
        ),
        PromptStrategy(
            strategy_id="meta_prompting",
            name="Meta-Prompting",
            description="Prompt the model about prompting",
            strategy_type=StrategyType.META_PROMPTING,
            templates=[
                "Task: {task}\n\nFirst, determine the best approach. Then execute it.",
            ],
            best_for=["self_improvement", "strategy", "planning"],
            effectiveness=0.85,
        ),
        PromptStrategy(
            strategy_id="persona_stack",
            name="Persona Stack",
            description="Multiple personas collaborate on solution",
            strategy_type=StrategyType.PERSONA_STACK,
            templates=[
                "Solve {task} with these experts: (1) Analyst, (2) Creator, (3) Critic. Combine insights.",
            ],
            best_for=["creative", "complex", "multidimensional"],
            effectiveness=0.86,
        ),
        PromptStrategy(
            strategy_id="contrastive",
            name="Contrastive Generation",
            description="Generate and critique simultaneously",
            strategy_type=StrategyType.CONTRASTIVE,
            templates=[
                "Complete this: {task}\nNow provide alternative solutions. Compare pros/cons of each.",
            ],
            best_for=["quality", "analysis", "comparison"],
            effectiveness=0.88,
        ),
        PromptStrategy(
            strategy_id="chunking",
            name="Chunking",
            description="Break into digestible parts",
            strategy_type=StrategyType.CHUNKING,
            templates=[
                "Break '{task}' into clear steps. Address each step systematically.",
            ],
            best_for=["large_tasks", "complex", "structured"],
            effectiveness=0.84,
        ),
        PromptStrategy(
            strategy_id="analogical",
            name="Analogical Reasoning",
            description="Use analogies to solve problems",
            strategy_type=StrategyType.TREE_OF_THOUGHT,
            templates=[
                "Task: {task}\nFind a similar problem you've solved. Apply that approach here.",
            ],
            best_for=["problem_solving", "learning", "transfer"],
            effectiveness=0.83,
        ),
    ]

    def __init__(self):
        self.strategies = {s.strategy_id: s for s in self.STRATEGIES}
        self.usage_stats: Dict[str, int] = {}

    def get_strategy(self, strategy_id: str) -> Optional[PromptStrategy]:
        """Get a strategy by ID."""
        return self.strategies.get(strategy_id)

    def get_strategies_for_task(self, task_type: str) -> List[PromptStrategy]:
        """Get best strategies for a task type."""
        results = []
        for strategy in self.STRATEGIES:
            if task_type in strategy.best_for:
                results.append(strategy)
        return sorted(results, key=lambda s: s.effectiveness, reverse=True)

    def get_all_strategies(self) -> List[PromptStrategy]:
        """Get all strategies."""
        return self.STRATEGIES

    def apply_strategy(self, strategy_id: str, task: str, **kwargs) -> str:
        """Apply a strategy to a task."""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return task

        template = strategy.templates[0]

        template_vars = {"task": task}
        template_vars.update(kwargs)

        try:
            return template.format(**template_vars)
        except KeyError:
            return task

    def suggest_strategy(self, task_description: str) -> List[PromptStrategy]:
        """Suggest best strategies for a task."""
        task_lower = task_description.lower()

        suggestions = []

        if any(w in task_lower for w in ["think", "reason", "solve", "analyze"]):
            suggestions.extend(self.get_strategies_for_task("reasoning"))

        if any(w in task_lower for w in ["write", "create", "draft"]):
            suggestions.extend(self.get_strategies_for_task("writing"))

        if any(w in task_lower for w in ["code", "program", "function"]):
            suggestions.extend(self.get_strategies_for_task("coding"))

        if any(w in task_lower for w in ["plan", "break", "decompose"]):
            suggestions.extend(self.get_strategies_for_task("planning"))

        if any(w in task_lower for w in ["complex", "difficult", "hard"]):
            suggestions.extend(self.get_strategies_for_task("complex_tasks"))

        seen = set()
        unique = []
        for s in suggestions:
            if s.strategy_id not in seen:
                seen.add(s.strategy_id)
                unique.append(s)

        return unique[:5]

    def record_usage(self, strategy_id: str):
        """Record strategy usage for learning."""
        self.usage_stats[strategy_id] = self.usage_stats.get(strategy_id, 0) + 1

    def get_popular_strategies(self) -> List[str]:
        """Get most used strategies."""
        return sorted(
            self.usage_stats.keys(), key=lambda x: self.usage_stats[x], reverse=True
        )


def create_prompt_strategies() -> PromptStrategies:
    """Factory function to create prompt strategies."""
    return PromptStrategies()
