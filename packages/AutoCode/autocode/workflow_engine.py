"""
Workflow Engine - Manages Multi-Agent Workflows

Defines and executes predefined collaboration patterns between agents.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from autocode.models import WorkflowState, TaskResult
from autocode.message_bus import MessageBus


class BaseWorkflow(ABC):
    """Abstract base class for workflow definitions."""

    def __init__(self, workflow_id: str, task_description: str):
        self.workflow_id = workflow_id
        self.task_description = task_description
        self.state = WorkflowState(
            workflow_id=workflow_id,
            task_description=task_description,
            current_step=0,
            total_steps=self.get_total_steps(),
        )
        self.logger = logging.getLogger(f"Workflow.{self.__class__.__name__}")

    @abstractmethod
    def get_total_steps(self) -> int:
        """Return total number of steps in workflow."""
        pass

    @abstractmethod
    def execute(
        self,
        message_bus: MessageBus,
        context: Optional[dict] = None,
    ) -> list[TaskResult]:
        """
        Execute the workflow.

        Args:
            message_bus: Message bus for agent communication
            context: Optional context data

        Returns:
            List of task results from each step
        """
        pass

    def update_state(self, step: int, status: str = "running"):
        """Update workflow state."""
        self.state.current_step = step
        self.state.status = status
        if status in ("completed", "failed", "cancelled"):
            self.state.completed_at = datetime.now()


class LinearWorkflow(BaseWorkflow):
    """
    Simple linear workflow: Architect -> Coder -> Reviewer -> Tester

    Each agent completes their task sequentially, passing results to next.
    """

    def get_total_steps(self) -> int:
        return 4

    def execute(
        self,
        message_bus: MessageBus,
        context: Optional[dict] = None,
    ) -> list[TaskResult]:
        """Execute the linear workflow."""
        results = []
        context = context or {}

        steps = [
            ("architect", "design", "Design the solution"),
            ("coder", "implementation", "Implement the solution"),
            ("reviewer", "review", "Review the implementation"),
            ("tester", "tests", "Write tests"),
        ]

        for step_num, (agent, output_key, description) in enumerate(steps, 1):
            self.update_state(step_num, "running")
            self.logger.info(f"Step {step_num}/4: {description}")

            task = self._build_task(step_num, context)

            from_agent = "orchestrator"
            message = message_bus._build_message(
                from_agent=from_agent,
                to_agent=agent,
                content=task,
                thread_id=self.workflow_id,
                metadata=context,
            )

            responses = message_bus.send(message)

            if responses:
                context[output_key] = responses[0]
                results.append(
                    TaskResult(
                        task_id=f"{self.workflow_id}_step{step_num}",
                        agent_name=agent,
                        success=True,
                        output=responses[0],
                    )
                )
            else:
                results.append(
                    TaskResult(
                        task_id=f"{self.workflow_id}_step{step_num}",
                        agent_name=agent,
                        success=False,
                        output="",
                        errors=[f"No response from {agent}"],
                    )
                )

        self.update_state(4, "completed")
        return results

    def _build_task(self, step: int, context: dict) -> str:
        """Build task description for each step."""
        base_task = self.task_description

        if step == 1:
            return base_task
        elif step == 2:
            design = context.get("design", "")
            return f"{base_task}\n\nDesign:\n{design}"
        elif step == 3:
            impl = context.get("implementation", "")
            return f"{base_task}\n\nCode:\n{impl}"
        else:
            impl = context.get("implementation", "")
            review = context.get("review", "")
            return f"{base_task}\n\nCode:\n{impl}\n\nReview:\n{review}"


class IterativeWorkflow(BaseWorkflow):
    """
    Iterative workflow with review-feedback-fix cycles.

    Architect -> Coder -> Reviewer -> (if issues) Coder -> Reviewer -> Tester
    """

    def __init__(self, workflow_id: str, task_description: str, max_iterations: int = 2):
        self.max_iterations = max_iterations
        super().__init__(workflow_id, task_description)

    def get_total_steps(self) -> int:
        return 4 + (self.max_iterations * 2)

    def execute(
        self,
        message_bus: MessageBus,
        context: Optional[dict] = None,
    ) -> list[TaskResult]:
        """Execute with iterative review cycles."""
        results = []
        context = context or {}
        step = 0

        for iteration in range(self.max_iterations + 1):
            step += 1
            self.update_state(step, "running")
            self.logger.info(f"Iteration {iteration + 1}")

            if iteration == 0:
                result = self._run_architect_design(message_bus, context)
                results.append(result)
                context["design"] = result.output

            result = self._run_coder_impl(message_bus, context)
            results.append(result)
            context["implementation"] = result.output

            result = self._run_reviewer(message_bus, context)
            results.append(result)
            context["review"] = result.output

            if self._has_critical_issues(result.output):
                if iteration < self.max_iterations:
                    self.logger.info("Critical issues found, iterating...")
                    continue
                else:
                    self.logger.warning("Max iterations reached with issues")

            break

        step += 1
        self.update_state(step, "running")
        result = self._run_tester(message_bus, context)
        results.append(result)

        self.update_state(step, "completed")
        return results

    def _run_architect_design(self, bus: MessageBus, context: dict) -> TaskResult:
        """Run architect step."""
        msg = bus._build_message(
            from_agent="orchestrator",
            to_agent="architect",
            content=self.task_description,
            thread_id=self.workflow_id,
            metadata=context,
        )
        responses = bus.send(msg)
        return TaskResult(
            task_id=f"{self.workflow_id}_arch",
            agent_name="architect",
            success=bool(responses),
            output=responses[0] if responses else "",
        )

    def _run_coder_impl(self, bus: MessageBus, context: dict) -> TaskResult:
        """Run coder step."""
        msg = bus._build_message(
            from_agent="orchestrator",
            to_agent="coder",
            content=f"Task: {self.task_description}\nDesign: {context.get('design', '')}",
            thread_id=self.workflow_id,
            metadata=context,
        )
        responses = bus.send(msg)
        return TaskResult(
            task_id=f"{self.workflow_id}_code",
            agent_name="coder",
            success=bool(responses),
            output=responses[0] if responses else "",
        )

    def _run_reviewer(self, bus: MessageBus, context: dict) -> TaskResult:
        """Run reviewer step."""
        msg = bus._build_message(
            from_agent="orchestrator",
            to_agent="reviewer",
            content=f"Review: {self.task_description}",
            thread_id=self.workflow_id,
            metadata=context,
        )
        responses = bus.send(msg)
        return TaskResult(
            task_id=f"{self.workflow_id}_review",
            agent_name="reviewer",
            success=bool(responses),
            output=responses[0] if responses else "",
        )

    def _run_tester(self, bus: MessageBus, context: dict) -> TaskResult:
        """Run tester step."""
        msg = bus._build_message(
            from_agent="orchestrator",
            to_agent="tester",
            content=f"Test: {self.task_description}",
            thread_id=self.workflow_id,
            metadata=context,
        )
        responses = bus.send(msg)
        return TaskResult(
            task_id=f"{self.workflow_id}_test",
            agent_name="tester",
            success=bool(responses),
            output=responses[0] if responses else "",
        )

    def _has_critical_issues(self, review: str) -> bool:
        """Check if review found critical issues."""
        critical_keywords = ["critical", "security", "bug", "error", "fail"]
        review_lower = review.lower()
        return any(kw in review_lower for kw in critical_keywords)


class WorkflowEngine:
    """
    Manages workflow execution and registration.

    Provides:
    - Workflow registration
    - Execution tracking
    - Result aggregation
    """

    def __init__(self):
        self.logger = logging.getLogger("WorkflowEngine")
        self._workflows: dict[str, type[BaseWorkflow]] = {}
        self._active_workflows: dict[str, WorkflowState] = {}
        self._completed_workflows: list[WorkflowState] = []

        self._register_builtin_workflows()

    def _register_builtin_workflows(self):
        """Register built-in workflow types."""
        self.register("linear", LinearWorkflow)
        self.register("iterative", IterativeWorkflow)

    def register(self, name: str, workflow_class: type[BaseWorkflow]):
        """Register a workflow type."""
        self._workflows[name] = workflow_class
        self.logger.info(f"Workflow registered: {name}")

    def create_workflow(
        self,
        workflow_type: str,
        workflow_id: str,
        task_description: str,
        **kwargs,
    ) -> BaseWorkflow:
        """Create a workflow instance."""
        workflow_class = self._workflows.get(workflow_type)
        if not workflow_class:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        return workflow_class(workflow_id, task_description, **kwargs)

    def execute(
        self,
        workflow: BaseWorkflow,
        message_bus: MessageBus,
        context: Optional[dict] = None,
    ) -> list[TaskResult]:
        """Execute a workflow and track results."""
        self._active_workflows[workflow.workflow_id] = workflow.state

        start_time = time.time()
        self.logger.info(f"Starting workflow: {workflow.workflow_id}")

        try:
            results = workflow.execute(message_bus, context)

            workflow.state.status = "completed"
            workflow.state.results = [r.to_dict() for r in results]
            self.logger.info(f"Workflow completed: {workflow.workflow_id}")

        except Exception as e:
            workflow.state.status = "failed"
            self.logger.error(f"Workflow failed: {e}")
            raise

        finally:
            workflow.state.completed_at = datetime.now()
            del self._active_workflows[workflow.workflow_id]
            self._completed_workflows.append(workflow.state)

        return results

    def get_active_workflows(self) -> list[WorkflowState]:
        """Get all active workflows."""
        return list(self._active_workflows.values())

    def get_completed_workflows(self, limit: int = 10) -> list[WorkflowState]:
        """Get recently completed workflows."""
        return self._completed_workflows[-limit:]

    def get_stats(self) -> dict:
        """Get workflow engine statistics."""
        return {
            "registered_workflows": len(self._workflows),
            "active_workflows": len(self._active_workflows),
            "completed_workflows": len(self._completed_workflows),
        }
