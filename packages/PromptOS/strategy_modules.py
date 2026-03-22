"""
Strategy Modules - Micro-Instructions for Prompt Shaping

Each module is a composable block that can be enabled/disabled.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class StrategyModule:
    """A single prompt strategy module."""
    name: str
    description: str
    template: str
    position: str  # "prefix", "infix", "suffix"
    compatible_tasks: List[str]
    incompatible_with: List[str]
    cost_tokens: int
    models_improved: List[str]
    models_degraded: List[str]
    weight: float = 1.0  # Adjustable by learning


# Module definitions
STRATEGY_MODULES = {
    "role": StrategyModule(
        name="ROLE",
        description="Stabilizes model, reduces hallucinations",
        template="""You are {role_description}.

Follow the structured process below.
Only produce the requested output format.
""",
        position="prefix",
        compatible_tasks=["coding", "debugging", "reasoning", "writing", "planning", "review", "tools"],
        incompatible_with=[],
        cost_tokens=50,
        models_improved=["qwen2.5:3b", "qwen2.5:7b", "llama3.2:3b", "gemma2:2b"],
        models_degraded=[],
    ),
    
    "decompose": StrategyModule(
        name="DECOMPOSE",
        description="Break problem into smaller steps before solving",
        template="""
[MODULE:DECOMPOSE]
Break this problem into smaller, manageable steps.
List the steps required to solve it.
Do not solve yet - just identify the steps.
""",
        position="infix",
        compatible_tasks=["coding", "debugging", "reasoning", "planning"],
        incompatible_with=["planner"],
        cost_tokens=80,
        models_improved=["qwen2.5:3b", "gemma2:2b", "llama3.2:3b"],
        models_degraded=["gpt-4o", "claude-opus"],
    ),
    
    "scratchpad": StrategyModule(
        name="SCRATCHPAD",
        description="Hidden reasoning space for step-by-step thinking",
        template="""
[MODULE:SCRATCHPAD]
Use the scratchpad below to work through the problem step by step.
You may use logical reasoning, calculations, or intermediate notes.
Do not produce the final answer in the scratchpad.

<SCRATCHPAD>
[Your internal reasoning goes here]
</SCRATCHPAD>
""",
        position="infix",
        compatible_tasks=["reasoning", "coding", "debugging", "planning"],
        incompatible_with=[],
        cost_tokens=150,
        models_improved=["qwen2.5:3b", "qwen2.5:7b", "gemma2:2b", "llama3.2:3b"],
        models_degraded=[],
    ),
    
    "tools": StrategyModule(
        name="TOOLS",
        description="Tool planning & simulation",
        template="""
[MODULE:TOOLS]
Decide which tools would help solve this task.

Available tools:
{available_tools}

Explain how each tool would be used.
Do not execute tools yet - just plan.
""",
        position="infix",
        compatible_tasks=["tools", "coding", "debugging"],
        incompatible_with=[],
        cost_tokens=100,
        models_improved=["qwen2.5:7b", "llama3.2:3b"],
        models_degraded=["gpt-4o"],
    ),
    
    "verify": StrategyModule(
        name="VERIFY",
        description="Self-correction & reflection",
        template="""
[MODULE:VERIFY]
Review your solution before finalizing.

Check for:
- Logical errors
- Incorrect calculations
- Missing requirements
- Edge cases

If you find problems, correct them now.
""",
        position="infix",
        compatible_tasks=["coding", "debugging", "reasoning", "review"],
        incompatible_with=[],
        cost_tokens=120,
        models_improved=["qwen2.5:3b", "qwen2.5:7b", "gemma2:2b"],
        models_degraded=[],
    ),
    
    "format": StrategyModule(
        name="FORMAT",
        description="Strict output formatting",
        template="""
