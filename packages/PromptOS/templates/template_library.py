"""
PromptOS Template Library

Pre-built prompt templates for specific failure modes and capabilities.
Each template targets a specific weakness or discipline problem.

Usage:
    from PromptOS.templates import TemplateLibrary
    
    templates = TemplateLibrary()
    
    # Get template for failure mode
    template = templates.get("strict_json")
    prompt = template.apply(task="Extract data from text")
    
    # Get template for capability
    template = templates.get("scratchpad_reasoning")
    prompt = template.apply(task="Solve this math problem")
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """A reusable prompt template."""
    name: str
    description: str
    template: str
    variables: List[str]
    failure_modes_addressed: List[str]
    best_for_models: List[str]
    best_for_tasks: List[str]
    
    def apply(self, **kwargs) -> str:
        """Apply template with variables."""
        result = self.template
        
        for var in self.variables:
            value = kwargs.get(var, f"[{var}]")
            result = result.replace(f"{{{var}}}", str(value))
        
        return result


class TemplateLibrary:
    """
    Library of prompt templates for specific failure modes.
    
    Templates organized by:
    - Discipline problems (JSON, format, constraints)
    - Reasoning problems (logic, math, planning)
    - Tool problems (tool use, simulation)
    - Communication problems (verbosity, explanations)
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates."""
        
        # ========== DISCIPLINE TEMPLATES ==========
        
        self.templates["strict_json"] = PromptTemplate(
            name="strict_json",
            description="Enforces strict JSON output with no extra text",
            template="""You must output ONLY valid JSON. No explanations, no markdown, no extra text.

Requirements:
- Output must be valid JSON
- No markdown code blocks
- No explanations before or after
- All required fields must be present

Task: {task}

Output format:
{output_format}

Remember: ONLY JSON, nothing else.""",
            variables=["task", "output_format"],
            failure_modes_addressed=["wrong_format", "verbosity", "ignoring_constraints"],
            best_for_models=["qwen2.5:7b", "llama3.2:3b", "codex"],
            best_for_tasks=["extraction", "formatting", "structured_output"],
        )
        
        self.templates["strict_schema"] = PromptTemplate(
            name="strict_schema",
            description="Enforces strict schema compliance",
            template="""You must follow this schema EXACTLY. Do not add fields. Do not omit fields.

Schema:
{schema}

Task: {task}

Before outputting, verify:
1. All required fields present
2. No extra fields added
3. Types match schema
4. No explanations included

Output ONLY the JSON that matches the schema.""",
            variables=["schema", "task"],
            failure_modes_addressed=["wrong_format", "schema_violation", "hallucination"],
            best_for_models=["qwen2.5:7b", "claude-sonnet", "gpt-4o"],
            best_for_tasks=["structured_output", "api_response", "data_extraction"],
        )
        
        self.templates["no_explanation"] = PromptTemplate(
            name="no_explanation",
            description="Suppresses unwanted explanations",
            template="""Answer the question directly. Do NOT explain your reasoning. Do NOT add context.

Task: {task}

Output ONLY the answer. Nothing else.""",
            variables=["task"],
            failure_modes_addressed=["verbosity", "over_explaining", "ignoring_constraints"],
            best_for_models=["qwen2.5:7b", "llama3.2:3b"],
            best_for_tasks=["simple_qa", "extraction", "classification"],
        )
        
        # ========== REASONING TEMPLATES ==========
        
        self.templates["scratchpad_reasoning"] = PromptTemplate(
            name="scratchpad_reasoning",
            description="Forces step-by-step reasoning in scratchpad",
            template="""Think through this step by step in a scratchpad before answering.

<SCRATCHPAD>
1. What is being asked?
2. What information do I have?
3. What are the steps to solve this?
4. Work through each step
5. Verify the answer
</SCRATCHPAD>

Task: {task}

After the scratchpad, provide your final answer.""",
            variables=["task"],
            failure_modes_addressed=["logic_error", "reasoning_failure", "jumping_to_conclusions"],
            best_for_models=["qwen2.5:3b", "qwen2.5:7b", "llama3.2:3b"],
            best_for_tasks=["reasoning", "math", "logic", "complex_qa"],
        )
        
        self.templates["decompose_first"] = PromptTemplate(
            name="decompose_first",
            description="Forces problem decomposition before solving",
            template="""Before solving, break this problem into smaller steps.

Task: {task}

Step 1: Decompose the problem
List all sub-problems or steps needed:
1.
2.
3.

Step 2: Solve each sub-problem in order

Step 3: Combine into final answer""",
            variables=["task"],
            failure_modes_addressed=["incomplete", "missing_steps", "complexity_overwhelm"],
            best_for_models=["qwen2.5:7b", "llama3.2:3b"],
            best_for_tasks=["planning", "complex_reasoning", "multi_step"],
        )
        
        self.templates["verify_answer"] = PromptTemplate(
            name="verify_answer",
            description="Forces answer verification before finalizing",
            template="""Solve this problem, then verify your answer before finalizing.

Task: {task}

Solution:
[Your solution here]

Verification:
- Check for calculation errors
- Check for logic errors
- Verify all constraints are satisfied
- Consider edge cases
- Does the answer make sense?

