# Skill: Reflexion (Self-Critique)

**skill_id:** `reflexion_001`  
**name:** reflexion  
**category:** prompt_strategy  
**version:** 1.0  

## Description

The model critiques its own output, identifies mistakes, and iteratively improves the solution.

## Primitive Tags

- self_critique
- error_detection
- iterative_improvement
- reflection
- feedback_loop
- self_correction

## Prompt Strategy

```
For Reflexion:

1. INITIAL ATTEMPT
   - Generate first solution
   - Complete but not perfect

2. REFLECTION PHASE
   - Review the solution critically
   - Identify specific errors or gaps
   - Note what could be improved

3. REVISED ATTEMPT
   - Address identified issues
   - Improve the solution
   - Explain changes made

4. OPTIONAL: REPEAT
   - Multiple reflection cycles
   - Diminishing returns after 2-3
```

## Solution Summary

### Prompt Templates

**Phase 1: Initial Solution**
```
Problem: {problem}

Generate a complete solution. Don't worry about perfection yet.
```

**Phase 2: Reflection**
```
Review your solution critically:

1. Are there any errors (factual, logical, calculation)?
2. Are there any gaps or missing steps?
3. Is anything unclear or ambiguous?
4. Could this be improved? How?

Be specific and honest about weaknesses.
```

**Phase 3: Revision**
```
Based on your reflection, revise the solution.

For each issue identified:
- Explain how you're fixing it
- Show the corrected version

Provide the complete improved solution.
```

### Python Implementation

```python
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ReflexionPhase(Enum):
    INITIAL = "initial"
    REFLECTION = "reflection"
    REVISION = "revision"


@dataclass
class Reflection:
    errors_found: List[str]
    gaps_identified: List[str]
    improvements_suggested: List[str]
    overall_confidence: float


@dataclass
class ReflexionResult:
    problem: str
    initial_solution: str
    reflection: Reflection
    revised_solution: str
    improvements_made: List[str]
    cycles: int


async def reflexion(
    problem: str,
    model_fn,
    max_cycles: int = 2
) -> ReflexionResult:
    """
    Generate solution with self-critique and revision.
    
    Args:
        problem: The problem to solve
        model_fn: Async function to call LLM
        max_cycles: Number of reflection cycles
    
    Returns:
        ReflexionResult with final improved solution
    """
    # Phase 1: Initial solution
    initial_solution = await generate_initial_solution(problem, model_fn)
    
    improvements_made = []
    current_solution = initial_solution
    
    for cycle in range(max_cycles):
        # Phase 2: Reflection
        reflection = await reflect_on_solution(current_solution, model_fn)
        
        # If no significant issues, stop
        if not reflection.errors_found and not reflection.gaps_identified:
            break
        
        # Phase 3: Revision
        revision_result = await revise_solution(
            current_solution, reflection, model_fn
        )
        
        improvements_made.extend(revision_result['improvements'])
        current_solution = revision_result['revised_solution']
    
    return ReflexionResult(
        problem=problem,
        initial_solution=initial_solution,
        reflection=reflection,
        revised_solution=current_solution,
        improvements_made=improvements_made,
        cycles=cycle + 1
    )


async def generate_initial_solution(problem: str, model_fn) -> str:
    """Generate initial solution."""
    prompt = f"""Problem: {problem}

Generate a complete solution. Work through it systematically.
Don't worry about perfection - we'll review and improve this."""
    
    return await model_fn(prompt)


async def reflect_on_solution(solution: str, model_fn) -> Reflection:
    """Critique the solution."""
    prompt = f"""Review this solution critically:

{solution}

Identify:
1. Any errors (factual, logical, calculation mistakes)
2. Any gaps or missing steps
3. Anything unclear or ambiguous
4. Specific improvements that could be made

Be honest and specific. Format your response as:

ERRORS:
- [list each error]

GAPS:
- [list each gap]

IMPROVEMENTS:
- [list each improvement]

CONFIDENCE: [0-100%]"""
    
    response = await model_fn(prompt)
    
    # Parse response (simplified - would use better parsing in production)
    return Reflection(
        errors_found=parse_section(response, "ERRORS"),
        gaps_identified=parse_section(response, "GAPS"),
        improvements_suggested=parse_section(response, "IMPROVEMENTS"),
        overall_confidence=0.75  # Would parse from response
    )


async def revise_solution(
    solution: str,
    reflection: Reflection,
    model_fn
) -> dict:
    """Revise solution based on reflection."""
    issues = "\n".join(
        reflection.errors_found + 
        reflection.gaps_identified + 
        reflection.improvements_suggested
    )
    
    prompt = f"""Original solution:
{solution}

Issues identified:
{issues}

Revise the solution to address all these issues.
For each change, briefly explain what you fixed.

Provide the complete revised solution."""
    
    response = await model_fn(prompt)
    
    return {
        'revised_solution': response,
        'improvements': reflection.improvements_suggested
    }


def parse_section(response: str, section: str) -> List[str]:
    """Parse a section from the response."""
    import re
    
    pattern = rf'{section}:\s*\n(.*?)(?=\n\n|\n[A-Z]+:|$)'
    match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
    
    if match:
        items = re.findall(r'^[-•*]\s*(.+)$', match.group(1), re.MULTILINE)
        return [item.strip() for item in items]
    
    return []
```

## Tests Passed

- [x] Generates initial complete solution
- [x] Identifies real errors in reflection
- [x] Produces improved revision
- [x] Tracks improvements made
- [x] Stops when no issues found
- [x] Works for code generation
- [x] Works for reasoning tasks

## Failure Modes

- **Over-criticism**: Finding non-existent issues
  - Mitigation: Request "specific, real" errors only
- **Under-criticism**: Missing real problems
  - Mitigation: Provide error type checklist
- **Infinite loops**: Never satisfied
  - Mitigation: Limit cycles to 2-3

## Best For

- Code generation and review
- Complex reasoning tasks
- Writing and editing
- Solution verification
- Learning from mistakes

## Performance

- **Quality improvement**: Typically 10-20% over single attempt
- **Cost**: 2-3x single generation
- **Latency**: Sequential (can't parallelize cycles)

## Related Skills

- `chain_of_thought_001` - Step-by-step reasoning
- `meta_prompting_001` - Design then execute
- `debate_multi_agent_001` - External critique

## Timestamp

2026-03-08