[MODULE:FORMAT]
Return ONLY the final answer in the requested format.
No reasoning, no explanation, no scratchpad in the final output.
""",
        position="suffix",
        compatible_tasks=["coding", "writing", "tools", "reasoning", "extraction"],
        incompatible_with=["hidden_scratchpad"],
        cost_tokens=40,
        models_improved=["gpt-4o", "claude-sonnet"],
        models_degraded=["qwen2.5:3b"],
    ),
    
    "planner": StrategyModule(
        name="PLANNER",
        description="Plan-then-solve pattern (for coding)",
        template="""
[MODULE:PLANNER]
First, write a plan for the solution.

Plan:
<List the steps you will take>

Then, implement the solution following the plan.

Solution:
<Your implementation>
""",
        position="infix",
        compatible_tasks=["coding", "debugging"],
        incompatible_with=["decompose"],
        cost_tokens=100,
        models_improved=["codex", "claude-sonnet", "qwen2.5:7b"],
        models_degraded=["gemma2:2b"],
    ),
    
    "hidden_scratchpad": StrategyModule(
        name="HIDDEN_SCRATCHPAD",
        description="Model thinks in scratchpad but final answer hides it",
        template="""
Think through this step by step in a scratchpad, then provide only the final answer.

<SCRATCHPAD>
[Internal reasoning - will be hidden from final output]
</SCRATCHPAD>

<FINAL>
[Final answer only - no reasoning shown]
</FINAL>
""",
        position="infix",
        compatible_tasks=["reasoning", "coding", "debugging"],
        incompatible_with=["format"],
        cost_tokens=150,
        models_improved=["qwen2.5:7b", "llama3.2:3b"],
        models_degraded=[],
    ),
    
    "few_shot": StrategyModule(
        name="FEW_SHOT",
        description="Include examples of desired output",
        template="""
[MODULE:FEW_SHOT]
Here are examples of the expected output:

{examples}

Now solve the task following the pattern above.
""",
        position="infix",
        compatible_tasks=["coding", "writing", "extraction", "classification"],
        incompatible_with=[],
        cost_tokens=200,
        models_improved=["qwen2.5:3b", "qwen2.5:7b", "llama3.2:3b"],
        models_degraded=[],
    ),
    
    "constraints": StrategyModule(
        name="CONSTRAINTS",
        description="Explicit constraints and requirements",
        template="""
[MODULE:CONSTRAINTS]
Constraints:
{constraints}

Ensure your solution satisfies all constraints.
""",
        position="infix",
        compatible_tasks=["coding", "reasoning", "planning"],
        incompatible_with=[],
        cost_tokens=80,
        models_improved=["qwen2.5:7b", "llama3.2:3b"],
        models_degraded=[],
    ),
}

# Role descriptions per task type
ROLE_DESCRIPTIONS = {
    "coding": "a senior software engineer with 15+ years of experience. You write clean, efficient, production-ready code following best practices.",
    "debugging": "an expert debugger and software reliability engineer. You systematically diagnose and fix issues with methodical precision.",
    "reasoning": "a logical reasoning expert and critical thinker. You approach problems systematically, considering all angles.",
    "writing": "a professional writer and editor. You craft clear, engaging, well-structured content.",
    "tools": "a technical operator with access to various tools. You select the right tool for each task and use it correctly.",
    "chat": "a friendly, helpful conversational assistant. You're warm, personable, and engaging while remaining informative.",
    "planning": "a strategic planner and project architect. You break down complex goals into actionable steps.",
    "review": "a code reviewer and quality assurance expert. You provide constructive, specific feedback.",
}

# Few-shot examples per task
FEW_SHOT_EXAMPLES = {
    "coding": [
        {
            "input": "Write a function to reverse a string",
            "output": """def reverse_string(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return s[::-1]"""
        }
    ],
    "debugging": [
        {
            "input": "Fix IndexError in list access",
            "output": """# Check list length before indexing
if my_list:
    item = my_list[0]
else:
    item = None  # Handle empty case"""
        }
    ],
    "chat": [
        {
            "input": "Hey, how's it going?",
            "output": "Hey! Doing great, thanks for asking! 😊 How about you?"
        }
    ],
}
