"""
Neural Networks Module

Build neural networks from scratch — no GPU, no TensorFlow, no PyTorch.
Pure Python + NumPy implementation.

Based on NeuralNetwork.txt spec: "Make a neural network without data, without a GPU"

Includes:
- Dense (fully connected) layers
- Activation functions (ReLU, Sigmoid, Tanh, Softmax)
- Loss functions (MSE, Cross-Entropy)
- Backpropagation
- SGD and Adam optimizers
- Mini-batch training

Usage:
    from modules.neural_networks import NeuralNetwork, DenseLayer, ReLU, Sigmoid

    # Build a network
    nn = NeuralNetwork()
    nn.add(DenseLayer(input_size=2, output_size=16))
    nn.add(ReLU())
    nn.add(DenseLayer(input_size=16, output_size=8))
    nn.add(ReLU())
    nn.add(DenseLayer(input_size=8, output_size=1))
    nn.add(Sigmoid())

    # Train on XOR
    X = np.array([[0,0],[0,1],[1,0],[1,1]])
    y = np.array([[0],[1],[1],[0]])
    nn.train(X, y, epochs=1000, lr=0.1)

    # Predict
    print(nn.predict(np.array([[1,0]])))  # ~[1]
"""

import logging
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================
# Activation Functions
# ============================================================


