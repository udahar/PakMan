"""
Agent definitions for the AutoCode system.

Each agent has a specialized role and personality.
"""

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


class ArchitectAgent(BaseAgent):
    """Agent responsible for system design and architecture."""

    def __init__(self):
        config = AgentConfig(
            name="Architect",
            role=AgentRole.ARCHITECT,
            system_prompt=ARCHITECT_PROMPT,
            model="qwen2.5:7b",
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


class CoderAgent(BaseAgent):
    """Agent responsible for implementing code."""

    def __init__(self):
        config = AgentConfig(
            name="Coder",
            role=AgentRole.CODER,
            system_prompt=CODER_PROMPT,
            model="qwen2.5:7b",
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


class ReviewerAgent(BaseAgent):
    """Agent responsible for code review."""

    def __init__(self):
        config = AgentConfig(
            name="Reviewer",
            role=AgentRole.REVIEWER,
            system_prompt=REVIEWER_PROMPT,
            model="qwen2.5:7b",
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


class TesterAgent(BaseAgent):
    """Agent responsible for writing tests."""

    def __init__(self):
        config = AgentConfig(
            name="Tester",
            role=AgentRole.TESTER,
            system_prompt=TESTER_PROMPT,
            model="qwen2.5:7b",
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
