"""
Prompt Mutation Strategies
"""

import random
from typing import List


class PromptMutator:
    """Mutate prompts to improve performance."""

    def __init__(self):
        self.mutation_strategies = [
            self._add_examples,
            self._clarify_instructions,
            self._add_constraints,
            self._simplify,
            self._add_context,
        ]

    def mutate(self, prompt: str, score: float) -> str:
        """Mutate prompt based on score."""
        if score > 0.8:
            return prompt

        strategy = random.choice(self.mutation_strategies)
        return strategy(prompt)

    def _add_examples(self, prompt: str) -> str:
        """Add examples to prompt."""
        return prompt + "\n\nExample: " + "[Add relevant example here]"

    def _clarify_instructions(self, prompt: str) -> str:
        """Clarify instructions."""
        return "Clearly: " + prompt

    def _add_constraints(self, prompt: str) -> str:
        """Add constraints."""
        return prompt + "\n\nConstraints: Be concise and accurate."

    def _simplify(self, prompt: str) -> str:
        """Simplify prompt."""
        return "Simplified: " + prompt[: len(prompt) // 2]

    def _add_context(self, prompt: str) -> str:
        """Add context."""
        return f"Context: You are an expert AI assistant.\n\n{prompt}"
