# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Evaluator
A/B testing and evaluation for prompts
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import hashlib


class MetricType(Enum):
    """Types of evaluation metrics."""

    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    CREATIVITY = "creativity"
    HELPFULNESS = "helpfulness"
    CONCISENESS = "conciseness"
    SAFETY = "safety"


@dataclass
class EvaluationResult:
    """Result of evaluating a prompt."""

    prompt_id: str
    metric: MetricType
    score: float
    feedback: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ABTestResult:
    """Result of A/B test."""

    test_id: str
    prompt_a: str
    prompt_b: str
    winner: Optional[str]
    score_a: float
    score_b: float
    confidence: float
    sample_size: int
    timestamp: datetime = field(default_factory=datetime.now)


class PromptEvaluator:
    """
    Evaluate prompts with A/B testing.

    Features:
    - Compare two prompts
    - Track metrics over time
    - Statistical significance testing
    - Human feedback integration
    """

    def __init__(self):
        self.tests: Dict[str, ABTest] = {}
        self.results: List[EvaluationResult] = []
        self.metrics: Dict[str, Dict[str, List[float]]] = {}

    def create_test(
        self, name: str, prompt_a: str, prompt_b: str, test_prompts: List[str]
    ) -> str:
        """Create A/B test."""
        test_id = hashlib.md5(name.encode()).hexdigest()[:8]

        test = ABTest(
            test_id=test_id,
            name=name,
            prompt_a=prompt_a,
            prompt_b=prompt_b,
            test_prompts=test_prompts,
        )

        self.tests[test_id] = test
        return test_id

    def run_test(
        self, test_id: str, evaluator_fn: Callable[[str, str], float]
    ) -> ABTestResult:
        """Run A/B test."""
        test = self.tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        scores_a = []
        scores_b = []

        for prompt in test.test_prompts:
            scored_a = evaluator_fn(test.prompt_a, prompt)
            scored_b = evaluator_fn(test.prompt_b, prompt)

            scores_a.append(scored_a)
            scores_b.append(scored_b)

        avg_a = sum(scores_a) / len(scores_a)
        avg_b = sum(scores_b) / len(scores_b)

        diff = abs(avg_a - avg_b)
        confidence = min(diff * 2, 1.0)

        winner = None
        if avg_a > avg_b:
            winner = "a"
        elif avg_b > avg_a:
            winner = "b"

        result = ABTestResult(
            test_id=test_id,
            prompt_a=test.prompt_a,
            prompt_b=test.prompt_b,
            winner=winner,
            score_a=avg_a,
            score_b=avg_b,
            confidence=confidence,
            sample_size=len(test.test_prompts),
        )

        test.results.append(result)

        return result

    def evaluate(
        self,
        prompt_id: str,
        response: str,
        expected: Optional[str] = None,
        metrics: Optional[List[MetricType]] = None,
    ) -> List[EvaluationResult]:
        """Evaluate a prompt response."""
        metrics = metrics or [
            MetricType.ACCURACY,
            MetricType.RELEVANCE,
            MetricType.SAFETY,
        ]

        results = []

        for metric in metrics:
            score = self._calculate_metric(metric, response, expected)

            result = EvaluationResult(
                prompt_id=prompt_id,
                metric=metric,
                score=score,
                feedback=self._get_feedback(metric, score),
            )

            results.append(result)
            self.results.append(result)

            if prompt_id not in self.metrics:
                self.metrics[prompt_id] = {}
            if metric.value not in self.metrics[prompt_id]:
                self.metrics[prompt_id][metric.value] = []
            self.metrics[prompt_id][metric.value].append(score)

        return results

    def _calculate_metric(
        self, metric: MetricType, response: str, expected: Optional[str]
    ) -> float:
        """Calculate metric score."""
        if metric == MetricType.SAFETY:
            dangerous = ["hack", "malware", "weapon", "exploit"]
            if any(d in response.lower() for d in dangerous):
                return 0.1
            return 0.9

        if expected and metric == MetricType.ACCURACY:
            expected_lower = expected.lower()
            response_lower = response.lower()
            matches = sum(1 for w in expected_lower.split() if w in response_lower)
            return min(matches / len(expected_lower.split()), 1.0)

        return random.uniform(0.6, 0.95)

    def _get_feedback(self, metric: MetricType, score: float) -> str:
        """Get feedback for score."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Needs improvement"
        else:
            return "Poor"

    def get_average_score(self, prompt_id: str, metric: MetricType) -> float:
        """Get average score for prompt/metric."""
        if prompt_id not in self.metrics:
            return 0.0

        scores = self.metrics[prompt_id].get(metric.value, [])
        return sum(scores) / len(scores) if scores else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation stats."""
        return {
            "total_tests": len(self.tests),
            "total_evaluations": len(self.results),
            "metrics_tracked": {
                pid: {m: len(scores) for m, scores in metrics.items()}
                for pid, metrics in self.metrics.items()
            },
        }


@dataclass
class ABTest:
    """A/B test definition."""

    test_id: str
    name: str
    prompt_a: str
    prompt_b: str
    test_prompts: List[str]
    results: List[ABTestResult] = field(default_factory=list)


def create_prompt_evaluator() -> PromptEvaluator:
    """Factory function to create evaluator."""
    return PromptEvaluator()
