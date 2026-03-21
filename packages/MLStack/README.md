# MLStack

Local ML toolchain package for Alfred / BrowserV1.

## Purpose

This package groups the model-side dependencies you said you want next:

- `PyTorch`
- `TensorFlow`
- `ONNX`
- `ONNX Runtime`
- `LoRA / PEFT`
- `DSPy`
- dataset / acceleration helpers

It is not meant to replace your existing PakMan packages like:

- `LoRA`
- `benchmark_arena`
- `PromptOS`

It is the shared install surface that makes those packages easier to use together.

## Why this exists

You wanted a truthful way to start claiming ML-side tooling in the project:

1. create a clean package for the stack
2. install it
3. use it for real experiments
4. then turn that work into resume components

That is the defensible path.

## Included stack

- `torch`
- `tensorflow`
- `onnx`
- `onnxruntime`
- `onnxscript`
- `peft`
- `datasets`
- `accelerate`
- `safetensors`
- `dspy-ai`

## Not included

- `pickle`

Reason:
- `pickle` is part of Python stdlib already

## Suggested first uses

- model eval sandbox
- ONNX export / inference checks
- lightweight LoRA experiments
- DSPy prompt/program optimization
- field benchmark harness integration later

## Install

Recommended path: use Python `3.12` in a package-local virtual environment.

From this package folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

This creates:

```text
MLStack\.venv312\
```

Then runs a smoke test for:

- `torch`
- `tensorflow`
- `onnx`
- `onnxruntime`
- `peft`
- `datasets`
- `accelerate`
- `safetensors`
- `dspy`

Manual install if needed:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv312\Scripts\python -m pip install -r requirements.txt
.\.venv312\Scripts\python .\scripts\smoke_test.py
```

## Next practical step

After install, use the stack for one real project proof:

- PyTorch or TensorFlow mini experiment
- ONNX export or runtime inference
- DSPy or benchmark integration

Then extract that into:

- a skills block
- a project block
- one or two proof bullets

## Probe

There is now a lightweight proof module in:

- `probes/ml_stack_probe.py`

It exercises:

- `PyTorch`
- `TensorFlow`
- `ONNX Runtime`
- `DSPy`

Run it with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_probe.ps1
```

This gives you a concrete local artifact proving the stack is not just installed, but usable.

## What this stack enables

At this point, MLStack gives Semantica a local ML tool belt:

- tensor compute with `PyTorch` and `TensorFlow`
- ONNX export and local inference with `onnxruntime`
- adapter / LoRA-ready workflows through `peft`
- DSPy program optimization
- a clean place to build browser-side ML experiments without polluting the main app

Show the current capability manifest with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\show_capabilities.ps1
```

## Behavior learning

There is now a lightweight behavior-model scaffold in:

- `behavior_profile.py`

This is the path toward:

- learning from apply / save / skip behavior
- adapting job ranking from your habits
- training a user-side preference model without pretending we trained a foundation model

Run the demo with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_behavior_demo.ps1
```
