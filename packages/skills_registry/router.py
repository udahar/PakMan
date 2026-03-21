# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Skill Router - Routes tasks to appropriate skills
Custom written based on FRANK_SKILLS_TAXONOMY.md patterns
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class SkillMatch:
    """A matched skill with confidence score."""

    skill_id: str
    skill_name: str
    confidence: float
    reason: str


class SkillRouter:
    """Routes user tasks to appropriate skills."""

    KEYWORD_PATTERNS = {
        "code_generation": [
            "write code",
            "generate code",
            "create function",
            "implement",
            "build",
        ],
        "code_explanation": ["explain", "what does", "how does", "what is"],
        "code_review": ["review", "check code", "audit", "assess"],
        "code_optimization": ["optimize", "improve", "faster", "performance"],
        "code_refactoring": ["refactor", "restructure", "reorganize"],
        "bug_detection": ["find bug", "debug", "error", "fix"],
        "test_generation": ["test", "unit test", "write tests", "coverage"],
        "file_read": ["read file", "show file", "cat", "view"],
        "file_write": ["write file", "create file", "save to"],
        "search_files": ["search", "find file", "locate"],
        "web_search": ["search the web", "google", "lookup"],
        "data_analysis": ["analyze", "analysis", "stats", "pattern"],
        "text_summarization": ["summarize", "summary", "tldr"],
        "task_decomposition": ["break down", "subtasks", "plan", "roadmap"],
        "brainstorm_ideas": ["brainstorm", "ideas", "generate options"],
        "fact_checking": ["fact check", "verify", "is it true"],
    }

    EXTENSION_TO_SKILL = {
        ".py": "code_generation_python",
        ".js": "code_generation_javascript",
        ".ts": "code_generation_javascript",
        ".jsx": "code_generation_javascript",
        ".tsx": "code_generation_javascript",
        ".sql": "code_generation_sql",
        ".sh": "code_generation_bash",
        ".bash": "code_generation_bash",
        ".ps1": "code_generation_powershell",
        ".go": "code_generation_go",
        ".rs": "code_generation_rust",
        ".java": "code_generation_java",
        ".cpp": "code_generation_cpp",
        ".c": "code_generation_cpp",
        ".html": "code_generation_html_css",
        ".css": "code_generation_html_css",
    }

    def __init__(self, registry=None):
        self.registry = registry

    def route(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> List[SkillMatch]:
        """
        Route a task to appropriate skills.

        Args:
            task: The user's task description
            context: Optional context (file types, etc.)

        Returns:
            List of skill matches sorted by confidence
        """
        task_lower = task.lower()
        matches = []

        # Check file extensions in context
        if context and "file_path" in context:
            ext = self._get_extension(context["file_path"])
            if ext in self.EXTENSION_TO_SKILL:
                skill_id = self.EXTENSION_TO_SKILL[ext]
                matches.append(
                    SkillMatch(
                        skill_id=skill_id,
                        skill_name=self._get_skill_name(skill_id),
                        confidence=0.9,
                        reason=f"Detected {ext} file",
                    )
                )

        # Keyword-based matching
        for skill_id, keywords in self.KEYWORD_PATTERNS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    confidence = self._calculate_confidence(keyword, task_lower)
                    matches.append(
                        SkillMatch(
                            skill_id=skill_id,
                            skill_name=self._get_skill_name(skill_id),
                            confidence=confidence,
                            reason=f"Matched keyword: {keyword}",
                        )
                    )

        # Add default skills for general coding tasks
        if not matches:
            matches.append(
                SkillMatch(
                    skill_id="code_generation_python",
                    skill_name="Generate Python code",
                    confidence=0.5,
                    reason="Default coding skill",
                )
            )

        # Sort by confidence and deduplicate
        matches = self._deduplicate_and_sort(matches)
        return matches[:5]  # Top 5 matches

    def _get_extension(self, path: str) -> str:
        """Get file extension from path."""
        if "." in path:
            return "." + path.rsplit(".", 1)[-1]
        return ""

    def _get_skill_name(self, skill_id: str) -> str:
        """Get human-readable skill name."""
        if self.registry:
            skill = self.registry.get_skill(skill_id)
            if skill:
                return skill.name
        # Fallback: convert skill_id to name
        return skill_id.replace("_", " ").title()

    def _calculate_confidence(self, keyword: str, task: str) -> float:
        """Calculate confidence score based on keyword match quality."""
        base = 0.6
        # Exact match gets higher score
        if keyword in task:
            base += 0.2
        # Longer keywords are more specific
        if len(keyword) > 5:
            base += 0.1
        return min(base, 1.0)

    def _deduplicate_and_sort(self, matches: List[SkillMatch]) -> List[SkillMatch]:
        """Remove duplicates and sort by confidence."""
        seen = set()
        unique = []
        for m in matches:
            if m.skill_id not in seen:
                seen.add(m.skill_id)
                unique.append(m)
        return sorted(unique, key=lambda x: x.confidence, reverse=True)

    def get_skill_prompt(self, skill_id: str, task: str) -> str:
        """Get the DSPy-optimized prompt for a skill."""
        if self.registry:
            skill = self.registry.get_skill(skill_id)
            if skill:
                return skill.dspy_prompt.format(task=task)
        return f"Complete this task: {task}"

    def explain_routing(self, matches: List[SkillMatch]) -> str:
        """Explain why skills were selected."""
        if not matches:
            return "No matching skills found."

        lines = ["Selected skills:"]
        for i, m in enumerate(matches):
            lines.append(f"  {i + 1}. {m.skill_name} (confidence: {m.confidence:.0%})")
            lines.append(f"     Reason: {m.reason}")
        return "\n".join(lines)


def create_skill_router(registry=None) -> SkillRouter:
    """Factory function to create skill router."""
    return SkillRouter(registry)
