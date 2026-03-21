#!/usr/bin/env python3
# Updated-On: 2026-03-20
# Updated-By: Codex
"""
Lightweight user-side behavior model scaffold.

Goal:
- learn preference weights from browsing / apply / save / skip behavior
- stay small, transparent, and local
- provide a bridge between raw Semantica events and future model training
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(x, 40.0), -40.0)))


@dataclass
class PreferenceExample:
    features: dict[str, float]
    reward: float
    source: str = "manual"


@dataclass
class BehaviorProfile:
    learning_rate: float = 0.05
    bias: float = 0.0
    weights: dict[str, float] = field(default_factory=dict)
    event_count: int = 0

    def score(self, features: dict[str, float]) -> float:
        raw = self.bias
        for key, value in features.items():
            raw += self.weights.get(key, 0.0) * float(value)
        return _sigmoid(raw)

    def update(self, example: PreferenceExample) -> float:
        prediction = self.score(example.features)
        error = float(example.reward) - prediction
        self.bias += self.learning_rate * error
        for key, value in example.features.items():
            self.weights[key] = self.weights.get(key, 0.0) + self.learning_rate * error * float(value)
        self.event_count += 1
        return prediction

    def train(self, examples: Iterable[PreferenceExample], epochs: int = 1) -> int:
        seen = 0
        for _ in range(max(1, epochs)):
            for example in examples:
                self.update(example)
                seen += 1
        return seen

    def top_weights(self, limit: int = 12) -> list[tuple[str, float]]:
        return sorted(self.weights.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]

    def to_dict(self) -> dict:
        return {
            "learning_rate": self.learning_rate,
            "bias": self.bias,
            "weights": self.weights,
            "event_count": self.event_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BehaviorProfile":
        return cls(
            learning_rate=float(data.get("learning_rate", 0.05)),
            bias=float(data.get("bias", 0.0)),
            weights={str(k): float(v) for k, v in data.get("weights", {}).items()},
            event_count=int(data.get("event_count", 0)),
        )

    def save(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return output

    @classmethod
    def load(cls, path: str | Path) -> "BehaviorProfile":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def example_from_job_event(
    *,
    applied: bool = False,
    saved: bool = False,
    opened: bool = False,
    ai_role: bool = False,
    remote_canada: bool = False,
    public_sector: bool = False,
    fit_score: float = 0.0,
    priority: float = 0.0,
    source: str = "career_event",
) -> PreferenceExample:
    reward = 1.0 if applied else 0.7 if saved else 0.4 if opened else 0.0
    return PreferenceExample(
        features={
            "ai_role": 1.0 if ai_role else 0.0,
            "remote_canada": 1.0 if remote_canada else 0.0,
            "public_sector": 1.0 if public_sector else 0.0,
            "fit_score": float(fit_score) / 100.0,
            "priority": float(priority) / 100.0,
        },
        reward=reward,
        source=source,
    )


__all__ = ["BehaviorProfile", "PreferenceExample", "example_from_job_event"]
