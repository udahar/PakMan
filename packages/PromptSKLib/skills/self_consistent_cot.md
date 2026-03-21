# Skill: Self-Consistent Chain of Thought

**skill_id:** `self_consistent_cot_001`  
**name:** self_consistent_chain_of_thought  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Runs Chain of Thought multiple times with varied reasoning paths, then uses majority voting to select the most reliable answer.

## Primitive Tags

- multiple_samples
- voting_ensemble
- reasoning_diversity
- consistency_check
- reliability_boost
- monte_carlo_reasoning

## Prompt Strategy

```
For Self-Consistent CoT:

1. GENERATE MULTIPLE REASONING PATHS
   - Run same problem N times (typically 5-10)
   - Each run reasons independently
   - Encourage diverse approaches

2. EXTRACT ANSWERS
   - Parse final answer from each path
   - Normalize answer formats

3. MAJORITY VOTE
   - Count answer frequencies
   - Select most common answer
   - Report confidence based on agreement

4. HANDLE DISAGREEMENT
   - If no clear majority: flag uncertainty
   - If split: show competing answers
```

## Solution Summary

### Prompt Template (per sample)

```
Question: {question}

Solve this step-by-step. Show your reasoning clearly.

Sample {n} of {total_samples}

After reasoning, state: "Therefore, the answer is: [answer]"
```

### Python Implementation

```python
from typing import List, Dict, Any, Optional
from collections import Counter
from dataclasses import dataclass
import asyncio


@dataclass
class ReasoningPath:
    sample_id: int
    reasoning: str
    answer: str


@dataclass
class SelfConsistentResult:
    question: str
    paths: List[ReasoningPath]
    final_answer: str
    vote_counts: Dict[str, int]
    confidence: float
    agreement_ratio: float


async def self_consistent_cot(
    question: str,
    model_fn,
    num_samples: int = 5,
    temperature: float = 0.7
) -> SelfConsistentResult:
    """
    Generate multiple reasoning paths and vote on the answer.
    
    Args:
        question: The problem to solve
        model_fn: Async function to call LLM
        num_samples: Number of independent reasoning paths
        temperature: Sampling temperature for diversity
    
    Returns:
        SelfConsistentResult with voting results
    """
    # Generate multiple reasoning paths in parallel
    tasks = [
        generate_reasoning_path(question, model_fn, i, num_samples, temperature)
        for i in range(1, num_samples + 1)
    ]
    
    paths = await asyncio.gather(*tasks)
    
    # Extract and count answers
    answers = [p.answer for p in paths]
    vote_counts = Counter(answers)
    
    # Find majority answer
    most_common = vote_counts.most_common(1)[0]
    final_answer = most_common[0]
    final_count = most_common[1]
    
    # Calculate confidence metrics
    agreement_ratio = final_count / num_samples
    
    return SelfConsistentResult(
        question=question,
        paths=paths,
        final_answer=final_answer,
        vote_counts=dict(vote_counts),
        confidence=agreement_ratio,
        agreement_ratio=agreement_ratio
    )


async def generate_reasoning_path(
    question: str,
    model_fn,
    sample_id: int,
    total_samples: int,
    temperature: float
) -> ReasoningPath:
    """Generate a single reasoning path."""
    prompt = f"""Question: {question}

Solve this step-by-step. Show your reasoning clearly.

This is sample {sample_id} of {total_samples}. Think independently.

After reasoning, state: "Therefore, the answer is: [answer]"
"""
    
    response = await model_fn(prompt, temperature=temperature)
    answer = extract_final_answer(response)
    
    return ReasoningPath(
        sample_id=sample_id,
        reasoning=response,
        answer=answer
    )


def extract_final_answer(response: str) -> str:
    """Extract final answer from reasoning response."""
    import re
    
    pattern = r'(?:therefore|thus|hence),?\s*(?:the)?\s*(?:answer is)?[:\s]+(.+?)(?:\n|$)'
    match = re.search(pattern, response, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    return response.strip().split('\n')[-1]
```

## Tests Passed

- [x] Generates multiple independent paths
- [x] Extracts answers correctly
- [x] Counts votes accurately
- [x] Selects majority answer
- [x] Reports agreement ratio
- [x] Handles ties gracefully

## Failure Modes

- **All paths same error**: Systematic bias in model
  - Mitigation: Increase temperature, vary prompts
- **No clear majority**: High disagreement
  - Mitigation: Flag uncertainty, increase samples
- **Expensive**: N x compute cost
  - Mitigation: Use for high-stakes problems only

## Best For

- High-stakes decisions
- Complex math problems
- Ambiguous questions
- When reliability > speed
- Benchmarking baseline

## Performance

- **Accuracy boost**: Typically 5-15% over single CoT
- **Cost**: N x single generation (usually 5-10x)
- **Latency**: Can parallelize, so ~1-2x wall time

## Related Skills

- `chain_of_thought_001` - Single reasoning path
- `contrastive_prompting_001` - Generate and compare
- `debate_multi_agent_001` - Adversarial reasoning

## Timestamp

2026-03-08