class Activation:
    """Base activation function."""

    def forward(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def backward(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class ReLU(Activation):
    """Rectified Linear Unit: max(0, x)"""

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._last_input = x
        return np.maximum(0, x)

    def backward(self, grad: np.ndarray) -> np.ndarray:
        return grad * (self._last_input > 0)


class Sigmoid(Activation):
    """Sigmoid: 1 / (1 + exp(-x))"""

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._output = 1 / (1 + np.exp(-np.clip(x, -500, 500)))
        return self._output

    def backward(self, grad: np.ndarray) -> np.ndarray:
        return grad * self._output * (1 - self._output)


class Tanh(Activation):
    """Hyperbolic tangent."""

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._output = np.tanh(x)
        return self._output

    def backward(self, grad: np.ndarray) -> np.ndarray:
        return grad * (1 - self._output**2)


class Softmax(Activation):
    """Softmax for multi-class classification."""

    def forward(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        self._output = exp_x / np.sum(exp_x, axis=-1, keepdims=True)
        return self._output

    def backward(self, grad: np.ndarray) -> np.ndarray:
        # Simplified: assumes grad is already dL/dz from cross-entropy
        return grad


# ============================================================
# Layers
# ============================================================


class Layer:
    """Base layer."""

    def forward(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def backward(self, grad: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def get_params(self) -> Dict[str, np.ndarray]:
        return {}

    def set_params(self, params: Dict[str, np.ndarray]):
        pass


class DenseLayer(Layer):
    """
    Fully connected layer with Xavier initialization.

    Args:
        input_size: Number of input features
        output_size: Number of output features
        bias: Whether to include bias term
    """

    def __init__(self, input_size: int, output_size: int, bias: bool = True):
        # Xavier initialization
        scale = np.sqrt(2.0 / (input_size + output_size))
        self.weights = np.random.randn(input_size, output_size) * scale
        self.bias_enabled = bias
        self.bias = np.zeros((1, output_size)) if bias else None

        # Gradients
        self.dweights = np.zeros_like(self.weights)
        self.dbias = np.zeros_like(self.bias) if bias else None
        self._last_input = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._last_input = x
        out = x @ self.weights
        if self.bias_enabled:
            out = out + self.bias
        return out

    def backward(self, grad: np.ndarray) -> np.ndarray:
        self.dweights = self._last_input.T @ grad
        if self.bias_enabled:
            self.dbias = np.sum(grad, axis=0, keepdims=True)
        return grad @ self.weights.T

    def get_params(self) -> Dict[str, np.ndarray]:
        p = {"weights": self.weights}
        if self.bias_enabled:
            p["bias"] = self.bias
        return p

    def set_params(self, params: Dict[str, np.ndarray]):
        self.weights = params["weights"]
        if "bias" in params and self.bias_enabled:
            self.bias = params["bias"]


class Dropout(Layer):
    """Dropout regularization layer."""

    def __init__(self, rate: float = 0.5):
        self.rate = rate
        self._mask = None
        self._training = True

    def forward(self, x: np.ndarray) -> np.ndarray:
        if not self._training:
            return x
        self._mask = (np.random.rand(*x.shape) > self.rate) / (1 - self.rate)
        return x * self._mask

    def backward(self, grad: np.ndarray) -> np.ndarray:
        if not self._training:
            return grad
        return grad * self._mask

    def train(self):
        self._training = True

    def eval(self):
        self._training = False


# ============================================================
# Loss Functions
# ============================================================


class Loss:
    """Base loss function."""

    def forward(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        raise NotImplementedError

    def backward(self, y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class MSELoss(Loss):
    """Mean Squared Error: mean((y_pred - y_true)^2)"""

    def forward(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        return np.mean((y_pred - y_true) ** 2)

    def backward(self, y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
        return 2 * (y_pred - y_true) / y_true.shape[0]


class CrossEntropyLoss(Loss):
    """Cross-Entropy Loss for classification."""

    def forward(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        eps = 1e-12
        y_pred = np.clip(y_pred, eps, 1 - eps)
        if y_true.ndim == 1 or y_true.shape[1] == 1:
            # Binary
            return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        else:
            # Multi-class
            return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))

    def backward(self, y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
        eps = 1e-12
        y_pred = np.clip(y_pred, eps, 1 - eps)
        if y_true.ndim == 1 or y_true.shape[1] == 1:
            return -(y_true / y_pred - (1 - y_true) / (1 - y_pred)) / y_true.shape[0]
        else:
            return -y_true / y_pred / y_true.shape[0]


# ============================================================
# Optimizers
# ============================================================


class Optimizer:
    """Base optimizer."""

    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def step(self, layers: List[Layer]):
        raise NotImplementedError


class SGD(Optimizer):
    """Stochastic Gradient Descent with optional momentum."""

    def __init__(self, lr: float = 0.01, momentum: float = 0.0):
        super().__init__(lr)
        self.momentum = momentum
        self._velocities = {}

    def step(self, layers: List[Layer]):
        for i, layer in enumerate(layers):
            if not isinstance(layer, DenseLayer):
                continue

            if i not in self._velocities:
                self._velocities[i] = {
                    "w": np.zeros_like(layer.weights),
                    "b": np.zeros_like(layer.bias) if layer.bias_enabled else None,
                }

            v = self._velocities[i]
            v["w"] = self.momentum * v["w"] - self.lr * layer.dweights
            layer.weights = layer.weights + v["w"]

            if layer.bias_enabled and layer.dbias is not None:
                v["b"] = self.momentum * v["b"] - self.lr * layer.dbias
                layer.bias = layer.bias + v["b"]


class Adam(Optimizer):
    """Adam optimizer."""

    def __init__(
        self,
        lr: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ):
        super().__init__(lr)
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self._m = {}
        self._v = {}
        self._t = 0

    def step(self, layers: List[Layer]):
        self._t += 1

        for i, layer in enumerate(layers):
            if not isinstance(layer, DenseLayer):
                continue

            if i not in self._m:
                self._m[i] = {
                    "w": np.zeros_like(layer.weights),
                    "b": np.zeros_like(layer.bias) if layer.bias_enabled else None,
                }
                self._v[i] = {
                    "w": np.zeros_like(layer.weights),
                    "b": np.zeros_like(layer.bias) if layer.bias_enabled else None,
                }

            # Weights
            self._m[i]["w"] = (
                self.beta1 * self._m[i]["w"] + (1 - self.beta1) * layer.dweights
            )
            self._v[i]["w"] = (
                self.beta2 * self._v[i]["w"] + (1 - self.beta2) * layer.dweights**2
            )
            m_hat = self._m[i]["w"] / (1 - self.beta1**self._t)
            v_hat = self._v[i]["w"] / (1 - self.beta2**self._t)
            layer.weights = layer.weights - self.lr * m_hat / (
                np.sqrt(v_hat) + self.eps
            )

            # Bias
            if layer.bias_enabled and layer.dbias is not None:
                self._m[i]["b"] = (
                    self.beta1 * self._m[i]["b"] + (1 - self.beta1) * layer.dbias
                )
                self._v[i]["b"] = (
                    self.beta2 * self._v[i]["b"] + (1 - self.beta2) * layer.dbias**2
                )
                m_hat_b = self._m[i]["b"] / (1 - self.beta1**self._t)
                v_hat_b = self._v[i]["b"] / (1 - self.beta2**self._t)
                layer.bias = layer.bias - self.lr * m_hat_b / (
                    np.sqrt(v_hat_b) + self.eps
                )


# ============================================================
# Neural Network
# ============================================================


class NeuralNetwork:
    """
    Build and train a neural network from scratch.

    Usage:
        nn = NeuralNetwork()
        nn.add(DenseLayer(2, 16))
        nn.add(ReLU())
        nn.add(DenseLayer(16, 1))
        nn.add(Sigmoid())

        nn.compile(loss=MSELoss(), optimizer=SGD(lr=0.1))
        history = nn.train(X, y, epochs=500)
        predictions = nn.predict(X_test)
    """

    def __init__(self):
        logger.info("Initializing NeuralNetwork")
        self.layers: List[Layer] = []
        self.loss_fn: Loss = MSELoss()
        self.optimizer: Optimizer = SGD()
        self.history: Dict[str, List[float]] = {"loss": []}

    def add(self, layer: Layer) -> "NeuralNetwork":
        """Add a layer to the network."""
        self.layers.append(layer)
        return self

    def compile(self, loss: Loss = None, optimizer: Optimizer = None):
        """Configure loss and optimizer."""
        if loss:
            self.loss_fn = loss
        if optimizer:
            self.optimizer = optimizer

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through all layers."""
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, grad: np.ndarray):
        """Backward pass through all layers (reversed)."""
        for layer in reversed(self.layers):
            grad = layer.backward(grad)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        lr: float = None,
        batch_size: int = None,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """
        Train the network.

        Args:
            X: Input data (n_samples, n_features)
            y: Target data (n_samples, n_outputs)
            epochs: Number of training epochs
            lr: Learning rate (overrides optimizer lr)
            batch_size: Mini-batch size (None = full batch)
            verbose: Print progress

        Returns:
            Training history dict with 'loss' key
        """
        if lr:
            self.optimizer.lr = lr

        n_samples = X.shape[0]
        if batch_size is None:
            batch_size = n_samples

        self.history = {"loss": []}
        logger.info(f"Training for {epochs} epochs, batch_size={batch_size}")

        for epoch in range(epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_idx = indices[start:end]
                X_batch = X[batch_idx]
                y_batch = y[batch_idx]

                # Forward
                y_pred = self.forward(X_batch)

                # Loss
                loss = self.loss_fn.forward(y_pred, y_batch)
                epoch_loss += loss
                n_batches += 1

                # Backward
                grad = self.loss_fn.backward(y_pred, y_batch)
                self.backward(grad)

                # Update
                self.optimizer.step(self.layers)

            avg_loss = epoch_loss / n_batches
            self.history["loss"].append(avg_loss)

            if verbose and (epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1):
                logger.debug(f"Epoch {epoch + 1}/{epochs} - loss: {avg_loss:.6f}")

        logger.info(f"Training complete. Final loss: {self.history['loss'][-1]:.6f}")
        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.forward(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate on test data."""
        y_pred = self.predict(X)
        loss = self.loss_fn.forward(y_pred, y)

        metrics = {"loss": loss}

        # Accuracy for classification
        if y_pred.shape[1] > 1:
            preds = np.argmax(y_pred, axis=1)
            true = np.argmax(y, axis=1) if y.ndim > 1 else y
            metrics["accuracy"] = np.mean(preds == true)
        elif np.all((y_pred >= 0) & (y_pred <= 1)):
            preds = (y_pred > 0.5).astype(int)
            metrics["accuracy"] = np.mean(preds == y)

        return metrics

    def save(self, filepath: str):
        """Save network weights to file."""
        import pickle

        data = {
            "params": [layer.get_params() for layer in self.layers],
            "layer_types": [type(layer).__name__ for layer in self.layers],
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filepath: str):
        """Load network weights from file."""
        import pickle

        with open(filepath, "rb") as f:
            data = pickle.load(f)
        for layer, params in zip(self.layers, data["params"]):
            if params:
                layer.set_params(params)


# Convenience builders
def build_classifier(
    input_size: int, hidden_sizes: List[int], num_classes: int
) -> NeuralNetwork:
    """Build a classification network."""
    nn = NeuralNetwork()

    prev = input_size
    for h in hidden_sizes:
        nn.add(DenseLayer(prev, h))
        nn.add(ReLU())
        prev = h

    nn.add(DenseLayer(prev, num_classes))
    nn.add(Softmax())
    nn.compile(loss=CrossEntropyLoss(), optimizer=Adam())

    return nn


def build_regressor(
    input_size: int, hidden_sizes: List[int], output_size: int = 1
) -> NeuralNetwork:
    """Build a regression network."""
    nn = NeuralNetwork()

    prev = input_size
    for h in hidden_sizes:
        nn.add(DenseLayer(prev, h))
        nn.add(ReLU())
        prev = h

    nn.add(DenseLayer(prev, output_size))
    nn.compile(loss=MSELoss(), optimizer=Adam())

    return nn
