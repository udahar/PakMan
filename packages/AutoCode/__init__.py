"""AutoCode - AI-powered code generation assistant."""

# Re-export the subpackage's public API for convenience
from .autocode import *  # noqa: F403,F401

__version__ = "1.0.0"
__author__ = "Richard"
__email__ = "richard@example.com"

# Expose the subpackage as a submodule for those who prefer explicit access
from . import autocode  # noqa: F401

__all__ = [
    # From autocode.__all__
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
    # Submodule
    "autocode",
]
