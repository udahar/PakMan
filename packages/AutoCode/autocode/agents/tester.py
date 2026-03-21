"""Tester Agent - Quality Assurance Specialist"""

from autocode.agent_base import BaseAgent
from autocode.models import AgentConfig, AgentRole

TESTER_PROMPT = """You are the Tester - a dedicated QA engineer with a keen eye for edge cases.

Your strengths:
- Writing comprehensive test suites
- Finding boundary conditions and failure modes
- Thinking like an end user
- Breaking things to find bugs

When testing, always consider:
1. Happy path tests
2. Edge cases and boundary conditions
3. Error handling and failure modes
4. Integration tests
5. Performance tests

Be skeptical and thorough. Ask: "What could break?"
"""


class TesterAgent(BaseAgent):
    """Agent responsible for writing tests."""

    def __init__(self, model: str = "qwen2.5:7b"):
        config = AgentConfig(
            name="Tester",
            role=AgentRole.TESTER,
            system_prompt=TESTER_PROMPT,
            model=model,
        )
        super().__init__(config)

    def process_task(self, task: str, context: dict = None) -> str:
        """Write tests for the provided code."""
        code = context.get("implementation", "") if context else ""
        review = context.get("review", "") if context else ""

        prompt = f"""Write comprehensive tests for the following:

TASK: {task}

CODE:
{code if code else "(No code provided)"}

REVIEW NOTES:
{review if review else "(No review notes)"}

Provide:
1. Unit tests for individual functions/classes
2. Integration tests for component interactions
3. Edge case tests
4. Error handling tests
5. Test setup and teardown code

Include test descriptions explaining what each test verifies.
Format in markdown code blocks with language specification."""

        return self.think(prompt)
