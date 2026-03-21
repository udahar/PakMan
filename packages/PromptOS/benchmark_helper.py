#!/usr/bin/env python3
"""
Two-Mode Benchmarking Helper

Runs benchmarks in two modes:
1. Normal mode - just the prompt and task
2. Structured mode - prompt plus scaffolding (scratchpad, reasoning structure)

Compares results to measure scaffolding impact.

Usage:
    from PromptOS.benchmark_helper import TwoModeBenchmark
    
    bench = TwoModeBenchmark(llm_callable=llm, bench_callback=score)
    
    # Run two-mode benchmark
    results = bench.run_two_mode(
        prompt="Solve this math problem",
        model="qwen2.5:7b",
        test_name="math_reasoning"
    )
    
    print(f"Scaffolding impact: {results['improvement']:.1%}")
"""

from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
import time


@dataclass
class TwoModeResult:
    """Result from two-mode benchmark."""
    prompt: str
    model: str
    test_name: str
    normal_score: float
    normal_response: str
    normal_latency: float
    structured_score: float
    structured_response: str
    structured_latency: float
    improvement: float
    scaffolding_effective: bool


class TwoModeBenchmark:
    """
    Two-mode benchmarking helper.
    
    Runs tests in both normal and structured modes to measure
    how much prompt scaffolding affects performance.
    """
    
    def __init__(
        self,
        llm_callable: Callable,
        bench_callback: Optional[Callable] = None,
    ):
        """
        Initialize two-mode benchmark.
        
        Args:
            llm_callable: LLM callable function
            bench_callback: Bench scoring callback
        """
        self.llm_callable = llm_callable
        self.bench_callback = bench_callback
        
        # Structured mode templates
        self.structured_templates = {
            "reasoning": """Task: {task}

Please work through this systematically:

1. **Understanding**: What is being asked?

2. **Approach**: How will you solve this?

3. **Execution**: Work through the solution step by step.

4. **Verification**: Check your answer for errors.

5. **Final Answer**: Provide your final answer.""",
            
            "coding": """Task: {task}

Please approach this systematically:

1. **Requirements**: What needs to be built?

2. **Plan**: How will you implement this?

3. **Implementation**: Write the code.

4. **Testing**: Include tests.

5. **Final Code**: Provide the complete solution.""",
            
            "discipline": """Task: {task}

Requirements:
- Follow the format exactly
- No extra explanations
- All constraints must be satisfied

Output ONLY the required format.""",
        }
    
    def run_two_mode(
        self,
        prompt: str,
        model: str,
        test_name: str,
        task_type: Optional[str] = None,
    ) -> TwoModeResult:
        """
        Run benchmark in both normal and structured modes.
        
        Args:
            prompt: Test prompt
            model: Model name
            test_name: Test name
            task_type: Task type (auto-detected if None)
        
        Returns:
            TwoModeResult with comparison
        """
        # Auto-detect task type
        if task_type is None:
            task_type = self._detect_task_type(prompt)
        
        # Get structured template
        template = self.structured_templates.get(task_type, self.structured_templates["reasoning"])
        structured_prompt = template.format(task=prompt)
        
        # Run normal mode
        normal_start = time.time()
        normal_response = self.llm_callable(prompt)
        normal_latency = (time.time() - normal_start) * 1000
        
        # Score normal mode
        normal_score = self._score(normal_response, test_name)
        
        # Run structured mode
        structured_start = time.time()
        structured_response = self.llm_callable(structured_prompt)
        structured_latency = (time.time() - structured_start) * 1000
        
        # Score structured mode
        structured_score = self._score(structured_response, test_name)
        
        # Calculate improvement
        improvement = structured_score - normal_score
        scaffolding_effective = improvement > 0.05  # 5% threshold
        
        return TwoModeResult(
            prompt=prompt,
            model=model,
            test_name=test_name,
            normal_score=normal_score,
            normal_response=normal_response,
            normal_latency=normal_latency,
            structured_score=structured_score,
            structured_response=structured_response,
            structured_latency=structured_latency,
            improvement=improvement,
            scaffolding_effective=scaffolding_effective,
        )
    
    def run_batch_two_mode(
        self,
        tests: List[Dict[str, str]],
        model: str,
    ) -> Dict[str, Any]:
        """
        Run two-mode benchmark on a batch of tests.
        
        Args:
            tests: List of {prompt, test_name, task_type} dicts
            model: Model name
        
        Returns:
            Batch results with statistics
        """
        results = []
        
        for test in tests:
            result = self.run_two_mode(
                prompt=test["prompt"],
                model=model,
                test_name=test["test_name"],
                task_type=test.get("task_type"),
            )
            results.append(result)
        
        # Calculate statistics
        normal_scores = [r.normal_score for r in results]
        structured_scores = [r.structured_score for r in results]
        improvements = [r.improvement for r in results]
        
        effective_count = sum(1 for r in results if r.scaffolding_effective)
        
        return {
            "model": model,
            "total_tests": len(results),
            "normal_avg": sum(normal_scores) / len(normal_scores),
            "structured_avg": sum(structured_scores) / len(structured_scores),
            "improvement_avg": sum(improvements) / len(improvements),
            "scaffolding_effective_pct": effective_count / len(results),
            "by_task_type": self._group_by_task_type(results),
            "results": results,
        }
    
    def _detect_task_type(self, prompt: str) -> str:
        """Detect task type from prompt."""
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["write", "code", "function", "implement"]):
            return "coding"
        elif any(kw in prompt_lower for kw in ["json", "format", "schema", "strict"]):
            return "discipline"
        else:
            return "reasoning"
    
    def _score(self, response: str, test_name: str) -> float:
        """Score a response."""
        if self.bench_callback:
            return self.bench_callback(response, test_name)
        
        # Default scoring (placeholder)
        return 0.5
    
    def _group_by_task_type(self, results: List[TwoModeResult]) -> Dict[str, Dict]:
        """Group results by task type."""
        by_type: Dict[str, List[TwoModeResult]] = {}
        
        for result in results:
            task_type = self._detect_task_type(result.prompt)
            if task_type not in by_type:
                by_type[task_type] = []
            by_type[task_type].append(result)
        
        # Calculate stats per type
        stats = {}
        for task_type, type_results in by_type.items():
            stats[task_type] = {
                "count": len(type_results),
                "normal_avg": sum(r.normal_score for r in type_results) / len(type_results),
                "structured_avg": sum(r.structured_score for r in type_results) / len(type_results),
                "improvement_avg": sum(r.improvement for r in type_results) / len(type_results),
            }
        
        return stats


# Convenience function
def benchmark_two_mode(
    llm_callable: Callable,
    prompt: str,
    model: str,
    test_name: str,
    bench_callback: Optional[Callable] = None,
) -> TwoModeResult:
    """
    Run two-mode benchmark.
    
    Args:
        llm_callable: LLM callable
        prompt: Test prompt
        model: Model name
        test_name: Test name
        bench_callback: Optional scoring callback
    
    Returns:
        TwoModeResult
    """
    bench = TwoModeBenchmark(llm_callable=llm_callable, bench_callback=bench_callback)
    return bench.run_two_mode(prompt, model, test_name)
