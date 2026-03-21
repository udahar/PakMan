# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
PromptOS Integration
Connect prompt_library with PromptOS for strategic reasoning
"""

from typing import List, Dict, Optional, Any

from .index import PromptIndex
from .matcher import PromptMatcher
from .strategies import PromptStrategies, create_prompt_strategies


class PromptOSIntegration:
    """
    Integrate prompt library with PromptOS.

    This allows PromptOS to:
    - Use vetted prompts from prompts.chat
    - Use strategies for prompt optimization
    - Select optimal prompts for strategic reasoning
    - Learn from prompt performance
    """

    def __init__(self, index: PromptIndex):
        self.index = index
        self.matcher = None
        self.strategies = create_prompt_strategies()

    def _get_matcher(self) -> PromptMatcher:
        """Get or create matcher."""
        if self.matcher is None:
            from .matcher import create_prompt_matcher

            self.matcher = create_prompt_matcher(self.index)
        return self.matcher

    def select_prompt_for_strategy(self, goal: str, context: Dict[str, Any]) -> str:
        """
        Select the best prompt for strategic reasoning.

        Args:
            goal: The strategic goal
            context: Context information

        Returns:
            Selected prompt text
        """
        matcher = self._get_matcher()

        task = f"{goal} strategic reasoning planning"

        results = matcher.match(task)

        if results:
            return results[0].modified_prompt

        return "Think step by step about this goal and create a strategic plan."

    def get_reasoning_prompts(self) -> List[str]:
        """Get prompts useful for reasoning tasks."""
        reasoning_keywords = [
            "think step by step",
            "chain of thought",
            "strategic",
            "planning",
            "analyze",
        ]

        prompts = []
        for p in self.index.get_vetted_prompts():
            prompt_lower = p.prompt.lower()
            if any(kw in prompt_lower for kw in reasoning_keywords):
                prompts.append(p.prompt)

        return prompts[:20]

    def get_coding_prompts(self) -> List[str]:
        """Get prompts useful for coding tasks."""
        return [p.prompt for p in self.index.get_vetted_prompts() if p.for_devs][:20]

    def suggest_prompts_for_task(self, task_description: str) -> Dict[str, List[str]]:
        """
        Suggest multiple prompt categories for a task.

        Returns categorized prompts:
        - reasoning: For thinking/planning
        - coding: For implementation
        - review: For evaluation
        """
        matcher = self._get_matcher()

        suggestions = {"reasoning": [], "coding": [], "review": []}

        reasoning_results = matcher.match(f"{task_description} think plan strategy")
        for r in reasoning_results[:3]:
            suggestions["reasoning"].append(r.modified_prompt)

        coding_results = matcher.match(f"{task_description} code program develop")
        for r in coding_results[:3]:
            suggestions["coding"].append(r.modified_prompt)

        review_results = matcher.match(f"{task_description} review check analyze")
        for r in review_results[:3]:
            suggestions["review"].append(r.modified_prompt)

        return suggestions

    def suggest_strategies_for_task(
        self, task_description: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest best strategies for a task.

        Returns strategies with effectiveness scores.
        """
        strategies = self.strategies.suggest_strategy(task_description)

        return [
            {
                "strategy_id": s.strategy_id,
                "name": s.name,
                "description": s.description,
                "effectiveness": s.effectiveness,
                "best_for": s.best_for,
                "template": s.templates[0],
            }
            for s in strategies
        ]

    def apply_strategy_to_prompt(self, strategy_id: str, prompt: str, **kwargs) -> str:
        """Apply a strategy to a prompt."""
        return self.strategies.apply_strategy(strategy_id, prompt, **kwargs)

    def export_for_dspy(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        Export vetted prompts for DSPy training.

        Returns prompts formatted for PromptForge integration.
        """
        export = []

        for prompt in self.index.get_vetted_prompts()[:limit]:
            export.append(
                {
                    "act": prompt.act,
                    "prompt": prompt.prompt,
                    "for_devs": prompt.for_devs,
                    "tags": prompt.tags,
                }
            )

        return export

    def export_with_strategies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Export prompts WITH strategy combinations for DSPy training.

        Creates prompt + strategy combinations.
        """
        export = []

        prompts = self.index.get_vetted_prompts()[:limit]

        for prompt in prompts:
            task_type = prompt.tags[0] if prompt.tags else "general"
            strategies = self.strategies.get_strategies_for_task(task_type)

            for strategy in strategies[:3]:
                combined = self.strategies.apply_strategy(
                    strategy.strategy_id, prompt.prompt
                )

                export.append(
                    {
                        "act": prompt.act,
                        "base_prompt": prompt.prompt,
                        "strategy": strategy.strategy_id,
                        "combined_prompt": combined,
                        "effectiveness": strategy.effectiveness,
                        "for_devs": prompt.for_devs,
                        "tags": prompt.tags,
                    }
                )

        return export


def create_promptos_integration(index: PromptIndex) -> PromptOSIntegration:
    """Factory function to create PromptOS integration."""
    return PromptOSIntegration(index)
