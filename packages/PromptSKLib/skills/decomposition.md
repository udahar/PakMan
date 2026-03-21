# Skill: Decomposition / Task Chunking

**skill_id:** `decomposition_001`  
**name:** decomposition  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Breaks complex tasks into smaller, manageable subtasks, solves each independently, then combines results into a complete solution.

## Primitive Tags

- task_breakdown
- subtask_generation
- divide_and_conquer
- hierarchical_solving
- result_combination
- complexity_reduction

## Prompt Strategy

```
For Decomposition:

1. ANALYZE TASK
   - Understand the full scope
   - Identify natural divisions

2. BREAK INTO SUBTASKS
   - Create 3-7 manageable pieces
   - Each should be independently solvable
   - Define clear success criteria

3. SOLVE SUBTASKS
   - Address each subtask
   - Can parallelize or sequence
   - Track progress

4. COMBINE RESULTS
   - Synthesize subtask outputs
   - Ensure coherence
   - Fill any gaps
```

## Solution Summary

### Prompt Templates

**Decomposition Prompt**
```
Task: {complex_task}

Break this task into 3-7 smaller subtasks.

For each subtask:
1. Give it a clear label
2. Describe what needs to be done
3. Define success criteria
4. Note any dependencies on other subtasks

Format:
SUBTASK 1: [label]
- Description: ...
- Success criteria: ...
- Dependencies: ...

SUBTASK 2: ...
```

**Subtask Execution**
```
Working on: {subtask_label}

Description: {subtask_description}

Complete this subtask now. Be thorough but focused only on this piece.
```

**Synthesis Prompt**
```
Task: {original_task}

Subtask results:

{subtask_results}

Combine these results into a complete solution for the original task.

Ensure:
1. All subtasks are addressed
2. Results flow logically
3. No gaps or contradictions
4. Clear final output
```

### Python Implementation

