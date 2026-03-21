"""
Real Model Evaluator - Actually calls AI models and runs tests

This integrates with your existing benchmark system to get real scores.
"""

import time
import json
from typing import Any, Optional
from datetime import datetime


class RealModelEvaluator:
    """
    Actually evaluates models by calling them and scoring outputs.
    
    Integrates with existing benchmark infrastructure.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self._test_cache = {}
    
    def evaluate(
        self,
        model: str,
        role: str,
        test_suite: list[dict],
    ) -> dict[str, Any]:
        """
        Run real evaluation against a model.
        
        Args:
            model: Model name (e.g., "qwen2.5:7b")
            role: Role to evaluate for
            test_suite: List of test cases
        
        Returns:
            Dict with quality, reliability, latency metrics
        """
        results = []
        total_time = 0
        passed = 0
        
        for test in test_suite:
            start = time.time()
            
            # Call the model
            output = self._call_model(model, test["input"])
            
            elapsed = time.time() - start
            total_time += elapsed
            
            # Score the output
            score = self._score_output(output, test)
            
            results.append({
                "test": test["name"],
                "passed": score["passed"],
                "quality": score["quality"],
                "latency_ms": elapsed * 1000,
                "output": output,
            })
            
            if score["passed"]:
                passed += 1
        
        # Calculate metrics
        avg_latency = total_time / len(results) * 1000 if results else 0
        reliability = (passed / len(results)) * 100 if results else 0
        avg_quality = sum(r["quality"] for r in results) / len(results) if results else 0
        
        return {
            "quality": avg_quality,
            "reliability": reliability,
            "latency_ms": avg_latency,
            "test_results": results,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _call_model(self, model: str, prompt: str) -> str:
        """Call model via Ollama API."""
        try:
            import requests
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
            
        except Exception as e:
            return f"Error: {e}"
    
    def _score_output(self, output: str, test: dict) -> dict:
        """
        Score a model's output against test criteria.
        
        Returns dict with passed (bool) and quality (0-100).
        """
        score = 0
        max_score = 0
        
        # Check expected output contains
        if "expected_output_contains" in test:
            max_score += 50
            for expected in test["expected_output_contains"]:
                if expected.lower() in output.lower():
                    score += 50 / len(test["expected_output_contains"])
        
        # Check expected tools
        if "expected_tools" in test:
            max_score += 50
            for tool in test["expected_tools"]:
                if tool.lower() in output.lower():
                    score += 50 / len(test["expected_tools"])
        
        # Check structure
        if "expected_structure" in test:
            max_score += 30
            for section in test["expected_structure"]:
                if section.lower() in output.lower():
                    score += 30 / len(test["expected_structure"])
        
        # Calculate quality percentage
        quality = (score / max_score * 100) if max_score > 0 else 0
        
        # Passed threshold
        passed = quality >= 70  # 70% quality threshold
        
        return {
            "passed": passed,
            "quality": quality,
            "score": score,
            "max_score": max_score,
        }


def get_test_suite_for_role(role: str) -> list[dict]:
    """Load test suite for a specific role."""
    if role == "planner":
        from kofh.tests.planner_tests import PLANNER_TESTS
        return PLANNER_TESTS
    elif role == "engineer":
        from kofh.tests.engineer_tests import ENGINEER_TESTS
        return ENGINEER_TESTS
    elif role == "scientist":
        from kofh.tests.scientist_tests import SCIENTIST_TESTS
        return SCIENTIST_TESTS
    elif role == "analyst":
        from kofh.tests.analyst_tests import ANALYST_TESTS
        return ANALYST_TESTS
    else:
        return []
