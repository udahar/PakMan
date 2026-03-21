"""
Zoo Keeper - Multi-Agent Orchestrator

Main entry point for coordinating agent collaboration.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from autocode.message_bus import MessageBus, AgentMessage
from autocode.workflow_engine import WorkflowEngine, LinearWorkflow
from autocode.models import MessagePriority, TaskResult
from autocode.agents.architect import ArchitectAgent
from autocode.agents.coder import CoderAgent
from autocode.agents.reviewer import ReviewerAgent
from autocode.agents.tester import TesterAgent


@dataclass
class ZooConfig:
    """Configuration for the Zoo Keeper."""

    model: str = "qwen2.5:7b"
    base_url: str = "http://127.0.0.1:11434"
    enable_logging: bool = True
    log_level: str = "INFO"
    workflow_type: str = "linear"


class ZooKeeper:
    """
    Orchestrates multi-agent collaboration.

    Responsibilities:
    - Initialize and manage agents
    - Configure message bus
    - Execute workflows
    - Aggregate results
    """

    def __init__(self, config: Optional[ZooConfig] = None):
        self.config = config or ZooConfig()
        self.logger = self._setup_logging()

        self.message_bus = MessageBus()
        self.workflow_engine = WorkflowEngine()

        self.agents = {}
        self._initialize_agents()
        self._register_agents_with_bus()

        self.logger.info("ZooKeeper initialized")

    def _setup_logging(self) -> logging.Logger:
        """Configure logging."""
        logger = logging.getLogger("ZooKeeper")
        logger.setLevel(getattr(logging, self.config.log_level))

        if not logger.handlers and self.config.enable_logging:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_agents(self):
        """Create agent instances."""
        model = self.config.model

        self.agents = {
            "architect": ArchitectAgent(model=model),
            "coder": CoderAgent(model=model),
            "reviewer": ReviewerAgent(model=model),
            "tester": TesterAgent(model=model),
        }

        self.logger.info(f"Initialized {len(self.agents)} agents")

    def _register_agents_with_bus(self):
        """Register agents with the message bus."""

        def make_callback(agent_name: str):
            def callback(message: AgentMessage) -> str:
                agent = self.agents.get(agent_name)
                if not agent:
                    return f"Agent {agent_name} not found"
                return agent.receive_message(message)

            return callback

        for name, agent in self.agents.items():
            self.message_bus.register_agent(name, make_callback(name))

        self.logger.info("Agents registered with message bus")

    def collaborate(self, task: str, workflow_type: Optional[str] = None) -> dict:
        """
        Run a collaborative task through all agents.

        Args:
            task: The task description
            workflow_type: Optional workflow type override

        Returns:
            Dictionary with all agent outputs
        """
        workflow_type = workflow_type or self.config.workflow_type
        workflow_id = str(uuid.uuid4())[:8]

        self.logger.info(f"Starting collaboration: {task[:50]}...")
        self.logger.info(f"Workflow: {workflow_type}, ID: {workflow_id}")

        workflow = self.workflow_engine.create_workflow(
            workflow_type=workflow_type,
            workflow_id=workflow_id,
            task_description=task,
        )

        results = self.workflow_engine.execute(
            workflow=workflow,
            message_bus=self.message_bus,
        )

        return self._aggregate_results(results)

    def _aggregate_results(self, results: list[TaskResult]) -> dict:
        """Aggregate task results into a structured response."""
        output = {
            "design": "",
            "implementation": "",
            "review": "",
            "tests": "",
            "summary": {},
        }

        for result in results:
            if result.agent_name == "architect":
                output["design"] = result.output
            elif result.agent_name == "coder":
                output["implementation"] = result.output
            elif result.agent_name == "reviewer":
                output["review"] = result.output
            elif result.agent_name == "tester":
                output["tests"] = result.output

            output["summary"][result.agent_name] = {
                "success": result.success,
                "duration": result.duration_seconds,
                "errors": result.errors,
            }

        output["summary"]["total_agents"] = len(results)
        output["summary"]["successful"] = sum(
            1 for r in results if r.success
        )

        return output

    def run_once(self, task: str) -> dict:
        """
        Simple collaboration with default workflow.

        Convenience method for quick tasks.
        """
        return self.collaborate(task)

    def get_agent_stats(self) -> dict:
        """Get statistics for all agents."""
        return {
            name: {
                "role": agent.role,
                "tasks_processed": agent.task_count,
            }
            for name, agent in self.agents.items()
        }

    def get_message_stats(self) -> dict:
        """Get message bus statistics."""
        return self.message_bus.get_stats()

    def get_workflow_stats(self) -> dict:
        """Get workflow engine statistics."""
        return self.workflow_engine.get_stats()

    def get_full_stats(self) -> dict:
        """Get comprehensive system statistics."""
        return {
            "agents": self.get_agent_stats(),
            "messages": self.get_message_stats(),
            "workflows": self.get_workflow_stats(),
        }


def create_zoo_keeper(**kwargs) -> ZooKeeper:
    """Factory function to create ZooKeeper with custom config."""
    config = ZooConfig(**kwargs)
    return ZooKeeper(config)


if __name__ == "__main__":
    zoo = ZooKeeper()
    result = zoo.collaborate("Build a REST API for todo list")

    print("\n" + "=" * 60)
    print("COLLABORATION RESULTS")
    print("=" * 60)

    print("\n=== DESIGN ===")
    print(result["design"][:500] + "..." if len(result["design"]) > 500 else result["design"])

    print("\n=== IMPLEMENTATION ===")
    print(result["implementation"][:500] + "..." if len(result["implementation"]) > 500 else result["implementation"])

    print("\n=== REVIEW ===")
    print(result["review"][:500] + "..." if len(result["review"]) > 500 else result["review"])

    print("\n=== TESTS ===")
    print(result["tests"][:500] + "..." if len(result["tests"]) > 500 else result["tests"])

    print("\n=== SUMMARY ===")
    for agent, stats in result["summary"].items():
        if isinstance(stats, dict):
            print(f"  {agent}: {'OK' if stats.get('success') else 'FAILED'}")
