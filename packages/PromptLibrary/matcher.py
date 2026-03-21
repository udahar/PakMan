# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Matcher
Find the best prompt for a given task
"""

import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from .index import PromptIndex, IndexedPrompt
from .parser import Prompt


@dataclass
class MatchResult:
    """Result of matching a task to a prompt."""

    prompt: IndexedPrompt
    match_reason: str
    confidence: float
    modified_prompt: str


class PromptMatcher:
    """
    Match user tasks to the best prompts from the library.

    Integrates with PromptOS for strategic reasoning.
    """

    TASK_KEYWORDS = {
        "code": ["code", "program", "function", "script", "developer", "coding"],
        "write": ["write", "create", "generate", "make", "compose"],
        "explain": ["explain", "describe", "what is", "how does", "understand"],
        "translate": ["translate", "convert", "to english", "to spanish", "language"],
        "review": ["review", "check", "analyze", "assess", "evaluate"],
        "improve": ["improve", "optimize", "enhance", "better", "refactor"],
        "teach": ["teach", "learn", "tutorial", "explain", "guide"],
        "roleplay": ["act as", "play", "simulate", "pretend", "interview"],
        "data": ["data", "spreadsheet", "excel", "table", "csv", "analysis"],
        "system": ["terminal", "linux", "command", "bash", "shell", "console"],
    }

    def __init__(self, index: PromptIndex):
        self.index = index

    def match(self, task: str, require_vetted: bool = True) -> List[MatchResult]:
        """
        Match a task to the best prompts.

        Args:
            task: The user's task description
            require_vetted: Only return vetted prompts

        Returns:
            List of match results with modified prompts
        """
        task_lower = task.lower()

        tags = self._extract_tags(task_lower)

        devs_only = any(
            kw in task_lower for kw in ["code", "program", "function", "developer"]
        )

        results = self.index.search(
            query=task, limit=10, tags=tags if tags else None, devs_only=devs_only
        )

        if require_vetted:
            results = [r for r in results if r.vetted]

        matches = []
        for r in results:
            modified = self._modify_prompt(r.prompt, task)
            reason = self._explain_match(r, task)

            matches.append(
                MatchResult(
                    prompt=r,
                    match_reason=reason,
                    confidence=r.score,
                    modified_prompt=modified,
                )
            )

        return matches[:5]

    def _extract_tags(self, task: str) -> List[str]:
        """Extract relevant tags from task."""
        tags = []
        for tag, keywords in self.TASK_KEYWORDS.items():
            if any(kw in task for kw in keywords):
                tags.append(tag)
        return tags

    def _explain_match(self, result: IndexedPrompt, task: str) -> str:
        """Explain why this prompt was selected."""
        reasons = []

        if result.for_devs:
            reasons.append("Developer-focused")

        if result.tags:
            reasons.append(f"Tags: {', '.join(result.tags[:3])}")

        reasons.append(f"Match score: {result.score:.2f}")

        return " | ".join(reasons)

    def _modify_prompt(self, prompt: str, task: str) -> str:
        """Modify prompt template with task-specific details."""
        modified = prompt

        variable_pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"

        def replace_var(match):
            var_name = match.group(1)
            default = match.group(2)

            task_lower = task.lower()

            if "language" in var_name.lower():
                if "spanish" in task_lower:
                    return "Spanish"
                if "french" in task_lower:
                    return "French"
                if "german" in task_lower:
                    return "German"
                return default or "English"

            if "position" in var_name.lower():
                return default or "Software Developer"

            if "topic" in var_name.lower():
                return default or task[:50]

            return default or f"[{var_name}]"

        modified = re.sub(variable_pattern, replace_var, modified)

        return modified

    def get_prompt_for_task(self, task: str) -> Optional[str]:
        """Get the best prompt for a task."""
        matches = self.match(task)

        if matches:
            return matches[0].modified_prompt

        return None

    def suggest_improvements(self, prompt: str, task: str) -> List[str]:
        """Suggest improvements to a prompt."""
        suggestions = []

        if "${" not in prompt:
            suggestions.append("Add variables using ${variable} format for flexibility")

        if len(prompt) < 50:
            suggestions.append("Prompt is very short, consider adding more context")

        if not any(kw in prompt.lower() for kw in ["i want", "please", "act as"]):
            suggestions.append(
                "Add role definition like 'Act as...' or 'I want you to...'"
            )

        if prompt.count("\n") < 2 and len(prompt) > 200:
            suggestions.append("Consider breaking into multiple paragraphs for clarity")

        return suggestions


def create_prompt_matcher(index: PromptIndex) -> PromptMatcher:
    """Factory function to create prompt matcher."""
    return PromptMatcher(index)
