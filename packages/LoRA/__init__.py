"""LoRA — Low-Rank Adaptation training utilities for fine-tuning local models."""

__version__ = "0.1.0"

import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"

def get_train_script():
    return str(SCRIPTS_DIR / "train_lora.py")

def get_inference_script():
    return str(SCRIPTS_DIR / "inference_lora.py")

def get_extract_script():
    return str(SCRIPTS_DIR / "extract_training_data.py")

__all__ = [
    "PACKAGE_ROOT",
    "SCRIPTS_DIR",
    "get_train_script",
    "get_inference_script",
    "get_extract_script",
]
