"""Architect Agent - System Design Specialist"""

from autocode.agent_base import BaseAgent
from autocode.models import AgentConfig, AgentRole

ARCHITECT_PROMPT = """You are the Architect - a senior software architect with 20+ years of experience.

Your strengths:
- Thinking in systems, patterns, and tradeoffs
- Designing maintainable, scalable, and simple solutions
- Considering security, performance, and extensibility
- Breaking complex problems into manageable components

When analyzing a task, always address:
1. Overall architecture and component structure
2. Data flow and state management
3. API design and interfaces
4. Technology choices and tradeoffs
5. Potential bottlenecks and risks

Be thoughtful and deliberate. Ask: "What's the best way to structure this?"
"""


class ArchitectAgent(BaseAgent):
    """Agent responsible for system design and architecture."""

    def __init__(self, model: str = "qwen2.5:7b"):
        config = AgentConfig(
            name="Architect",
            role=AgentRole.ARCHITECT,
            system_prompt=ARCHITECT_PROMPT,
            model=model,
        )
        super().__init__(config)

    def process_task(self, task: str, context: dict = None) -> str:
        """Design an approach for the given task."""
        prompt = f"""Design a solution for the following task:

TASK: {task}

Provide:
1. High-level architecture overview
2. Component breakdown
3. Data flow description
4. Technology recommendations
5. Potential challenges and mitigations

Be specific and actionable."""

        return self.think(prompt)
