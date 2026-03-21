#!/usr/bin/env python3
# Updated-On: 2026-03-20
# Updated-By: Codex
"""
Small proof module for the local ML stack.

This is intentionally lightweight:
- verifies PyTorch tensor ops
- verifies TensorFlow tensor ops
- exports a tiny ONNX graph
- runs ONNX Runtime inference
- verifies DSPy imports cleanly
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import onnxruntime as ort
import tensorflow as tf
import torch
from torch import nn

import dspy


class TinyLinear(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(2, 1)
        with torch.no_grad():
            self.linear.weight[:] = torch.tensor([[0.5, -0.25]])
            self.linear.bias[:] = torch.tensor([0.1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def run_probe() -> dict:
    model = TinyLinear().eval()
    sample = torch.tensor([[2.0, 4.0]], dtype=torch.float32)
    torch_output = model(sample).detach().numpy().round(6).tolist()

    tf_output = tf.matmul(
        tf.constant([[2.0, 4.0]], dtype=tf.float32),
        tf.constant([[0.5], [-0.25]], dtype=tf.float32),
    ) + tf.constant([[0.1]], dtype=tf.float32)
    tf_output = tf_output.numpy().round(6).tolist()

    tmp_dir = Path(__file__).resolve().parent / ".tmp_probe"
    tmp_dir.mkdir(exist_ok=True)
    onnx_path = tmp_dir / "tiny_linear.onnx"
    try:
        torch.onnx.export(
            model,
            sample,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
            opset_version=18,
            dynamo=False,
        )
        session = ort.InferenceSession(str(onnx_path))
        ort_output = session.run(
            None,
            {"input": np.array([[2.0, 4.0]], dtype=np.float32)},
        )[0].round(6).tolist()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return {
        "torch": torch_output,
        "tensorflow": tf_output,
        "onnxruntime": ort_output,
        "dspy_version": getattr(dspy, "__version__", "unknown"),
        "status": "ok",
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2))
