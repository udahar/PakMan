# Skill: Chain of Thought

**skill_id:** `chain_of_thought_001`  
**name:** chain_of_thought  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Forces step-by-step reasoning before answering, improving accuracy on math, logic, and debugging tasks.

## Primitive Tags

- step_by_step
- sequential_reasoning
- explicit_thinking
- intermediate_steps
- reasoning_trace
- final_answer

## Prompt Strategy

```
For Chain of Thought:

1. PRESENT PROBLEM
   - State the question clearly

2. REASON STEP-BY-STEP
   - Break down into logical steps
   - Show each inference
   - Number the steps

3. STATE FINAL ANSWER
   - Clearly mark the conclusion
   - Ensure it follows from reasoning
```

## Solution Summary

### Prompt Template

```
Question: {question}

Let's solve this step-by-step:

Step 1: [First logical step]
Step 2: [Next inference]
Step 3: [Continue reasoning]
...
Step N: [Final inference]

Therefore, the answer is: [FINAL ANSWER]
```

### Python Implementation

```python
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ReasoningStep:
    step_number: int
    reasoning: str
    conclusion: Optional[str] = None


@dataclass
class ChainOfThoughtResult:
    question: str
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float = 1.0


async def chain_of_thought(
    question: str,
    model_fn,
    max_steps: int = 10
) -> ChainOfThoughtResult:
    """
    Generate step-by-step reasoning for a question.
    
    Args:
        question: The problem to solve
        model_fn: Async function to call LLM
        max_steps: Maximum reasoning steps
    
    Returns:
        ChainOfThoughtResult with steps and answer
    """
    prompt = f"""Question: {question}

Solve this step-by-step. For each step:
1. Number it (Step 1, Step 2, etc.)
2. Show your reasoning
3. Draw a small conclusion if applicable

After all steps, clearly state: "Therefore, the answer is: [your answer]"

Limit: {max_steps} steps maximum."""

    response = await model_fn(prompt)
    
    # Parse response into structured steps
    steps = parse_reasoning_steps(response)
    final_answer = extract_final_answer(response)
    
    return ChainOfThoughtResult(
        question=question,
        steps=steps,
        final_answer=final_answer,
        confidence=1.0
    )


def parse_reasoning_steps(response: str) -> List[ReasoningStep]:
    """Parse LLM response into structured reasoning steps."""
    import re
    
    steps = []
    step_pattern = r'(?:step\s*(\d+)[:\.]?\s*)(.*?)(?=(?:step\s*\d+|$))'
    
    matches = re.findall(step_pattern, response, re.IGNORECASE | re.DOTALL)
    
    for num, content in matches:
        steps.append(ReasoningStep(
            step_number=int(num),
            reasoning=content.strip()
        ))
    
    return steps


def extract_final_answer(response: str) -> str:
    """Extract the final answer from response."""
    import re
    
    # Look for common answer patterns
    patterns = [
        r'(?:therefore|thus|hence),?\s*(?:the)?\s*(?:answer is)?[:\s]+(.+?)(?:\n|$)',
        r'(?:final answer)[:\s]+(.+?)(?:\n|$)',
        r'(?:answer)[:\s]+(.+?)(?:\n|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Fallback: return last line
    return response.strip().split('\n')[-1]
```

## Tests Passed

- [x] Generates numbered reasoning steps
- [x] Shows intermediate conclusions
- [x] Clearly marks final answer
- [x] Works for math problems
- [x] Works for logic puzzles
- [x] Works for debugging tasks

## Failure Modes

- **Skipping steps**: Model jumps to conclusion
  - Mitigation: Explicitly require "Show all work"
- **Too verbose**: Excessive detail in steps
  - Mitigation: Set max steps, request conciseness
- **Wrong final answer**: Reasoning correct, conclusion wrong
  - Mitigation: Add verification step

## Best For

- Mathematics problems
- Logic puzzles
- Code debugging
- Multi-step calculations
- Causal reasoning

## Related Skills

- `self_consistent_cot_001` - Multiple CoT with voting
- `react_reasoning_001` - Reasoning with tool use
- `program_of_thought_001` - Code-based reasoning

## Timestamp

2026-03-08
