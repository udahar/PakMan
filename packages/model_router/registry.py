# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Model Registry
Registry of available models with their capabilities
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    """Model providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


class ModelCapability(Enum):
    """Model capabilities."""

    CODING = "coding"
    REASONING = "reasoning"
    CREATIVE = "creative"
    FAST = "fast"
    CHEAP = "cheap"
    LARGE_CONTEXT = "large_context"
    MULTIMODAL = "multimodal"


@dataclass
class ModelInfo:
    """Information about a model."""

    model_id: str
    name: str
    provider: ModelProvider
    context_window: int
    capabilities: List[ModelCapability]
    cost_per_1k_tokens: float = 0.0
    speed_score: float = 0.5
    quality_score: float = 0.5
    avg_latency_ms: int = 1000
    success_rate: float = 0.95


class ModelRegistry:
    """Registry of available models."""

    DEFAULT_MODELS = {
        "qwen2.5:7b": ModelInfo(
            model_id="qwen2.5:7b",
            name="Qwen 2.5 7B",
            provider=ModelProvider.OLLAMA,
            context_window=32768,
            capabilities=[ModelCapability.CODING, ModelCapability.FAST],
            cost_per_1k_tokens=0.0,
            speed_score=0.9,
            quality_score=0.8,
            avg_latency_ms=500,
        ),
        "qwen2.5:32b": ModelInfo(
            model_id="qwen2.5:32b",
            name="Qwen 2.5 32B",
            provider=ModelProvider.OLLAMA,
            context_window=32768,
            capabilities=[ModelCapability.CODING, ModelCapability.REASONING],
            cost_per_1k_tokens=0.0,
            speed_score=0.6,
            quality_score=0.9,
            avg_latency_ms=2000,
        ),
        "llama3.2:3b": ModelInfo(
            model_id="llama3.2:3b",
            name="Llama 3.2 3B",
            provider=ModelProvider.OLLAMA,
            context_window=128000,
            capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
            cost_per_1k_tokens=0.0,
            speed_score=0.95,
            quality_score=0.7,
            avg_latency_ms=300,
        ),
        "llama3.1:70b": ModelInfo(
            model_id="llama3.1:70b",
            name="Llama 3.1 70B",
            provider=ModelProvider.OLLAMA,
            context_window=128000,
            capabilities=[ModelCapability.REASONING, ModelCapability.LARGE_CONTEXT],
            cost_per_1k_tokens=0.0,
            speed_score=0.3,
            quality_score=0.95,
            avg_latency_ms=8000,
        ),
        "gpt-4o": ModelInfo(
            model_id="gpt-4o",
            name="GPT-4o",
            provider=ModelProvider.OPENAI,
            context_window=128000,
            capabilities=[
                ModelCapability.CODING,
                ModelCapability.REASONING,
                ModelCapability.MULTIMODAL,
            ],
            cost_per_1k_tokens=0.0025,
            speed_score=0.7,
            quality_score=0.95,
            avg_latency_ms=1500,
        ),
        "gpt-4o-mini": ModelInfo(
            model_id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider=ModelProvider.OPENAI,
            context_window=128000,
            capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
            cost_per_1k_tokens=0.00015,
            speed_score=0.95,
            quality_score=0.8,
            avg_latency_ms=200,
        ),
    }

    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default models."""
        self.models.update(self.DEFAULT_MODELS)

    def register_model(self, model: ModelInfo):
        """Register a model."""
        self.models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID."""
        return self.models.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        """List all models."""
        return list(self.models.values())

    def find_models(self, capability: ModelCapability) -> List[ModelInfo]:
        """Find models with capability."""
        return [m for m in self.models.values() if capability in m.capabilities]

    def get_cheapest(self, limit: int = 3) -> List[ModelInfo]:
        """Get cheapest models."""
        sorted_models = sorted(self.models.values(), key=lambda m: m.cost_per_1k_tokens)
        return sorted_models[:limit]

    def get_fastest(self, limit: int = 3) -> List[ModelInfo]:
        """Get fastest models."""
        return sorted(self.models.values(), key=lambda m: m.speed_score, reverse=True)[
            :limit
        ]

    def get_best_quality(self, limit: int = 3) -> List[ModelInfo]:
        """Get highest quality models."""
        return sorted(
            self.models.values(), key=lambda m: m.quality_score, reverse=True
        )[:limit]


def create_model_registry() -> ModelRegistry:
    """Factory function to create model registry."""
    return ModelRegistry()
