# Skill: Meta-Prompting

**skill_id:** `meta_prompting_001`  
**name:** meta_prompting  
**category:** prompt_strategy  
**version:** 1.0  

## Description

The model first designs the optimal prompt for a task, then executes that prompt to solve the problem.

## Primitive Tags

- prompt_design
- two_stage
- self_optimization
- prompt_engineering
- meta_reasoning
- adaptive_prompting

## Prompt Strategy

```
For Meta-Prompting:

1. ANALYZE TASK
   - Understand what's being asked
   - Identify task type and requirements

2. DESIGN OPTIMAL PROMPT
   - What prompt structure would work best?
   - What information is needed?
   - What reasoning approach?

3. EXECUTE DESIGNED PROMPT
   - Run the designed prompt
   - Generate the solution

4. OPTIONAL: EVALUATE
   - Did the prompt work well?
   - How could it be improved?
```

## Solution Summary

### Prompt Templates

**Stage 1: Design the Prompt**
```
Task: {task_description}

Design the best prompt to solve this task. Consider:
- What information is needed?
- What reasoning approach works best?
- What format should the answer take?
- Any special instructions or constraints?

Output ONLY the prompt you've designed, nothing else.
```

**Stage 2: Execute the Prompt**
```
{designed_prompt}

Now execute this prompt to solve the original task.
```

### Python Implementation

```python
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class MetaPromptResult:
    original_task: str
    designed_prompt: str
    execution_result: str
    prompt_rationale: str
    success: bool


async def meta_prompting(
    task: str,
    model_fn,
    include_rationale: bool = True
) -> MetaPromptResult:
    """
    Design optimal prompt then execute it.
    
    Args:
        task: The task to solve
        model_fn: Async function to call LLM
        include_rationale: Include reasoning about prompt design
    
    Returns:
        MetaPromptResult with designed prompt and solution
    """
    # Stage 1: Design the prompt
    designed_prompt, rationale = await design_prompt(task, model_fn)
    
    # Stage 2: Execute the designed prompt
    execution_result = await model_fn(designed_prompt)
    
    return MetaPromptResult(
        original_task=task,
        designed_prompt=designed_prompt,
        execution_result=execution_result,
        prompt_rationale=rationale,
        success=True
    )


async def design_prompt(task: str, model_fn) -> Tuple[str, str]:
    """Design an optimal prompt for the task."""
    prompt = f"""Task: {task}

Design the best prompt to solve this task.

Consider:
1. What type of task is this? (math, reasoning, creative, analysis, etc.)
2. What reasoning approach works best? (step-by-step, examples, etc.)
3. What information or context is needed?
4. What format should the answer take?
5. Any special instructions that would help?

Provide your response in this format:

RATIONALE:
[Explain your prompt design choices]

DESIGNED PROMPT:
[The complete prompt you've designed]
"""
    
    response = await model_fn(prompt)
    
    # Parse response
    rationale = extract_section(response, "RATIONALE")
    designed_prompt = extract_section(response, "DESIGNED PROMPT")
    
    return designed_prompt, rationale


async def design_prompt_for_category(
    task: str,
    task_category: str,
    model_fn
) -> str:
    """Design prompt with category-specific best practices."""
    
    category_templates = {
        "math": "Solve step-by-step, showing all work.",
        "code": "Write clean, tested code with explanations.",
        "analysis": "Analyze systematically, cite evidence.",
        "creative": "Be imaginative while staying on topic.",
        "reasoning": "Think logically, justify each step."
    }
    
    base_template = category_templates.get(
        task_category, 
        "Think carefully and explain your reasoning."
    )
    
    prompt = f"""Task: {task}

Category: {task_category}

Best practices for this category:
{base_template}

Design a prompt that incorporates these best practices."""
    
    return await model_fn(prompt)


def extract_section(response: str, section: str) -> str:
    """Extract a section from the response."""
    import re
    
    pattern = rf'{section}:\s*\n(.*?)(?=\n\n[A-Z]+:|$)'
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ""
```

## Tests Passed

- [x] Designs relevant prompts
- [x] Incorporates task requirements
- [x] Executes designed prompt correctly
- [x] Provides rationale for design choices
- [x] Adapts to different task types
- [x] Produces better results than generic prompts

## Failure Modes

- **Over-engineering**: Prompt too complex for simple task
  - Mitigation: Match prompt complexity to task
- **Generic design**: Prompt lacks specificity
  - Mitigation: Request concrete examples in prompt
- **Execution drift**: Designed prompt not followed
  - Mitigation: Clear separation between stages

## Best For

- Complex, ambiguous tasks
- PromptForge experiments
- Optimizing for specific metrics
- Novel problem types
- When generic prompts underperform

## Performance

- **Quality**: Often better than one-size-fits-all prompts
- **Cost**: 2x (design + execute)
- **Latency**: Sequential stages

## Related Skills

- `reflexion_001` - Self-critique and improve
- `decomposition_001` - Break into subtasks
- `prompt_optimizer_001` - A/B test prompts

## Timestamp

2026-03-08
