# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Model Router
Route tasks to the best model based on task analysis
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .registry import ModelRegistry, ModelInfo, ModelCapability, create_model_registry


@dataclass
class RoutingDecision:
    """Decision about which model to use."""

    model_id: str
    model_name: str
    reason: str
    confidence: float
    alternatives: List[str]


class ModelRouter:
    """
    Route tasks to the best model based on:
    - Task type
    - Complexity
    - Cost constraints
    - Speed requirements
    """

    TASK_PATTERNS = {
        "coding": ["code", "program", "function", "script", "debug", "refactor"],
        "reasoning": ["think", "reason", "solve", "explain", "analyze"],
        "creative": ["write", "create", "story", "poem", "creative"],
        "fast": ["quick", "simple", "fast", "short"],
        "analysis": ["analyze", "review", "compare", "evaluate"],
        "large_context": ["document", "file", "long", "large"],
    }

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        default_model: str = "qwen2.5:7b",
    ):
        self.registry = registry or create_model_registry()
        self.default_model = default_model
        self.usage_stats: Dict[str, int] = {}

    def analyze_task(self, task: str) -> Dict[str, float]:
        """Analyze task to determine requirements."""
        task_lower = task.lower()

        scores = {
            "needs_coding": 0.0,
            "needs_reasoning": 0.0,
            "needs_creative": 0.0,
            "needs_fast": 0.0,
            "needs_analysis": 0.0,
            "needs_large_context": 0.0,
            "complexity": 0.5,
        }

        for pattern in self.TASK_PATTERNS["coding"]:
            if pattern in task_lower:
                scores["needs_coding"] += 0.3

        for pattern in self.TASK_PATTERNS["reasoning"]:
            if pattern in task_lower:
                scores["needs_reasoning"] += 0.25

        for pattern in self.TASK_PATTERNS["creative"]:
            if pattern in task_lower:
                scores["needs_creative"] += 0.25

        for pattern in self.TASK_PATTERNS["fast"]:
            if pattern in task_lower:
                scores["needs_fast"] += 0.4

        for pattern in self.TASK_PATTERNS["analysis"]:
            if pattern in task_lower:
                scores["needs_analysis"] += 0.3

        for pattern in self.TASK_PATTERNS["large_context"]:
            if pattern in task_lower:
                scores["needs_large_context"] += 0.4

        scores["complexity"] = min(1.0, len(task.split()) / 50.0)

        return scores

    def route(
        self,
        task: str,
        prefer_cheap: bool = False,
        prefer_fast: bool = False,
        prefer_quality: bool = False,
        max_cost: Optional[float] = None,
    ) -> RoutingDecision:
        """Route task to best model."""
        analysis = self.analyze_task(task)

        candidates = []

        for model_id, model in self.registry.models.items():
            if max_cost and model.cost_per_1k_tokens > max_cost:
                continue

            score = 0.0
            reasons = []

            if analysis["needs_coding"] > 0.3:
                if ModelCapability.CODING in model.capabilities:
                    score += 0.4
                    reasons.append("coding capable")

            if analysis["needs_reasoning"] > 0.3:
                if ModelCapability.REASONING in model.capabilities:
                    score += 0.4
                    reasons.append("reasoning capable")

            if analysis["needs_fast"] > 0.3 or prefer_fast:
                score += model.speed_score * 0.3
                reasons.append(f"fast ({model.avg_latency_ms}ms)")

            if prefer_cheap:
                score += (1.0 - model.cost_per_1k_tokens) * 0.2

            if prefer_quality:
                score += model.quality_score * 0.3

            if analysis["needs_large_context"] > 0.3:
                if ModelCapability.LARGE_CONTEXT in model.capabilities:
                    score += 0.3
                    reasons.append("large context")

            score += (1.0 - analysis["complexity"]) * model.speed_score * 0.2

            candidates.append((model_id, model, score, reasons))

        if not candidates:
            return self._default_decision()

        candidates.sort(key=lambda x: x[2], reverse=True)

        best_id, best_model, best_score, reasons = candidates[0]

        self.usage_stats[best_id] = self.usage_stats.get(best_id, 0) + 1

        return RoutingDecision(
            model_id=best_id,
            model_name=best_model.name,
            reason=", ".join(reasons) if reasons else "best match",
            confidence=min(best_score, 1.0),
            alternatives=[c[0] for c in candidates[1:3]],
        )

    def _default_decision(self) -> RoutingDecision:
        """Return default decision."""
        model = self.registry.get_model(self.default_model)
        return RoutingDecision(
            model_id=self.default_model,
            model_name=model.name if model else self.default_model,
            reason="default",
            confidence=0.5,
            alternatives=list(self.registry.models.keys())[:2],
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get routing stats."""
        total = sum(self.usage_stats.values())
        return {
            "total_routes": total,
            "by_model": self.usage_stats,
            "available_models": len(self.registry.models),
        }


def create_model_router(default_model: str = "qwen2.5:7b") -> ModelRouter:
    """Factory function to create model router."""
    return ModelRouter(default_model=default_model)
