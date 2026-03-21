# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Multi-Model Orchestrator
Coordinates multiple models in parallel for complex tasks
Custom written - inspired by FRANK_2_FEATURES.md
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from langchain_ollama import ChatOllama


@dataclass
class ModelResponse:
    """Response from a model."""

    role: str
    model_name: str
    content: str
    execution_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class OrchestrationResult:
    """Result from orchestrating multiple models."""

    task: str
    responses: List[ModelResponse]
    integrated_result: str
    total_time: float
    parallel: bool


class MultiModelOrchestrator:
    """
    Coordinates multiple Ollama models for parallel execution.

    Example:
        orchestrator = MultiModelOrchestrator()
        result = orchestrator.build_feature("Build a REST API")
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        temperature: float = 0.7,
        max_workers: int = 4,
        default_roles: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url
        self.temperature = temperature
        self.max_workers = max_workers

        self.default_roles = default_roles or {
            "architect": "qwen2.5:7b",
            "coder": "qwen2.5:7b",
            "reviewer": "llama3.2:3b",
            "tester": "llama3.2:3b",
        }

        self.llm_cache: Dict[str, ChatOllama] = {}

    def _get_llm(self, model_name: str) -> ChatOllama:
        """Get or create cached LLM instance."""
        if model_name not in self.llm_cache:
            self.llm_cache[model_name] = ChatOllama(
                model=model_name, base_url=self.base_url, temperature=self.temperature
            )
        return self.llm_cache[model_name]

    def execute_parallel(
        self, task: str, prompts: Dict[str, str]
    ) -> List[ModelResponse]:
        """Execute multiple prompts in parallel."""
        responses = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._call_model, role, prompt, task): role
                for role, prompt in prompts.items()
            }

            for future in as_completed(futures):
                role = futures[future]
                try:
                    response = future.result()
                    responses.append(response)
                except Exception as e:
                    responses.append(
                        ModelResponse(
                            role=role,
                            model_name=self.default_roles.get(role, "unknown"),
                            content="",
                            execution_time=0,
                            success=False,
                            error=str(e),
                        )
                    )

        return responses

    def _call_model(self, role: str, prompt_template: str, task: str) -> ModelResponse:
        """Call a model with a specific role."""
        start_time = time.time()
        model_name = self.default_roles.get(role, "unknown")

        prompt = prompt_template.format(task=task)

        try:
            llm = self._get_llm(model_name)
            response = llm.invoke(prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )

            return ModelResponse(
                role=role,
                model_name=model_name,
                content=content,
                execution_time=time.time() - start_time,
                success=True,
            )
        except Exception as e:
            return ModelResponse(
                role=role,
                model_name=model_name,
                content="",
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
            )

    def build_feature(self, spec: str) -> OrchestrationResult:
        """
        Build a feature using multi-model collaboration.

        Steps:
        1. Architect designs the schema
        2. Coder implements the code
        3. Reviewer reviews the code
        4. Tester creates tests
        """
        start_time = time.time()

        prompts = {
            "architect": """You are a software architect. Design a clear specification for this requirement.
            
Requirement: {task}

Provide a detailed schema/design.""",
            "coder": """You are a senior coder. Implement the code based on this specification.

Task: {task}

Write clean, working code.""",
            "reviewer": """You are a code reviewer. Review this code for quality, bugs, and improvements.

Task: {task}

Provide specific feedback.""",
            "tester": """You are a test engineer. Write unit tests for this code.

Task: {task}

Write comprehensive tests.""",
        }

        responses = self.execute_parallel(spec, prompts)

        integrated = self._integrate_responses(responses)

        return OrchestrationResult(
            task=spec,
            responses=responses,
            integrated_result=integrated,
            total_time=time.time() - start_time,
            parallel=True,
        )

    def _integrate_responses(self, responses: List[ModelResponse]) -> str:
        """Integrate responses from multiple models."""
        if not responses:
            return "No responses to integrate."

        sections = ["# Multi-Model Collaboration Results\n"]

        for r in responses:
            status = "✓" if r.success else "✗"
            sections.append(f"## {status} {r.role.title()} ({r.model_name})")
            sections.append(f"Time: {r.execution_time:.2f}s")

            if r.success:
                sections.append(f"\n{r.content[:500]}")
            else:
                sections.append(f"\nError: {r.error}")

            sections.append("\n---\n")

        return "\n".join(sections)

    def execute_chain(
        self, task: str, chain: List[tuple[str, str]]
    ) -> List[ModelResponse]:
        """
        Execute models in sequence (chain pattern).

        Args:
            task: Initial task
            chain: List of (role, prompt_template) tuples

        Returns:
            List of responses
        """
        responses = []
        context = task

        for role, prompt_template in chain:
            response = self._call_model(role, prompt_template, context)
            responses.append(response)

            if response.success:
                context = f"Previous context:\n{response.content}\n\nTask: {task}"
            else:
                break

        return responses

    def health_check(self) -> Dict[str, bool]:
        """Check which models are available."""
        health = {}
        for role, model in self.default_roles.items():
            try:
                llm = self._get_llm(model)
                llm.invoke("ping")
                health[role] = True
            except Exception:
                health[role] = False
        return health


def create_orchestrator(
    base_url: str = "http://127.0.0.1:11434",
    temperature: float = 0.7,
    models: Optional[Dict[str, str]] = None,
) -> MultiModelOrchestrator:
    """Factory function to create orchestrator."""
    return MultiModelOrchestrator(
        base_url=base_url, temperature=temperature, default_roles=models
    )
