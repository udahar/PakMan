#!/usr/bin/env python3
"""
Benchmark Arena - Automated Model Comparison
Starter implementation
"""

from dataclasses import dataclass
from typing import Optional
from langchain_ollama import ChatOllama
import time


MODEL_CATALOG = {
    "qwen2.5:7b": {"quality": 7, "speed": 1.0, "cost": 0.0},
    "qwen2.5:3b": {"quality": 5, "speed": 1.5, "cost": 0.0},
    "llama3.2:3b": {"quality": 6, "speed": 1.2, "cost": 0.0},
    "mistral:7b": {"quality": 6, "speed": 1.1, "cost": 0.0},
    "gpt-4o": {"quality": 9, "speed": 0.8, "cost": 5.0},
    "gpt-4o-mini": {"quality": 7, "speed": 2.0, "cost": 0.15},
}


@dataclass
class BenchmarkResult:
    model: str
    prompt: str
    response: str
    latency: float
    tokens: int
    quality_score: Optional[float] = None


class TaskClassifier:
    def classify(self, task: str) -> str:
        task_lower = task.lower()

        if any(w in task_lower for w in ["code", "function", "implement", "write"]):
            return "coding"
        elif any(w in task_lower for w in ["explain", "what is", "how does"]):
            return "reasoning"
        elif any(w in task_lower for w in ["write", "story", "poem", "creative"]):
            return "creative"
        elif any(w in task_lower for w in ["summarize", "extract", "find"]):
            return "analysis"
        else:
            return "general"


class CostTracker:
    def __init__(self):
        self.sessions = []

    def track(self, model: str, prompt_tokens: int, completion_tokens: int):
        cost_per_1k = MODEL_CATALOG.get(model, {}).get("cost", 0)
        total = (prompt_tokens + completion_tokens) / 1000 * cost_per_1k

        self.sessions.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": total,
            }
        )

    def total_spent(self) -> float:
        return sum(s["cost"] for s in self.sessions)


class Arena:
    def __init__(self):
        self.classifier = TaskClassifier()
        self.cost_tracker = CostTracker()
        self.leaderboard = {}

    def auto_select(self, task: str, budget: float = None, min_quality: int = 5):
        task_type = self.classifier.classify(task)

        # Filter models by quality and budget
        candidates = []
        for model, specs in MODEL_CATALOG.items():
            if specs["quality"] < min_quality:
                continue
            if budget and specs["cost"] > budget:
                continue
            candidates.append((model, specs))

        # Sort by quality/speed ratio
        candidates.sort(key=lambda x: x[1]["quality"] / x[1]["speed"], reverse=True)

        return [c[0] for c in candidates[:3]]

    def run_arena(self, prompt: str, models: list[str] = None):
        if not models:
            models = self.auto_select(prompt)

        results = []

        for model in models:
            print(f"Running {model}...")

            llm = ChatOllama(model=model)

            start = time.time()
            response = llm.invoke(prompt)
            latency = time.time() - start

            result = BenchmarkResult(
                model=model,
                prompt=prompt,
                response=response.content,
                latency=latency,
                tokens=len(response.content.split()),
            )

            results.append(result)

            # Track cost
            if hasattr(response, "usage"):
                self.cost_tracker.track(
                    model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )

        return results

    def print_results(self, results: list[BenchmarkResult]):
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        for r in results:
            print(f"\nModel: {r.model}")
            print(f"  Latency: {r.latency:.2f}s")
            print(f"  Tokens: {r.tokens}")
            cost = MODEL_CATALOG.get(r.model, {}).get("cost", 0)
            print(f"  Est Cost: ${cost * r.tokens / 1000:.4f}")

        print(f"\nTotal spent: ${self.cost_tracker.total_spent():.4f}")


if __name__ == "__main__":
    arena = Arena()

    # Auto-select models for task
    models = arena.auto_select("Write a Python function to calculate fibonacci")
    print(f"Selected models: {models}")

    # Run benchmark
    results = arena.run_arena("Write a Python function to calculate fibonacci", models)

    # Print results
    arena.print_results(results)
