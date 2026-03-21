"""
Strategy Graph - Structured Reasoning Chains

Represents strategies as graphs instead of flat lists.
Enables:
- Sequential reasoning steps
- Branching logic
- Verification loops
- Tool call integration

Usage:
    from PromptForge import StrategyGraph
    
    # Create a reasoning graph
    graph = StrategyGraph()
    graph.add_step("planner", order=0)
    graph.add_step("decompose", order=1)
    graph.add_step("scratchpad", order=2, condition="if complex")
    graph.add_step("verify", order=3)
    
    # Execute graph
    result = graph.execute(llm_callable, prompt)
    
    # Convert to flat list for compatibility
    flat = graph.to_flat_list()
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum


class StepType(str, Enum):
    """Types of reasoning steps."""
    PLANNER = "planner"
    DECOMPOSE = "decompose"
    SCRATCHPAD = "scratchpad"
    VERIFY = "verify"
    FORMAT = "format"
    CONSTRAINTS = "constraints"
    TOOLS = "tools"
    FEW_SHOT = "few_shot"
    ROLE = "role"


class BranchCondition(str, Enum):
    """Conditions for branching."""
    ALWAYS = "always"
    IF_COMPLEX = "if_complex"
    IF_FAILED = "if_failed"
    IF_UNCERTAIN = "if_uncertain"
    CUSTOM = "custom"


@dataclass
class ReasoningStep:
    """A single step in a reasoning graph."""
    step_type: StepType
    order: int
    condition: BranchCondition = BranchCondition.ALWAYS
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "step_type": self.step_type.value,
            "order": self.order,
            "condition": self.condition.value,
            "params": self.params,
            "description": self.description,
        }


@dataclass
class StrategyGraph:
    """
    A graph of reasoning steps.
    
    Supports:
    - Sequential execution
    - Conditional branching
    - Loops (verification cycles)
    - Parallel branches
    """
    name: str
    steps: List[ReasoningStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(
        self,
        step_type: str,
        order: int,
        condition: str = "always",
        params: Optional[Dict] = None,
        description: str = "",
    ):
        """Add a step to the graph."""
        step = ReasoningStep(
            step_type=StepType(step_type),
            order=order,
            condition=BranchCondition(condition),
            params=params or {},
            description=description,
        )
        self.steps.append(step)
        # Sort by order
        self.steps.sort(key=lambda s: s.order)
    
    def to_flat_list(self) -> List[str]:
        """Convert graph to flat list (for compatibility)."""
        return [step.step_type.value for step in self.steps]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyGraph':
        """Create from dictionary."""
        graph = cls(name=data["name"], metadata=data.get("metadata", {}))
        
        for step_data in data.get("steps", []):
            step = ReasoningStep(
                step_type=StepType(step_data["step_type"]),
                order=step_data["order"],
                condition=BranchCondition(step_data["condition"]),
                params=step_data.get("params", {}),
                description=step_data.get("description", ""),
            )
            graph.steps.append(step)
        
        return graph
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyGraph':
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def execute(
        self,
        llm_callable: Callable,
        prompt: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Execute the reasoning graph.
        
        Args:
            llm_callable: LLM callable function
            prompt: Input prompt
            context: Execution context
        
        Returns:
            Execution result
        """
        if context is None:
            context = {}
        
        result = {
            "prompt": prompt,
            "steps_executed": [],
            "intermediate_results": {},
            "final_output": None,
        }
        
        current_context = {**context, "prompt": prompt}
        
        for step in self.steps:
            # Check condition
            if not self._check_condition(step, current_context):
                continue
            
            # Execute step
            step_result = self._execute_step(step, llm_callable, current_context)
            
            result["steps_executed"].append(step.step_type.value)
            result["intermediate_results"][step.step_type.value] = step_result
            
            # Update context
            current_context[step.step_type.value] = step_result
            
            # Check for early termination
            if step_result.get("terminate", False):
                break
        
        result["final_output"] = current_context.get("verify", current_context.get("scratchpad", ""))
        
        return result
    
    def _check_condition(
        self,
        step: ReasoningStep,
        context: Dict,
    ) -> bool:
        """Check if step condition is met."""
        condition = step.condition
        
        if condition == BranchCondition.ALWAYS:
            return True
        
        elif condition == BranchCondition.IF_COMPLEX:
            # Check if prompt is complex (simple heuristic)
            prompt = context.get("prompt", "")
            return len(prompt) > 200 or "complex" in prompt.lower()
        
        elif condition == BranchCondition.IF_FAILED:
            # Check if previous step failed
            return context.get("failed", False)
        
        elif condition == BranchCondition.IF_UNCERTAIN:
            # Check if confidence is low
            return context.get("confidence", 1.0) < 0.7
        
        return True
    
    def _execute_step(
        self,
        step: ReasoningStep,
        llm_callable: Callable,
        context: Dict,
    ) -> Dict[str, Any]:
        """Execute a single reasoning step."""
        step_type = step.step_type
        params = step.params
        
        # Build step prompt
        step_prompts = {
            StepType.ROLE: f"You are {params.get('role', 'an expert')}. {context['prompt']}",
            StepType.PLANNER: f"Create a plan to solve: {context['prompt']}",
            StepType.DECOMPOSE: f"Break this down into steps: {context['prompt']}",
            StepType.SCRATCHPAD: f"Think step by step: {context['prompt']}",
            StepType.VERIFY: f"Verify this solution: {context.get('scratchpad', context['prompt'])}",
            StepType.FORMAT: f"Format the output: {context.get('verify', context.get('scratchpad', context['prompt']))}",
            StepType.CONSTRAINTS: f"Solve with constraints {params.get('constraints', '')}: {context['prompt']}",
            StepType.TOOLS: f"Use tools to solve: {context['prompt']}",
            StepType.FEW_SHOT: f"Examples: {params.get('examples', '')}\n\nProblem: {context['prompt']}",
        }
        
        step_prompt = step_prompts.get(step_type, context['prompt'])
        
        # Execute LLM
        response = llm_callable(step_prompt)
        
        return {
            "prompt": step_prompt,
            "response": response,
            "step_type": step_type.value,
        }


