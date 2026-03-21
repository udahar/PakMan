"""
Core data models for the AutoCode system.

All shared dataclasses, enums, and types used across modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessagePriority(Enum):
    """Priority levels for inter-agent messages."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentRole(Enum):
    """Defined agent roles in the system."""

    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    name: str
    role: AgentRole
    system_prompt: str
    model: str = "qwen2.5:7b"
    base_url: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass
class AgentMessage:
    """Message passed between agents via the message bus."""

    from_agent: str
    to_agent: str
    content: str
    thread_id: str
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert message to dictionary for serialization."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "thread_id": self.thread_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "attachments": self.attachments,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        """Create message from dictionary."""
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            thread_id=data["thread_id"],
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(),
            attachments=data.get("attachments", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskResult:
    """Result of a completed task or agent operation."""

    task_id: str
    agent_name: str
    success: bool
    output: str
    artifacts: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "success": self.success,
            "output": self.output,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowState:
    """Tracks the state of a running workflow."""

    workflow_id: str
    task_description: str
    current_step: int
    total_steps: int
    status: str = "running"
    results: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.status in ("completed", "failed", "cancelled")

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
