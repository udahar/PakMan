"""Coder Agent - Implementation Specialist"""

from autocode.agent_base import BaseAgent
from autocode.models import AgentConfig, AgentRole

CODER_PROMPT = """You are the Coder - an expert programmer fluent in multiple languages.

Your strengths:
- Writing clean, efficient, and well-documented code
- Following best practices and design patterns
- Implementing features correctly and completely
- Adding appropriate error handling

When implementing, always:
1. Follow the architect's design
2. Use clear, descriptive names
3. Add comments for complex logic
4. Include error handling
5. Consider edge cases

Be practical and focused. Ask: "How do I implement this correctly?"
"""


class CoderAgent(BaseAgent):
    """Agent responsible for implementing code."""

    def __init__(self, model: str = "qwen2.5:7b"):
        config = AgentConfig(
            name="Coder",
            role=AgentRole.CODER,
            system_prompt=CODER_PROMPT,
            model=model,
        )
        super().__init__(config)

    def process_task(self, task: str, context: dict = None) -> str:
        """Implement the specified task."""
        design = context.get("design", "") if context else ""

        prompt = f"""Implement the following task:

TASK: {task}

DESIGN SPECIFICATIONS:
{design if design else "(No design provided - use your best judgment)"}

Provide:
1. Complete, working code implementation
2. Necessary imports and dependencies
3. Clear function/class structure
4. Error handling
5. Usage examples

Format code in markdown code blocks with language specification."""

        return self.think(prompt)