Final Answer:
[Verified answer]""",
            variables=["task"],
            failure_modes_addressed=["logic_error", "calculation_error", "missing_verification"],
            best_for_models=["qwen2.5:7b", "claude-sonnet"],
            best_for_tasks=["math", "reasoning", "verification_needed"],
        )
        
        # ========== PLANNING TEMPLATES ==========
        
        self.templates["plan_then_solve"] = PromptTemplate(
            name="plan_then_solve",
            description="Plan-then-solve pattern for coding",
            template="""First, write a detailed plan. Then implement following the plan.

Task: {task}

## Plan

1. Understand requirements
2. Design approach
3. Identify edge cases
4. Implementation steps
5. Testing strategy

## Solution

[Implement following the plan]""",
            variables=["task"],
            failure_modes_addressed=["incomplete", "missing_edge_cases", "poor_planning"],
            best_for_models=["codex", "claude-sonnet", "qwen2.5:7b"],
            best_for_tasks=["coding", "debugging", "implementation"],
        )
        
        self.templates["tool_simulation"] = PromptTemplate(
            name="tool_simulation",
            description="Simulates tool usage before execution",
            template="""You have access to these tools:

{tools}

Task: {task}

Before executing, plan your tool usage:

1. Which tools are needed?
2. What order should they be called?
3. What are the expected outputs?
4. How will you handle errors?

Tool Plan:
[Your plan here]

Now execute the plan.""",
            variables=["task", "tools"],
            failure_modes_addressed=["tool_misuse", "poor_planning", "error_handling"],
            best_for_models=["qwen2.5:7b", "llama3.2:3b"],
            best_for_tasks=["tools", "automation", "multi_step"],
        )
        
        # ========== CODE TEMPLATES ==========
        
        self.templates["code_with_tests"] = PromptTemplate(
            name="code_with_tests",
            description="Forces code with unit tests",
            template="""Write code to solve this task, including comprehensive unit tests.

Task: {task}

Requirements:
- Clean, readable code
- Error handling
- Edge case handling
- Unit tests covering:
  - Normal cases
  - Edge cases
  - Error cases

Code:
[Your code here]

Tests:
[Your tests here]""",
            variables=["task"],
            failure_modes_addressed=["incomplete", "missing_tests", "no_error_handling"],
            best_for_models=["codex", "claude-sonnet", "qwen2.5:7b"],
            best_for_tasks=["coding", "implementation"],
        )
        
        self.templates["code_review"] = PromptTemplate(
            name="code_review",
            description="Structured code review template",
            template="""Review this code systematically.

Code:
{code}

Review Checklist:
1. Correctness - Does it work?
2. Completeness - Edge cases handled?
3. Security - Any vulnerabilities?
4. Performance - Any bottlenecks?
5. Readability - Is it clear?
6. Testing - Are there tests?

Review:
[Your review here]

Suggestions:
[Your suggestions here]""",
            variables=["code"],
            failure_modes_addressed=["incomplete_review", "missing_security", "missing_edge_cases"],
            best_for_models=["claude-sonnet", "gpt-4o", "qwen2.5:7b"],
            best_for_tasks=["review", "audit", "code_quality"],
        )
        
        # ========== TWO-MODE TEMPLATES ==========
        
        self.templates["normal_mode"] = PromptTemplate(
            name="normal_mode",
            description="Standard prompt without scaffolding",
            template="""{task}""",
            variables=["task"],
            failure_modes_addressed=[],
            best_for_models=["gpt-4o", "claude-opus"],
            best_for_tasks=["all"],
        )
        
        self.templates["structured_mode"] = PromptTemplate(
            name="structured_mode",
            description="Full scaffolding with reasoning structure",
            template="""Task: {task}

Please work through this systematically:

1. **Understanding**: What is being asked?

2. **Approach**: How will you solve this?

3. **Execution**: Work through the solution step by step.

4. **Verification**: Check your answer for errors.

5. **Final Answer**: Provide your final answer.""",
            variables=["task"],
            failure_modes_addressed=["reasoning_failure", "incomplete", "lack_of_structure"],
            best_for_models=["qwen2.5:7b", "llama3.2:3b", "codex"],
            best_for_tasks=["reasoning", "coding", "complex_tasks"],
        )
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def get_for_failure_mode(self, failure_mode: str) -> List[PromptTemplate]:
        """Get all templates that address a failure mode."""
        return [
            t for t in self.templates.values()
            if failure_mode in t.failure_modes_addressed
        ]
    
    def get_for_task(self, task_type: str) -> List[PromptTemplate]:
        """Get all templates suitable for a task type."""
        return [
            t for t in self.templates.values()
            if task_type in t.best_for_tasks or "all" in t.best_for_tasks
        ]
    
    def get_for_model(self, model: str) -> List[PromptTemplate]:
        """Get all templates suitable for a model."""
        return [
            t for t in self.templates.values()
            if model in t.best_for_models or any(f in model for f in t.best_for_models)
        ]
    
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all templates with metadata."""
        return {
            name: {
                "description": t.description,
                "variables": t.variables,
                "failure_modes": t.failure_modes_addressed,
                "best_for_models": t.best_for_models,
                "best_for_tasks": t.best_for_tasks,
            }
            for name, t in self.templates.items()
        }


# Convenience function
def get_template(name: str) -> Optional[PromptTemplate]:
    """Get a template by name."""
    library = TemplateLibrary()
    return library.get(name)
