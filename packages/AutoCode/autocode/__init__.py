"""
AutoCode - Multi-Agent Code Generation Framework

A collaborative AI system where specialized agents work together
to design, implement, review, and test software.
"""

from autocode.models import (
    AgentConfig,
    AgentMessage,
    TaskResult,
    MessagePriority,
)
from autocode.agent_base import BaseAgent
from autocode.agents.architect import ArchitectAgent
from autocode.agents.coder import CoderAgent
from autocode.agents.reviewer import ReviewerAgent
from autocode.agents.tester import TesterAgent
from autocode.message_bus import MessageBus
from autocode.workflow_engine import WorkflowEngine
from autocode.zoo_keeper import ZooKeeper, ZooConfig

__version__ = "1.0.0"
__all__ = [
    "AgentConfig",
    "AgentMessage",
    "TaskResult",
    "MessagePriority",
    "BaseAgent",
    "ArchitectAgent",
    "CoderAgent",
    "ReviewerAgent",
    "TesterAgent",
    "MessageBus",
    "WorkflowEngine",
    "ZooKeeper",
    "ZooConfig",
]