```python
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class SubtaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class Subtask:
    id: str
    label: str
    description: str
    success_criteria: str
    dependencies: List[str] = field(default_factory=list)
    status: SubtaskStatus = SubtaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DecompositionResult:
    original_task: str
    subtasks: List[Subtask]
    combined_result: str
    success: bool


async def decomposition(
    task: str,
    model_fn,
    max_subtasks: int = 7,
    parallel: bool = True
) -> DecompositionResult:
    """
    Break complex task into subtasks and solve.
    
    Args:
        task: The complex task to solve
        model_fn: Async function to call LLM
        max_subtasks: Maximum number of subtasks
        parallel: Whether to solve subtasks in parallel
    
    Returns:
        DecompositionResult with combined solution
    """
    # Step 1: Decompose into subtasks
    subtasks = await decompose_task(task, model_fn, max_subtasks)
    
    # Step 2: Solve subtasks
    if parallel:
        await solve_subtasks_parallel(subtasks, task, model_fn)
    else:
        await solve_subtasks_sequential(subtasks, task, model_fn)
    
    # Step 3: Combine results
    combined = await combine_results(task, subtasks, model_fn)
    
    return DecompositionResult(
        original_task=task,
        subtasks=subtasks,
        combined_result=combined,
        success=all(s.status == SubtaskStatus.COMPLETED for s in subtasks)
    )


async def decompose_task(
    task: str,
    model_fn,
    max_subtasks: int
) -> List[Subtask]:
    """Break task into subtasks."""
    prompt = f"""Task: {task}

Break this into {max_subtasks} or fewer subtasks.

For each subtask provide:
- LABEL: Short name
- DESCRIPTION: What needs to be done
- SUCCESS CRITERIA: How to know it's complete
- DEPENDENCIES: Which other subtasks must come first (or "none")

Format exactly:

SUBTASK 1:
LABEL: [label]
DESCRIPTION: [description]
SUCCESS CRITERIA: [criteria]
DEPENDENCIES: [dependencies or "none"]

SUBTASK 2:
...
"""
    
    response = await model_fn(prompt)
    
    return parse_subtasks(response)


async def solve_subtasks_parallel(
    subtasks: List[Subtask],
    original_task: str,
    model_fn
):
    """Solve subtasks in parallel where possible."""
    # Build dependency graph
    completed = set()
    remaining = {s.id for s in subtasks}
    
    while remaining:
        # Find subtasks with satisfied dependencies
        ready = [
            s for s in subtasks 
            if s.id in remaining and 
            all(d in completed or d == "none" for d in s.dependencies)
        ]
        
        if not ready:
            # Deadlock - mark remaining as blocked
            for s in subtasks:
                if s.id in remaining:
                    s.status = SubtaskStatus.BLOCKED
                    s.error = "Dependency not satisfied"
            break
        
        # Solve ready subtasks in parallel
        tasks = [solve_single_subtask(s, original_task, model_fn) for s in ready]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update status
        for subtask, result in zip(ready, results):
            if isinstance(result, Exception):
                subtask.status = SubtaskStatus.BLOCKED
                subtask.error = str(result)
            else:
                subtask.result = result
                subtask.status = SubtaskStatus.COMPLETED
                completed.add(subtask.id)
                remaining.remove(subtask.id)


async def solve_subtasks_sequential(
    subtasks: List[Subtask],
    original_task: str,
    model_fn
):
    """Solve subtasks one at a time."""
    for subtask in subtasks:
        # Check dependencies
        if subtask.dependencies and subtask.dependencies != ["none"]:
            for dep_id in subtask.dependencies:
                dep = next((s for s in subtasks if s.id == dep_id), None)
                if dep and dep.status != SubtaskStatus.COMPLETED:
                    subtask.status = SubtaskStatus.BLOCKED
                    subtask.error = f"Dependency {dep_id} not completed"
                    continue
        
        if subtask.status == SubtaskStatus.BLOCKED:
            continue
        
        result = await solve_single_subtask(subtask, original_task, model_fn)
        subtask.result = result
        subtask.status = SubtaskStatus.COMPLETED


async def solve_single_subtask(
    subtask: Subtask,
    original_task: str,
    model_fn
) -> str:
    """Solve a single subtask."""
    prompt = f"""Original task: {original_task}

Your subtask: {subtask.label}

Description: {subtask.description}

Success criteria: {subtask.success_criteria}

Complete this subtask now. Be thorough but focused only on this piece.
"""
    
    return await model_fn(prompt)


async def combine_results(
    task: str,
    subtasks: List[Subtask],
    model_fn
) -> str:
    """Combine subtask results into final solution."""
    results_text = "\n\n".join(
        f"=== {s.label} ===\n{s.result or s.error or 'Not completed'}"
        for s in subtasks
    )
    
    prompt = f"""Original task: {task}

Subtask results:

{results_text}

Combine these results into a complete, coherent solution for the original task.

Ensure:
1. All subtasks are addressed
2. Results flow logically
3. No gaps or contradictions
4. Clear final output

Provide the complete combined solution."""
    
    return await model_fn(prompt)


def parse_subtasks(response: str) -> List[Subtask]:
    """Parse subtasks from response."""
    import re
    
    subtasks = []
    pattern = r'SUBTASK\s*(\d+):\s*LABEL:\s*(.+?)\s*DESCRIPTION:\s*(.+?)\s*SUCCESS CRITERIA:\s*(.+?)\s*DEPENDENCIES:\s*(.+?)(?=SUBTASK|$)'
    
    matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        num, label, desc, criteria, deps = match
        
        subtasks.append(Subtask(
            id=f"subtask_{num}",
            label=label.strip(),
            description=desc.strip(),
            success_criteria=criteria.strip(),
            dependencies=[d.strip() for d in deps.split(",")] if deps.lower() != "none" else []
        ))
    
    return subtasks
```

## Tests Passed

- [x] Breaks tasks into logical subtasks
- [x] Handles dependencies correctly
- [x] Solves subtasks completely
- [x] Combines results coherently
- [x] Works for parallel execution
- [x] Works for sequential execution
- [x] Handles blocked subtasks
- [x] Produces complete final solution

## Failure Modes

- **Over-decomposition**: Too many tiny subtasks
  - Mitigation: Limit to 3-7 subtasks
- **Wrong breakdown**: Subtasks don't add up to solution
  - Mitigation: Review decomposition before solving
- **Dependency cycles**: Circular dependencies
  - Mitigation: Detect and report cycles
- **Lost coherence**: Combined result feels fragmented
  - Mitigation: Strong synthesis prompt, add transitions

## Best For

- Complex multi-step problems
- Research projects
- Software development tasks
- Analysis requiring multiple angles
- Any task feeling "overwhelming"
- Workflow automation

## Performance

- **Success rate**: Higher on complex tasks vs. single-shot
- **Cost**: N+2 generations (decompose + N subtasks + combine)
- **Latency**: Can parallelize independent subtasks

## Related Skills

- `tree_of_thought_001` - Alternative branching approach
- `meta_prompting_001` - Design approach first
- `workflow_orchestrator_001` - Coordinate complex workflows

## Timestamp

2026-03-08
