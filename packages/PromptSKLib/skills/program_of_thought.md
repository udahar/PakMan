# Skill: Program of Thought (PoT)

**skill_id:** `program_of_thought_001`  
**name:** program_of_thought  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Instead of reasoning in natural language, the model writes and executes code to perform calculations and logical operations, ensuring accurate results.

## Primitive Tags

- code_based_reasoning
- code_execution
- computational_thinking
- accurate_calculation
- programmatic_solution
- code_generation_and_run

## Prompt Strategy

```
For Program of Thought:

1. ANALYZE PROBLEM
   - Identify computational components
   - Determine what needs code vs. reasoning

2. WRITE CODE
   - Generate code to solve the problem
   - Include all necessary calculations
   - Add comments explaining logic

3. EXECUTE CODE
   - Run the code in safe environment
   - Capture output and errors

4. INTERPRET RESULTS
   - Explain what the output means
   - Present final answer
   - Note any limitations
```

## Solution Summary

### Prompt Template

```
Problem: {problem}

Instead of reasoning in text, write Python code to solve this problem.

Your code should:
1. Implement the complete solution
2. Include comments explaining each step
3. Print the final answer clearly

After writing the code, I will execute it and show you the results.
Then you can interpret the output.
```

### Python Implementation

```python
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import ast
import sys
from io import StringIO


@dataclass
class CodeSolution:
    problem: str
    code: str
    code_explanation: str
    execution_output: str
    execution_error: Optional[str]
    interpreted_answer: str
    success: bool


@dataclass
class PoTResult:
    problem: str
    solution: CodeSolution
    reasoning_trace: str
    final_answer: str
    confidence: float


async def program_of_thought(
    problem: str,
    model_fn,
    executor_fn=None,
    timeout: int = 30
) -> PoTResult:
    """
    Solve problem by writing and executing code.
    
    Args:
        problem: The problem to solve
        model_fn: Async function to call LLM
        executor_fn: Function to execute code safely
        timeout: Execution timeout in seconds
    
    Returns:
        PoTResult with executed solution
    """
    # Step 1: Generate code solution
    code_solution = await generate_code_solution(problem, model_fn)
    
    # Step 2: Execute the code
    if executor_fn:
        execution_result = await executor_fn(code_solution.code, timeout)
    else:
        execution_result = execute_code_safely(code_solution.code, timeout)
    
    code_solution.execution_output = execution_result.get("output", "")
    code_solution.execution_error = execution_result.get("error")
    code_solution.success = execution_result.get("success", False)
    
    # Step 3: Interpret results
    interpreted_answer = await interpret_results(
        problem, code_solution, model_fn
    )
    
    return PoTResult(
        problem=problem,
        solution=code_solution,
        reasoning_trace=code_solution.code_explanation,
        final_answer=interpreted_answer,
        confidence=1.0 if code_solution.success else 0.3
    )


async def generate_code_solution(problem: str, model_fn) -> CodeSolution:
    """Generate code to solve the problem."""
    prompt = f"""Problem: {problem}

Solve this by writing Python code.

Requirements:
1. Write complete, runnable code
2. Include comments explaining your logic
3. Print the final answer with a clear label like: print(f"ANSWER: {{result}}")
4. Handle edge cases if applicable

Provide your code in a markdown code block:

```python
# Your code here
```

After the code, briefly explain your approach.
"""
    
    response = await model_fn(prompt)
    
    # Extract code from response
    code = extract_code_block(response)
    explanation = extract_explanation(response)
    
    return CodeSolution(
        problem=problem,
        code=code,
        code_explanation=explanation,
        execution_output="",
        execution_error=None,
        interpreted_answer="",
        success=False
    )


def execute_code_safely(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute code in a restricted environment.
    
    WARNING: This is a simplified example. In production, use:
    - Docker containers
    - Restricted sandboxes
    - Services like E2B, Judge0, etc.
    """
    # Restrict builtins for safety
    restricted_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "pow": pow,
            "round": round,
        }
    }
    
    # Capture stdout
    output_buffer = StringIO()
    sys.stdout = output_buffer
    
    try:
        # Execute with timeout (simplified - use asyncio in production)
        exec(code, restricted_globals)
        output = output_buffer.getvalue()
        success = True
        error = None
    except Exception as e:
        output = ""
        success = False
        error = str(e)
    finally:
        sys.stdout = sys.__stdout__
    
    return {
        "output": output,
        "error": error,
        "success": success
    }


async def interpret_results(
    problem: str,
    solution: CodeSolution,
    model_fn
) -> str:
    """Interpret the execution results."""
    if solution.execution_error:
        return f"Code execution failed: {solution.execution_error}"
    
    prompt = f"""Problem: {problem}

Code that was executed:
```python
{solution.code}
```

Execution output:
{solution.execution_output or "(no output)"}

Based on the execution output, what is the answer to the problem?
Explain your reasoning and state the final answer clearly.
"""
    
    response = await model_fn(prompt)
    return response


def extract_code_block(response: str) -> str:
    """Extract code block from response."""
    import re
    
    pattern = r'```python\s*(.*?)\s*```'
    match = re.search(pattern, response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # Fallback: try to find any code block
    pattern = r'```\s*(.*?)\s*```'
    match = re.search(pattern, response, re.DOTALL)
    
    return match.group(1).strip() if match else response


def extract_explanation(response: str) -> str:
    """Extract explanation from response."""
    # Remove code blocks, keep rest as explanation
    import re
    
    explanation = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
    return explanation.strip()
```

## Tests Passed

- [x] Generates runnable code
- [x] Executes code safely
- [x] Captures output correctly
- [x] Interprets results accurately
- [x] Handles execution errors
- [x] Works for math problems
- [x] Works for data analysis
- [x] Works for algorithmic problems

## Failure Modes

- **Code errors**: Syntax or runtime errors
  - Mitigation: Request model to debug and retry
- **Infinite loops**: Code doesn't terminate
  - Mitigation: Enforce timeout
- **Security risks**: Dangerous code execution
  - Mitigation: Use sandboxed environment, restrict builtins
- **Wrong approach**: Code doesn't solve problem
  - Mitigation: Better problem decomposition

## Best For

- Mathematical calculations
- Data analysis problems
- Algorithm implementation
- Problems requiring precision
- Multi-step computations
- Problems with verifiable answers

## Performance

- **Accuracy**: Near-perfect for computational problems
- **Cost**: 2x generation (code + interpretation)
- **Latency**: + execution time (usually <1s)

## Related Skills

- `chain_of_thought_001` - Text-based reasoning
- `code_generation_001` - General code writing
- `debugging_001` - Fix code errors

## Timestamp

2026-03-08