class StrategyGraphBuilder:
    """Builder for creating common strategy graphs."""
    
    @staticmethod
    def simple_reasoning() -> StrategyGraph:
        """Create a simple reasoning graph."""
        graph = StrategyGraph(name="simple_reasoning")
        graph.add_step("scratchpad", order=0)
        graph.add_step("verify", order=1)
        return graph
    
    @staticmethod
    def complex_reasoning() -> StrategyGraph:
        """Create a complex reasoning graph."""
        graph = StrategyGraph(name="complex_reasoning")
        graph.add_step("role", order=0, params={"role": "an expert problem solver"})
        graph.add_step("decompose", order=1, condition="if_complex")
        graph.add_step("planner", order=2, condition="if_complex")
        graph.add_step("scratchpad", order=3)
        graph.add_step("verify", order=4)
        return graph
    
    @staticmethod
    def coding_task() -> StrategyGraph:
        """Create a coding task graph."""
        graph = StrategyGraph(name="coding_task")
        graph.add_step("planner", order=0)
        graph.add_step("scratchpad", order=1)
        graph.add_step("verify", order=2, params={"check": "tests"})
        graph.add_step("format", order=3, params={"format": "code"})
        return graph
    
    @staticmethod
    def debugging_task() -> StrategyGraph:
        """Create a debugging task graph."""
        graph = StrategyGraph(name="debugging_task")
        graph.add_step("decompose", order=0)
        graph.add_step("scratchpad", order=1)
        graph.add_step("verify", order=2, params={"check": "root_cause"})
        graph.add_step("format", order=3, params={"format": "solution"})
        return graph
    
    @staticmethod
    def math_task() -> StrategyGraph:
        """Create a math task graph."""
        graph = StrategyGraph(name="math_task")
        graph.add_step("decompose", order=0)
        graph.add_step("scratchpad", order=1, params={"method": "step_by_step"})
        graph.add_step("verify", order=2, params={"check": "calculation"})
        return graph
