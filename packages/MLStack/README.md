# MLStack

> **Status:** BETA | **Tags:** ml, pytorch, tensorflow, onnx, dspy, peft

## Overview
Shared ML environment: PyTorch, TensorFlow, ONNX, PEFT, DSPy, and accelerate. Installs to ~/.pakman/venvs/ml — shared across FieldBench and other consumers.

This package is a standalone module designed as a professional AI upgrade. It has been strictly refactored for independent execution and clean architecture, with zero cross-package dependencies.

## Installation
Provided through the `PakMan` package manager, or standard python tools if running standalone:
```bash
pakman install MLStack
```

## Architecture & Integration
- **Standalone:** This package does not rely on any other module in `packages/`.
- **Security:** Free of hard-coded secrets. Fully integrates into local AI workflows safely.

## Usage
Simply import the core components:
```python
import MLStack
# Integrate MLStack as needed in your stack.
```

---
*Generated centrally by PakMan Repository Management to ensure professional documentation standards.*
