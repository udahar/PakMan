# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Model Selector
Advanced model selection with learning from past performance
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib

from .registry import ModelRegistry, ModelInfo, create_model_registry
from .router import ModelRouter, RoutingDecision, create_model_router

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ModelCache:
    """Redis-backed cache for model routing decisions and performance."""

    def __init__(
        self, host: str = "localhost", port: int = 6379, prefix: str = "frank:model:"
    ):
        self.prefix = prefix
        self.client = None
        self.use_redis = False
        self._connect(host, port)

    def _connect(self, host: str, port: int):
        if not REDIS_AVAILABLE:
            return
        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            self.client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def _key(self, name: str) -> str:
        return f"{self.prefix}{name}"

    def cache_routing(self, task: str, decision: Dict[str, Any], ttl: int = 300):
        """Cache routing decision for similar tasks."""
        if not self.use_redis:
            return
        task_hash = hashlib.md5(task[:200].encode()).hexdigest()
        try:
            self.client.setex(
                self._key(f"route:{task_hash}"), ttl, json.dumps(decision)
            )
        except Exception:
            pass

    def get_cached_routing(self, task: str) -> Optional[Dict[str, Any]]:
        """Get cached routing decision."""
        if not self.use_redis:
            return None
        task_hash = hashlib.md5(task[:200].encode()).hexdigest()
        try:
            data = self.client.get(self._key(f"route:{task_hash}"))
            return json.loads(data) if data else None
        except Exception:
            return None

    def cache_performance(self, model_id: str, perf: Dict[str, Any], ttl: int = 86400):
        """Cache model performance metrics."""
        if not self.use_redis:
            return
        try:
            self.client.setex(self._key(f"perf:{model_id}"), ttl, json.dumps(perf))
        except Exception:
            pass

    def get_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get cached performance for model."""
        if not self.use_redis:
            return None
        try:
            data = self.client.get(self._key(f"perf:{model_id}"))
            return json.loads(data) if data else None
        except Exception:
            return None

    def get_all_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached performance metrics."""
        if not self.use_redis:
            return {}
        try:
            keys = self.client.keys(self._key("perf:*"))
            result = {}
            for key in keys:
                model_id = key.replace(self._key("perf:"), "")
                data = self.client.get(key)
                if data:
                    result[model_id] = json.loads(data)
            return result
        except Exception:
            return {}

    def cache_response(self, task: str, response: str, ttl: int = 3600):
        """Cache model response for retry scenarios."""
        if not self.use_redis:
            return
        task_hash = hashlib.sha256(task.encode()).hexdigest()
        try:
            self.client.setex(self._key(f"response:{task_hash}"), ttl, response)
        except Exception:
            pass

    def get_cached_response(self, task: str) -> Optional[str]:
        """Get cached response for task."""
        if not self.use_redis:
            return None
        task_hash = hashlib.sha256(task.encode()).hexdigest()
        try:
            return self.client.get(self._key(f"response:{task_hash}"))
        except Exception:
            return None

    def invalidate_model(self, model_id: str):
        """Invalidate all cache for a specific model."""
        if not self.use_redis:
            return
        try:
            self.client.delete(self._key(f"perf:{model_id}"))
        except Exception:
            pass


