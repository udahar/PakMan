# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Skill Executor
Executes skills as LangChain tools - nanoclaw-style
Inspired by nanoclaw's skill system - custom Python implementation
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.tools import BaseTool, Tool

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None


@dataclass
class SkillExecution:
    """Result of skill execution."""

    skill_id: str
    input_data: str
    output: str
    success: bool
    execution_time: float
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class SkillExecutor:
    """
    Executes skills using LLMs.

    Similar to nanoclaw's skill execution but in Python.
    """

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://127.0.0.1:11434",
        temperature: float = 0.7,
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature

        self._llm = None
        self.skill_prompts: Dict[str, str] = {}
        self.execution_history: List[SkillExecution] = []

    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is None:
            if ChatOllama is None:
                raise ImportError("langchain_ollama not available")
            self._llm = ChatOllama(
                model=self.model, base_url=self.base_url, temperature=self.temperature
            )
        return self._llm

    def register_skill(self, skill_id: str, prompt_template: str):
        """Register a skill with its prompt template."""
        self.skill_prompts[skill_id] = prompt_template

    def execute_skill(
        self, skill_id: str, input_data: str, context: Optional[Dict[str, Any]] = None
    ) -> SkillExecution:
        """
        Execute a skill.

        Args:
            skill_id: The skill to execute
            input_data: Input for the skill
            context: Optional context

        Returns:
            SkillExecution result
        """
        import time

        start_time = time.time()

        if skill_id not in self.skill_prompts:
            return SkillExecution(
                skill_id=skill_id,
                input_data=input_data,
                output="",
                success=False,
                execution_time=time.time() - start_time,
                error=f"Skill '{skill_id}' not found",
            )

        prompt_template = self.skill_prompts[skill_id]
        prompt = prompt_template.format(
            task=input_data, context=context or {}, input=input_data
        )

        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            output = response.content if hasattr(response, "content") else str(response)

            execution = SkillExecution(
                skill_id=skill_id,
                input_data=input_data,
                output=output,
                success=True,
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            execution = SkillExecution(
                skill_id=skill_id,
                input_data=input_data,
                output="",
                success=False,
                execution_time=time.time() - start_time,
                error=str(e),
            )

        self.execution_history.append(execution)
        return execution

    def execute_chain(
        self, skills: List[tuple[str, str]], input_data: str
    ) -> List[SkillExecution]:
        """
        Execute a chain of skills.

        Args:
            skills: List of (skill_id, input_modifier) tuples
            input_data: Initial input

        Returns:
            List of execution results
        """
        results = []
        context = {"input": input_data}

        for skill_id, input_modifier in skills:
            if input_modifier == "previous":
                current_input = results[-1].output if results else input_data
            elif input_modifier == "original":
                current_input = input_data
            else:
                current_input = input_modifier

            execution = self.execute_skill(skill_id, current_input, context)
            results.append(execution)

            if not execution.success:
                break

            context[skill_id] = execution.output

        return results

    def get_available_skills(self) -> List[str]:
        """Get list of registered skills."""
        return list(self.skill_prompts.keys())

    def get_execution_history(
        self, skill_id: Optional[str] = None, limit: int = 10
    ) -> List[SkillExecution]:
        """Get execution history."""
        if skill_id:
            history = [e for e in self.execution_history if e.skill_id == skill_id]
        else:
            history = self.execution_history

        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0, "success_rate": 0, "avg_execution_time": 0}

        total = len(self.execution_history)
        successes = sum(1 for e in self.execution_history if e.success)
        avg_time = sum(e.execution_time for e in self.execution_history) / total

        return {
            "total_executions": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": successes / total,
            "avg_execution_time": avg_time,
            "skills_used": len(set(e.skill_id for e in self.execution_history)),
        }

    def to_langchain_tools(self) -> List[BaseTool]:
        """Convert registered skills to LangChain tools."""
        tools = []

        for skill_id, prompt in self.skill_prompts.items():

            def make_execute(sid):
                def execute(input_data: str) -> str:
                    result = self.execute_skill(sid, input_data)
                    if result.success:
                        return result.output
                    return f"Error: {result.error}"

                return execute

            tool = Tool(
                name=skill_id,
                description=f"Execute skill: {skill_id}",
                func=make_execute(skill_id),
            )
            tools.append(tool)

        return tools


def create_skill_executor(
    model: str = "qwen2.5:7b",
    base_url: str = "http://127.0.0.1:11434",
    temperature: float = 0.7,
) -> SkillExecutor:
    """Factory function to create skill executor."""
    return SkillExecutor(model, base_url, temperature)
