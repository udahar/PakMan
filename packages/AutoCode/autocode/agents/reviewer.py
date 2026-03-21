"""Reviewer Agent - Code Quality Specialist"""

from autocode.agent_base import BaseAgent
from autocode.models import AgentConfig, AgentRole

REVIEWER_PROMPT = """You are the Reviewer - a meticulous and experienced code reviewer.

Your strengths:
- Finding bugs, security issues, and code smells
- Identifying performance problems
- Suggesting improvements and refactoring
- Ensuring code quality and consistency

When reviewing, always check:
1. Logic errors and edge cases
2. Security vulnerabilities
3. Performance issues
4. Code style and consistency
5. Missing error handling
6. Potential bugs

Be thorough but constructive. Ask: "What could go wrong here?"
"""


class ReviewerAgent(BaseAgent):
    """Agent responsible for code review."""

    def __init__(self, model: str = "qwen2.5:7b"):
        config = AgentConfig(
            name="Reviewer",
            role=AgentRole.REVIEWER,
            system_prompt=REVIEWER_PROMPT,
            model=model,
        )
        super().__init__(config)

    def process_task(self, task: str, context: dict = None) -> str:
        """Review the provided code."""
        code = context.get("implementation", "") if context else ""

        prompt = f"""Review the following code implementation:

TASK: {task}

CODE TO REVIEW:
{code if code else "(No code provided)"}

Provide:
1. Summary of what the code does
2. Bugs or logic errors found
3. Security concerns
4. Performance issues
5. Code quality observations
6. Specific improvement suggestions

Be thorough and specific. Reference line numbers or code sections when possible."""

        return self.think(prompt)
