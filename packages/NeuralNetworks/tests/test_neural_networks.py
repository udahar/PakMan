"""Tests for neural_networks module."""
import pytest
import numpy as np
from neural_networks import (
    NeuralNetwork,
    DenseLayer,
    ReLU,
    Sigmoid,
    Tanh,
    Softmax,
    MSELoss,
    CrossEntropyLoss,
    SGD,
    Adam,
    build_classifier,
    build_regressor,
)


class TestActivationFunctions:
    """Test activation functions."""

    def test_relu(self):
        """Test ReLU activation."""
        relu = ReLU()
        x = np.array([[-1, 0, 1, 2]])
        out = relu.forward(x)
        assert out[0, 0] == 0
        assert out[0, 2] == 1
        assert out[0, 3] == 2

    def test_sigmoid(self):
        """Test Sigmoid activation."""
        sigmoid = Sigmoid()
        x = np.array([[0]])
        out = sigmoid.forward(x)
        assert 0.4 < out[0, 0] < 0.6

    def test_tanh(self):
        """Test Tanh activation."""
        tanh = Tanh()
        x = np.array([[0]])
        out = tanh.forward(x)
        assert abs(out[0, 0]) < 0.1

    def test_softmax(self):
        """Test Softmax activation."""
        softmax = Softmax()
        x = np.array([[1, 2, 3]])
        out = softmax.forward(x)
        assert abs(np.sum(out) - 1) < 1e-6
        assert np.all(out > 0)


class TestDenseLayer:
    """Test DenseLayer."""

    def test_forward(self):
        """Test forward pass."""
        layer = DenseLayer(input_size=3, output_size=2)
        x = np.array([[1, 2, 3]])
        out = layer.forward(x)
        assert out.shape == (1, 2)

    def test_backward(self):
        """Test backward pass."""
        layer = DenseLayer(input_size=3, output_size=2)
        x = np.array([[1, 2, 3]])
        layer.forward(x)
        grad = np.array([[1, 1]])
        out = layer.backward(grad)
        assert out.shape == x.shape


class TestLossFunctions:
    """Test loss functions."""

    def test_mse_loss(self):
        """Test MSE loss."""
        loss_fn = MSELoss()
        y_pred = np.array([[1, 2, 3]])
        y_true = np.array([[1, 2, 4]])
        loss = loss_fn.forward(y_pred, y_true)
        assert loss > 0

    def test_cross_entropy_loss(self):
        """Test cross-entropy loss."""
        loss_fn = CrossEntropyLoss()
        y_pred = np.array([[0.7, 0.3], [0.2, 0.8]])
        y_true = np.array([[1, 0], [0, 1]])
        loss = loss_fn.forward(y_pred, y_true)
        assert loss > 0


class TestOptimizers:
    """Test optimizers."""

    def test_sgd_step(self):
        """Test SGD step."""
        optimizer = SGD(lr=0.01)
        layer = DenseLayer(input_size=2, output_size=2)
        layers = [layer]
        optimizer.step(layers)

    def test_adam_step(self):
        """Test Adam step."""
        optimizer = Adam(lr=0.001)
        layer = DenseLayer(input_size=2, output_size=2)
        layers = [layer]
        optimizer.step(layers)


class TestNeuralNetwork:
    """Test NeuralNetwork."""

    def test_add_layer(self):
        """Test adding layers."""
        nn = NeuralNetwork()
        nn.add(DenseLayer(2, 4))
        nn.add(ReLU())
        assert len(nn.layers) == 2

    def test_forward(self):
        """Test forward pass."""
        nn = NeuralNetwork()
        nn.add(DenseLayer(2, 4))
        nn.add(ReLU())
        x = np.array([[1, 2]])
        out = nn.forward(x)
        assert out.shape == (1, 4)

    def test_train(self):
        """Test training."""
        nn = NeuralNetwork()
        nn.add(DenseLayer(2, 4))
        nn.add(ReLU())
        nn.add(DenseLayer(4, 1))
        nn.add(Sigmoid())

        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
        y = np.array([[0], [1], [1], [0]], dtype=float)

        nn.compile(loss=MSELoss(), optimizer=SGD(lr=0.1))
        history = nn.train(X, y, epochs=10, verbose=False)
        assert "loss" in history

    def test_predict(self):
        """Test prediction."""
        nn = NeuralNetwork()
        nn.add(DenseLayer(2, 1))
        X = np.array([[1, 2]])
        pred = nn.predict(X)
        assert pred.shape == (1, 1)


class TestBuildFunctions:
    """Test builder functions."""

    def test_build_classifier(self):
        """Test classifier builder."""
        nn = build_classifier(input_size=10, hidden_sizes=[8, 4], num_classes=3)
        assert len(nn.layers) > 0

    def test_build_regressor(self):
        """Test regressor builder."""
        nn = build_regressor(input_size=5, hidden_sizes=[4], output_size=1)
        assert len(nn.layers) > 0
