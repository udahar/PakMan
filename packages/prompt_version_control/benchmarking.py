"""
Prompt Benchmarking Integration

Run standardized tests on prompt versions and track metrics.
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""
    version_id: str
    test_name: str
    latency_ms: float
    quality_score: float
    token_count: int
    cost_estimate: float
    response: str
    metadata: Dict[str, Any]


class PromptBenchmarker:
    """
    Run benchmarks on prompt versions.
    
    Integrates with:
    - PromptRepo (for version retrieval)
    - Observatory (for metrics storage)
    - KOFH (for model evaluation)
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self._test_suites: Dict[str, List[Dict]] = {}
    
    def register_test_suite(self, name: str, tests: List[Dict]):
        """Register a test suite."""
        self._test_suites[name] = tests
    
    def run_benchmark(
        self,
        version_id: str,
        prompt: str,
        system: str,
        model: str,
        test_input: str,
        expected_output: Optional[str] = None,
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        try:
            import requests
            
            # Build request
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": test_input})
            
            # Time the request
            start = time.time()
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt.replace("{input}", test_input),
                    "system": system,
                    "stream": False,
                },
                timeout=120
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            response_data = response.json()
            response_text = response_data.get("response", "")
            
            # Calculate quality score
            quality_score = self._calculate_quality(
                response_text, expected_output
            ) if expected_output else 0.5
            
            # Estimate tokens
            token_count = len(response_text.split()) * 1.3  # Rough estimate
            
            # Estimate cost (local = free, but API would cost)
            cost_estimate = 0.0
            
            return BenchmarkResult(
                version_id=version_id,
                test_name="benchmark",
                latency_ms=latency_ms,
                quality_score=quality_score,
                token_count=int(token_count),
                cost_estimate=cost_estimate,
                response=response_text,
                metadata=response_data,
            )
            
        except Exception as e:
            return BenchmarkResult(
                version_id=version_id,
                test_name="benchmark",
                latency_ms=0,
                quality_score=0,
                token_count=0,
                cost_estimate=0,
                response=f"Error: {e}",
                metadata={"error": str(e)},
            )
    
    def _calculate_quality(
        self,
        response: str,
        expected: Optional[str],
    ) -> float:
        """Calculate quality score (0-1)."""
        if not expected:
            return 0.5  # No ground truth
        
        # Simple string matching
        response_lower = response.lower()
        expected_lower = expected.lower()
        
        # Check for key terms
        expected_terms = expected_lower.split()
        matches = sum(1 for term in expected_terms if term in response_lower)
        
        return matches / len(expected_terms) if expected_terms else 0.5
    
    def run_test_suite(
        self,
        version_id: str,
        prompt: str,
        system: str,
        model: str,
        suite_name: str,
    ) -> List[BenchmarkResult]:
        """Run a full test suite."""
        if suite_name not in self._test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        results = []
        
        for test in self._test_suites[suite_name]:
            result = self.run_benchmark(
                version_id=version_id,
                prompt=prompt,
                system=system,
                model=model,
                test_input=test["input"],
                expected_output=test.get("expected"),
            )
            results.append(result)
        
        return results
    
    def compare_versions(
        self,
        version_ids: List[str],
        prompts: Dict[str, str],
        systems: Dict[str, str],
        models: Dict[str, str],
        test_suite: List[Dict],
    ) -> Dict[str, Any]:
        """Compare multiple versions on the same tests."""
        results = {}
        
        for version_id in version_ids:
            prompt = prompts.get(version_id, "")
            system = systems.get(version_id, "")
            model = models.get(version_id, "qwen2.5:7b")
            
            version_results = []
            
            for test in test_suite:
                result = self.run_benchmark(
                    version_id=version_id,
                    prompt=prompt,
                    system=system,
                    model=model,
                    test_input=test["input"],
                    expected_output=test.get("expected"),
                )
                version_results.append(result)
            
            # Calculate averages
            avg_latency = sum(r.latency_ms for r in version_results) / len(version_results)
            avg_quality = sum(r.quality_score for r in version_results) / len(version_results)
            
            results[version_id] = {
                "avg_latency_ms": avg_latency,
                "avg_quality_score": avg_quality,
                "tests": len(version_results),
                "results": version_results,
            }
        
        return results


# Example test suites
EXAMPLE_TEST_SUITES = {
    "code_generation": [
        {
            "input": "Write a Python function to add two numbers",
            "expected": "def add(a, b): return a + b",
        },
        {
            "input": "Create a Rust struct for a user",
            "expected": "struct User",
        },
    ],
    "reasoning": [
        {
            "input": "If all A are B, and some B are C, what can we conclude?",
            "expected": "some A might be C",
        },
    ],
    "summarization": [
        {
            "input": "Summarize: The quick brown fox jumps over the lazy dog.",
            "expected": "Fox jumps over dog",
        },
    ],
}
