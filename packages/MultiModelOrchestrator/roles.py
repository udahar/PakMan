# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Model Roles Configuration
Defines roles for multi-model collaboration
Custom written - inspired by FRANK_2_FEATURES.md
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ModelRole(Enum):
    """Predefined model roles."""

    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    RESEARCHER = "researcher"
    PLANNER = "planner"
    DEBUGGER = "debugger"


@dataclass
class RoleConfig:
    """Configuration for a model role."""

    role: str
    model: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


DEFAULT_ROLE_CONFIGS = {
    "architect": RoleConfig(
        role="architect",
        model="qwen2.5:7b",
        system_prompt="""You are a software architect. Your role is to:
- Analyze requirements and design clean, scalable systems
- Create clear specifications and schemas
- Make architectural decisions with reasoning
- Consider tradeoffs and best practices

Provide detailed, actionable designs.""",
    ),
    "coder": RoleConfig(
        role="coder",
        model="qwen2.5:7b",
        system_prompt="""You are a senior software developer. Your role is to:
- Write clean, idiomatic code
- Follow language-specific best practices
- Handle edge cases and errors
- Write self-documenting code

Provide working, production-ready code.""",
    ),
    "reviewer": RoleConfig(
        role="reviewer",
        model="llama3.2:3b",
        system_prompt="""You are a code reviewer. Your role is to:
- Find bugs, security issues, and code smells
- Suggest improvements and optimizations
- Verify best practices are followed
- Check for test coverage

Provide specific, actionable feedback.""",
    ),
    "tester": RoleConfig(
        role="tester",
        model="llama3.2:3b",
        system_prompt="""You are a test engineer. Your role is to:
- Write comprehensive unit tests
- Test edge cases and error conditions
- Follow testing best practices
- Ensure good coverage

Provide complete, working test code.""",
    ),
    "documenter": RoleConfig(
        role="documenter",
        model="llama3.2:3b",
        system_prompt="""You are a technical writer. Your role is to:
- Write clear, concise documentation
- Explain concepts for the target audience
- Include code examples
- Document APIs thoroughly

Provide accurate, helpful documentation.""",
    ),
    "researcher": RoleConfig(
        role="researcher",
        model="qwen2.5:7b",
        system_prompt="""You are a research assistant. Your role is to:
- Find relevant information and resources
- Compare options and alternatives
- Provide evidence-based recommendations
- Cite sources when possible

Provide thorough, accurate research.""",
    ),
    "planner": RoleConfig(
        role="planner",
        model="qwen2.5:7b",
        system_prompt="""You are a project planner. Your role is to:
- Break down tasks into manageable steps
- Estimate effort and time
- Identify dependencies and risks
- Create realistic timelines

Provide clear, actionable plans.""",
    ),
    "debugger": RoleConfig(
        role="debugger",
        model="qwen2.5:7b",
        system_prompt="""You are a debugging expert. Your role is to:
- Analyze error messages and stack traces
- Identify root causes
- Suggest fixes with explanations
- Prevent similar issues in the future

Provide clear diagnosis and solutions.""",
    ),
}


def get_default_roles() -> Dict[str, RoleConfig]:
    """Get default role configurations."""
    return DEFAULT_ROLE_CONFIGS.copy()


def get_role(role_name: str) -> Optional[RoleConfig]:
    """Get a specific role configuration."""
    return DEFAULT_ROLE_CONFIGS.get(role_name)


def get_roles_for_task(task_type: str) -> List[RoleConfig]:
    """Get recommended roles for a task type."""
    task_roles = {
        "build": ["architect", "coder", "reviewer", "tester"],
        "debug": ["debugger", "reviewer"],
        "document": ["documenter", "reviewer"],
        "research": ["researcher", "planner"],
        "plan": ["planner", "architect"],
        "review": ["reviewer", "tester"],
    }

    role_names = task_roles.get(task_type.lower(), ["coder"])
    return [DEFAULT_ROLE_CONFIGS[r] for r in role_names if r in DEFAULT_ROLE_CONFIGS]


def create_custom_role(
    role: str, model: str, system_prompt: str, temperature: float = 0.7
) -> RoleConfig:
    """Create a custom role configuration."""
    return RoleConfig(
        role=role, model=model, system_prompt=system_prompt, temperature=temperature
    )
