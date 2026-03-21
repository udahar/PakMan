"""
Base Agent class for all AutoCode agents.

Provides common functionality for LLM interaction, logging, and state management.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

try:
    from langchain_ollama import ChatOllama
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from autocode.models import AgentConfig, AgentMessage, TaskResult


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the AutoCode system.

    Subclasses must implement:
    - process_task(): Core logic for the agent's role
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.llm = self._init_llm()
        self._message_history: list[AgentMessage] = []
        self._task_count = 0

    def _setup_logging(self) -> logging.Logger:
        """Configure agent-specific logger."""
        logger = logging.getLogger(f"Agent.{self.config.name}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_llm(self) -> Optional["ChatOllama"]:
        """Initialize the LLM connection."""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("langchain_ollama not available")
            return None

        try:
            return ChatOllama(
                model=self.config.model,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            return None

    def think(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and get a response.

        Args:
            prompt: The input prompt for the LLM

        Returns:
            The LLM's response text
        """
        if not self.llm:
            return "LLM not available - cannot process"

        try:
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt},
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            self.logger.error(f"LLM invocation failed: {e}")
            return f"Error: {str(e)}"

    def receive_message(self, message: AgentMessage) -> str:
        """
        Process an incoming message from another agent.

        Args:
            message: The incoming message

        Returns:
            Response to the message
        """
        self._message_history.append(message)
        self.logger.info(f"Received message from {message.from_agent}")

        response = self.process_task(message.content, message.metadata)

        return response

    @abstractmethod
    def process_task(self, task: str, context: Optional[dict] = None) -> str:
        """
        Process a task specific to this agent's role.

        Args:
            task: The task description
            context: Additional context from previous agents

        Returns:
            The agent's response/output
        """
        pass

    def execute(self, task_id: str, task: str, context: Optional[dict] = None) -> TaskResult:
        """
        Execute a task and return structured results.

        Args:
            task_id: Unique identifier for the task
            task: The task description
            context: Additional context

        Returns:
            TaskResult with output and metadata
        """
        start_time = time.time()
        self._task_count += 1

        try:
            output = self.process_task(task, context)

            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                success=True,
                output=output,
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                success=False,
                output="",
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    def get_message_history(self, limit: int = 50) -> list[AgentMessage]:
        """Get recent message history."""
        return self._message_history[-limit:]

    def clear_history(self):
        """Clear message history."""
        self._message_history.clear()
        self.logger.debug("Message history cleared")

    @property
    def task_count(self) -> int:
        """Get total tasks processed."""
        return self._task_count

    @property
    def role(self) -> str:
        """Get the agent's role."""
        return self.config.role.value

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.config.name
