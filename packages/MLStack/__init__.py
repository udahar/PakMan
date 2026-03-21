#!/usr/bin/env python3
# Updated-On: 2026-03-20
# Updated-By: Codex
# PM-Ticket: UNTRACKED
"""
MLStack - local model tooling stack for Alfred / BrowserV1 work.

Purpose:
- keep the PyTorch / TensorFlow / ONNX / LoRA toolchain in one PakMan package
- make future installs predictable
- give resume-proof package structure for local ML experimentation
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"
CONFIG_DIR = PACKAGE_ROOT / "config"
VENV_DIR = PACKAGE_ROOT / ".venv312"
PROBES_DIR = PACKAGE_ROOT / "probes"

STACK_COMPONENTS = [
    "torch",
    "tensorflow",
    "onnx",
    "onnxruntime",
    "onnxscript",
    "peft",
    "datasets",
    "accelerate",
    "safetensors",
    "dspy-ai",
]


def package_info() -> dict:
    return {
        "name": "MLStack",
        "version": __version__,
        "root": str(PACKAGE_ROOT),
        "venv": str(VENV_DIR),
        "probes": str(PROBES_DIR),
        "components": list(STACK_COMPONENTS),
        "notes": [
            "pickle is Python stdlib and does not need pip install",
            "LoRA package already exists in PakMan and can be composed with this stack",
            "FieldBench can be added once its exact package source is locked",
        ],
    }


__all__ = [
    "PACKAGE_ROOT",
    "SCRIPTS_DIR",
    "CONFIG_DIR",
    "PROBES_DIR",
    "VENV_DIR",
    "STACK_COMPONENTS",
    "package_info",
]
__version__ = "0.1.0"