@dataclass
class ModelPerformance:
    """Track model performance."""

    model_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_latency_ms: float = 0.0
    avg_quality_score: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    last_used: Optional[datetime] = None
    consecutive_failures: int = 0
    health_score: float = 1.0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    @property
    def avg_cost_per_call(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_cost / self.total_calls


class ModelSelector:
    """
    Advanced model selector with learning.

    Features:
    - Track per-model performance
    - Learn from success/failure
    - Adapt to user preferences
    - Fallback chains
    - Redis caching for distributed systems
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        router: Optional[ModelRouter] = None,
        use_cache: bool = True,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        self.registry = registry or create_model_registry()
        self.router = router or ModelRouter(registry=self.registry)
        self.performance: Dict[str, ModelPerformance] = {}
        self.user_preferences: Dict[str, float] = {}

        self.cache = None
        if use_cache:
            self.cache = ModelCache(host=redis_host, port=redis_port)
            if self.cache.use_redis:
                self._load_performance_from_cache()

    def _load_performance_from_cache(self):
        """Load cached performance metrics on startup."""
        if not self.cache or not self.cache.use_redis:
            return
        cached = self.cache.get_all_performance()
        for model_id, perf_data in cached.items():
            perf = ModelPerformance(
                model_id=model_id,
                total_calls=perf_data.get("total_calls", 0),
                successful_calls=perf_data.get("successful_calls", 0),
                failed_calls=perf_data.get("failed_calls", 0),
                avg_latency_ms=perf_data.get("avg_latency_ms", 0.0),
                avg_quality_score=perf_data.get("avg_quality_score", 0.0),
                total_cost=perf_data.get("total_cost", 0.0),
                total_tokens=perf_data.get("total_tokens", 0),
                consecutive_failures=perf_data.get("consecutive_failures", 0),
                health_score=perf_data.get("health_score", 1.0),
            )
            self.performance[model_id] = perf

    def select(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict]] = None,
    ) -> RoutingDecision:
        """Select best model for task."""
        context = context or {}

        prefer_cheap = context.get("prefer_cheap", False)
        prefer_fast = context.get("prefer_fast", False)
        prefer_quality = context.get("prefer_quality", False)

        if history and len(history) > 0:
            last_model = history[-1].get("model_id")
            if last_model and last_model in self.performance:
                perf = self.performance[last_model]
                if perf.avg_quality_score < 0.5:
                    prefer_quality = True

        decision = self.router.route(
            task,
            prefer_cheap=prefer_cheap,
            prefer_fast=prefer_fast,
            prefer_quality=prefer_quality,
        )

        if self.cache and self.cache.use_redis:
            self.cache.cache_routing(
                task,
                {
                    "model_id": decision.model_id,
                    "alternatives": decision.alternatives,
                    "reason": decision.reason,
                },
            )

        return decision

    def record_success(
        self,
        model_id: str,
        latency_ms: float,
        quality_score: float,
        tokens_used: int = 0,
        cost: float = 0.0,
    ):
        """Record successful call with full metrics."""
        if model_id not in self.performance:
            self.performance[model_id] = ModelPerformance(model_id=model_id)

        perf = self.performance[model_id]
        perf.total_calls += 1
        perf.successful_calls += 1
        perf.consecutive_failures = 0
        perf.last_used = datetime.now()

        n = perf.successful_calls
        perf.avg_latency_ms = (perf.avg_latency_ms * (n - 1) + latency_ms) / n
        perf.avg_quality_score = (perf.avg_quality_score * (n - 1) + quality_score) / n

        if tokens_used > 0:
            perf.total_tokens += tokens_used
        if cost > 0:
            perf.total_cost += cost

        perf.health_score = min(1.0, perf.health_score + 0.05)

        if self.cache and self.cache.use_redis:
            self.cache.cache_performance(
                model_id,
                {
                    "total_calls": perf.total_calls,
                    "successful_calls": perf.successful_calls,
                    "failed_calls": perf.failed_calls,
                    "avg_latency_ms": perf.avg_latency_ms,
                    "avg_quality_score": perf.avg_quality_score,
                    "total_cost": perf.total_cost,
                    "total_tokens": perf.total_tokens,
                    "consecutive_failures": perf.consecutive_failures,
                    "health_score": perf.health_score,
                },
            )

    def record_failure(self, model_id: str, error_type: str = "unknown"):
        """Record failed call with error tracking."""
        if model_id not in self.performance:
            self.performance[model_id] = ModelPerformance(model_id=model_id)

        perf = self.performance[model_id]
        perf.total_calls += 1
        perf.failed_calls += 1
        perf.consecutive_failures += 1
        perf.last_used = datetime.now()

        if perf.consecutive_failures >= 3:
            perf.health_score = max(0.0, perf.health_score - 0.2)

        if self.cache and self.cache.use_redis:
            self.cache.cache_performance(
                model_id,
                {
                    "total_calls": perf.total_calls,
                    "successful_calls": perf.successful_calls,
                    "failed_calls": perf.failed_calls,
                    "avg_latency_ms": perf.avg_latency_ms,
                    "avg_quality_score": perf.avg_quality_score,
                    "total_cost": perf.total_cost,
                    "total_tokens": perf.total_tokens,
                    "consecutive_failures": perf.consecutive_failures,
                    "health_score": perf.health_score,
                },
            )
            self.cache.invalidate_model(model_id)

    def get_fallback_chain(self, task: str, max_models: int = 3) -> List[str]:
        """Get fallback chain for task."""
        decision = self.router.route(task)

        chain = [decision.model_id]

        if decision.alternatives:
            chain.extend(decision.alternatives[: max_models - 1])

        return chain

    def get_best_for_task_type(self, task_type: str, limit: int = 3) -> List[ModelInfo]:
        """Get best models for task type."""
        from .registry import ModelCapability

        capability_map = {
            "coding": ModelCapability.CODING,
            "reasoning": ModelCapability.REASONING,
            "creative": ModelCapability.CREATIVE,
            "fast": ModelCapability.FAST,
            "cheap": ModelCapability.CHEAP,
        }

        capability = capability_map.get(task_type.lower())
        if not capability:
            return list(self.registry.models.values())[:limit]

        models = self.registry.find_models(capability)

        if models:
            models.sort(key=lambda m: m.quality_score, reverse=True)
            return models[:limit]

        return list(self.registry.models.values())[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get selector stats."""
        return {
            "models_tracked": len(self.performance),
            "performance": {
                mid: {
                    "total": p.total_calls,
                    "success_rate": p.successful_calls / p.total_calls
                    if p.total_calls > 0
                    else 0,
                    "avg_latency": p.avg_latency_ms,
                    "avg_quality": p.avg_quality_score,
                    "total_cost": p.total_cost,
                    "health_score": p.health_score,
                }
                for mid, p in self.performance.items()
            },
            "router_stats": self.router.get_stats(),
        }

    def check_model_health(self, model_id: str) -> Dict[str, Any]:
        """Check health status of a model."""
        if model_id not in self.performance:
            return {"status": "unknown", "health_score": 1.0}

        perf = self.performance[model_id]

        if perf.health_score >= 0.8:
            status = "healthy"
        elif perf.health_score >= 0.5:
            status = "degraded"
        elif perf.health_score > 0:
            status = "unhealthy"
        else:
            status = "failed"

        return {
            "status": status,
            "health_score": perf.health_score,
            "consecutive_failures": perf.consecutive_failures,
            "success_rate": perf.success_rate,
            "avg_latency_ms": perf.avg_latency_ms,
            "last_used": perf.last_used.isoformat() if perf.last_used else None,
        }

    def get_healthy_models(self) -> List[str]:
        """Get list of healthy models."""
        healthy = []
        for model_id, perf in self.performance.items():
            if perf.health_score >= 0.5:
                healthy.append(model_id)
        return healthy

    def get_best_performing(self, metric: str = "quality", limit: int = 3) -> List[str]:
        """Get best performing models by metric."""
        if metric == "quality":
            sorted_models = sorted(
                self.performance.items(),
                key=lambda x: x[1].avg_quality_score,
                reverse=True,
            )
        elif metric == "speed":
            sorted_models = sorted(
                self.performance.items(), key=lambda x: x[1].avg_latency_ms
            )
        elif metric == "cost":
            sorted_models = sorted(
                self.performance.items(), key=lambda x: x[1].avg_cost_per_call
            )
        else:
            sorted_models = sorted(
                self.performance.items(), key=lambda x: x[1].health_score, reverse=True
            )

        return [m[0] for m in sorted_models[:limit]]

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get total cost summary across all models."""
        total_cost = sum(p.total_cost for p in self.performance.values())
        total_tokens = sum(p.total_tokens for p in self.performance.values())

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "by_model": {
                mid: {
                    "cost": p.total_cost,
                    "tokens": p.total_tokens,
                    "avg_cost_per_call": p.avg_cost_per_call,
                }
                for mid, p in self.performance.items()
            },
        }


def create_model_selector() -> ModelSelector:
    """Factory function to create model selector."""
    return ModelSelector()
