#!/usr/bin/env python3
# Updated-On: 2026-03-20
# Updated-By: Codex
"""
Capability manifest for the local ML stack.
"""

from __future__ import annotations

from typing import Any


def get_capabilities() -> dict[str, Any]:
    return {
        "name": "MLStack",
        "purpose": "Local ML tooling for Semantica / BrowserV1 / PromptOS.",
        "capabilities": [
            {
                "id": "tensor_compute",
                "label": "Tensor compute",
                "tools": ["torch", "tensorflow"],
                "examples": [
                    "vector and tensor math",
                    "small local model experiments",
                    "feature/probe development",
                ],
            },
            {
                "id": "onnx_export_runtime",
                "label": "ONNX export and runtime",
                "tools": ["torch", "onnx", "onnxscript", "onnxruntime"],
                "examples": [
                    "export a small model to ONNX",
                    "run local inference through ONNX Runtime",
                    "compare outputs across runtimes",
                ],
            },
            {
                "id": "adapter_finetuning",
                "label": "Adapter / LoRA-ready workflows",
                "tools": ["peft", "accelerate", "datasets", "safetensors"],
                "examples": [
                    "adapter-style tuning experiments",
                    "dataset handling",
                    "checkpoint and artifact workflows",
                ],
            },
            {
                "id": "dspy_programming",
                "label": "DSPy program optimization",
                "tools": ["dspy-ai"],
                "examples": [
                    "prompt/program optimization",
                    "evaluation loops",
                    "benchmark-style orchestration",
                ],
            },
            {
                "id": "browser_ml",
                "label": "ML-capable browser workflows",
                "tools": ["all"],
                "examples": [
                    "ATS requirement-to-component ranking experiments",
                    "semantic retrieval evaluation",
                    "model-backed local scoring or reranking",
                ],
            },
            {
                "id": "behavior_learning",
                "label": "Behavior learning scaffold",
                "tools": ["torch", "datasets"],
                "examples": [
                    "learn job-interest weights from apply/save/skip events",
                    "adapt career ranking from your browsing habits",
                    "build a user-side preference model without training a full LLM",
                ],
            },
        ],
        "not_yet": [
            "full training pipeline",
            "GPU-specific tuning",
            "production model serving",
        ],
    }


__all__ = ["get_capabilities"]
