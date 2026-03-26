"""
Learning Types Module

Implements the three fundamental ML paradigms:
- Supervised Learning (classification, regression with labeled data)
- Unsupervised Learning (clustering, dimensionality reduction)
- Reinforcement Learning (agent learning from rewards)

Based on learning types spec: "supervised, unsupervised, reinforcement"

Usage:
    from modules.learning_types import SupervisedLearner, KMeansClusterer, QLearningAgent
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================
# SUPERVISED LEARNING
# ============================================================


class SupervisedLearner:
    """
    Generic supervised learning wrapper.

    Supports any model with fit/predict interface.
    Includes linear regression, logistic regression, and decision tree built-in.

    Usage:
        learner = SupervisedLearner(model_type='linear')
        learner.fit(X_train, y_train)
        predictions = learner.predict(X_test)
    """

    def __init__(self, model_type: str = "linear", **kwargs):
        logger.debug(f"Initializing SupervisedLearner with model_type={model_type}")
        self.model_type = model_type
        self.model = None
        self._kwargs = kwargs
        self._build_model()

    def _build_model(self):
        if self.model_type == "linear":
            self.model = LinearRegression(**self._kwargs)
        elif self.model_type == "logistic":
            self.model = LogisticRegression(**self._kwargs)
        elif self.model_type == "tree":
            self.model = DecisionTree(**self._kwargs)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def fit(self, X: np.ndarray, y: np.ndarray):
        logger.debug(f"Fitting {self.model_type} model on {len(X)} samples")
        self.model.fit(X, y)
        logger.info(f"{self.model_type} model fitted successfully")

    def predict(self, X: np.ndarray) -> np.ndarray:
        logger.debug(f"Predicting {len(X)} samples")
        return self.model.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        y_pred = self.predict(X)
        if self.model_type == "linear":
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            return 1 - ss_res / ss_tot if ss_tot > 0 else 0
        else:
            return np.mean(y_pred == y)


class LinearRegression:
    """Ordinary Least Squares linear regression."""

    def __init__(self):
        self.weights = None
        self.bias = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        # Add bias column
        X_b = np.column_stack([np.ones(X.shape[0]), X])
        # Normal equation: w = (X^T X)^-1 X^T y
        self.weights = np.linalg.lstsq(X_b, y, rcond=None)[0]
        self.bias = self.weights[0]
        self.weights = self.weights[1:]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return X @ self.weights + self.bias


class LogisticRegression:
    """Logistic regression via gradient descent."""

    def __init__(self, lr: float = 0.01, epochs: int = 1000):
        self.lr = lr
        self.epochs = epochs
        self.weights = None
        self.bias = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray):
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        for _ in range(self.epochs):
            z = X @ self.weights + self.bias
            predictions = 1 / (1 + np.exp(-np.clip(z, -500, 500)))

            dw = (1 / n_samples) * X.T @ (predictions - y)
            db = (1 / n_samples) * np.sum(predictions - y)

            self.weights -= self.lr * dw
            self.bias -= self.lr * db

    def predict(self, X: np.ndarray) -> np.ndarray:
        z = X @ self.weights + self.bias
        probs = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
        return (probs >= 0.5).astype(int)


class DecisionTree:
    """Simple decision tree classifier (CART algorithm)."""

    def __init__(self, max_depth: int = 10, min_samples_split: int = 2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.tree = self._build(X, y, depth=0)

    def _gini(self, y: np.ndarray) -> float:
        classes, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1 - np.sum(probs**2)

    def _build(self, X: np.ndarray, y: np.ndarray, depth: int) -> dict:
        n_samples = len(y)
        n_classes = len(np.unique(y))

        # Stopping conditions
        if (
            depth >= self.max_depth
            or n_classes == 1
            or n_samples < self.min_samples_split
        ):
            classes, counts = np.unique(y, return_counts=True)
            return {"leaf": True, "class": classes[np.argmax(counts)]}

        best_gain = -1
        best_feature, best_threshold = 0, 0

        parent_gini = self._gini(y)

        for feature in range(X.shape[1]):
            thresholds = np.unique(X[:, feature])
            for threshold in thresholds:
                left_mask = X[:, feature] <= threshold
                right_mask = ~left_mask

                if left_mask.sum() == 0 or right_mask.sum() == 0:
                    continue

                gain = parent_gini - (
                    left_mask.sum() / n_samples * self._gini(y[left_mask])
                    + right_mask.sum() / n_samples * self._gini(y[right_mask])
                )

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold

        if best_gain <= 0:
            classes, counts = np.unique(y, return_counts=True)
            return {"leaf": True, "class": classes[np.argmax(counts)]}

        left_mask = X[:, best_feature] <= best_threshold
        return {
            "leaf": False,
            "feature": best_feature,
            "threshold": best_threshold,
            "left": self._build(X[left_mask], y[left_mask], depth + 1),
            "right": self._build(X[~left_mask], y[~left_mask], depth + 1),
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_one(x, self.tree) for x in X])

    def _predict_one(self, x: np.ndarray, node: dict):
        if node["leaf"]:
            return node["class"]
        if x[node["feature"]] <= node["threshold"]:
            return self._predict_one(x, node["left"])
        return self._predict_one(x, node["right"])


# ============================================================
# UNSUPERVISED LEARNING
# ============================================================


class KMeansClusterer:
    """
    K-Means clustering.

    Usage:
        km = KMeansClusterer(n_clusters=3)
        km.fit(X)
        labels = km.predict(X)
        centers = km.centroids
    """

    def __init__(self, n_clusters: int = 3, max_iters: int = 100, tol: float = 1e-4):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.tol = tol
        self.centroids = None

    def fit(self, X: np.ndarray) -> "KMeansClusterer":
        logger.info(f"Fitting KMeans with {self.n_clusters} clusters on {len(X)} samples")
        n_samples = X.shape[0]

        indices = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.centroids = X[indices].copy()

        for iteration in range(self.max_iters):
            distances = self._compute_distances(X)
            labels = np.argmin(distances, axis=1)

            new_centroids = np.array(
                [
                    X[labels == k].mean(axis=0)
                    if np.sum(labels == k) > 0
                    else self.centroids[k]
                    for k in range(self.n_clusters)
                ]
            )

            if np.sum(np.abs(new_centroids - self.centroids)) < self.tol:
                logger.debug(f"KMeans converged at iteration {iteration + 1}")
                break

            self.centroids = new_centroids

        logger.info("KMeans fitting complete")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        distances = self._compute_distances(X)
        return np.argmin(distances, axis=1)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.predict(X)

    def _compute_distances(self, X: np.ndarray) -> np.ndarray:
        distances = np.zeros((X.shape[0], self.n_clusters))
        for k in range(self.n_clusters):
            distances[:, k] = np.sum((X - self.centroids[k]) ** 2, axis=1)
        return distances

    def inertia(self, X: np.ndarray) -> float:
        """Sum of squared distances to nearest centroid."""
        labels = self.predict(X)
        return sum(
            np.sum((X[labels == k] - self.centroids[k]) ** 2)
            for k in range(self.n_clusters)
            if np.sum(labels == k) > 0
        )


class PCAReducer:
    """
    Principal Component Analysis for dimensionality reduction.

    Usage:
        pca = PCARucuer(n_components=2)
        X_reduced = pca.fit_transform(X)
    """

    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self.components = None
        self.mean = None
        self.explained_variance_ratio = None

    def fit(self, X: np.ndarray) -> "PCAReducer":
        self.mean = np.mean(X, axis=0)
        X_centered = X - self.mean

        # Covariance matrix
        cov = np.cov(X_centered, rowvar=False)

        # Eigen decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Sort by eigenvalue descending
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        self.components = eigenvectors[:, : self.n_components]
        self.explained_variance_ratio = eigenvalues[: self.n_components] / np.sum(
            eigenvalues
        )

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_centered = X - self.mean
        return X_centered @ self.components

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X_reduced: np.ndarray) -> np.ndarray:
        return X_reduced @ self.components.T + self.mean


# ============================================================
# REINFORCEMENT LEARNING
# ============================================================


class QLearningAgent:
    """
    Q-Learning agent for tabular environments.

    Learns optimal actions through trial and error with reward signals.

    Usage:
        agent = QLearningAgent(n_states=100, n_actions=4)

        for episode in range(1000):
            state = env.reset()
            done = False
            while not done:
                action = agent.act(state)
                next_state, reward, done = env.step(action)
                agent.learn(state, action, reward, next_state, done)
                state = next_state

    Args:
        n_states: Number of states
        n_actions: Number of actions
        lr: Learning rate (alpha)
        gamma: Discount factor
        epsilon: Exploration rate
        epsilon_decay: Epsilon decay per episode
        epsilon_min: Minimum epsilon
    """

    def __init__(
        self,
        n_states: int,
        n_actions: int,
        lr: float = 0.1,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = np.zeros((n_states, n_actions))

    def act(self, state: int, training: bool = True) -> int:
        """Choose action using epsilon-greedy policy."""
        if training and np.random.rand() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def learn(
        self, state: int, action: int, reward: float, next_state: int, done: bool
    ):
        """Update Q-table from experience."""
        target = reward
        if not done:
            target += self.gamma * np.max(self.q_table[next_state])

        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])

    def end_episode(self):
        """Decay exploration rate after each episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def get_policy(self) -> np.ndarray:
        """Get optimal policy (best action per state)."""
        return np.argmax(self.q_table, axis=1)

    def get_value_function(self) -> np.ndarray:
        """Get state value function (max Q per state)."""
        return np.max(self.q_table, axis=1)


class SARSAAgent:
    """
    SARSA agent — on-policy reinforcement learning.

    Similar to Q-Learning but uses the actual next action for updates.
    """

    def __init__(
        self,
        n_states: int,
        n_actions: int,
        lr: float = 0.1,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = np.zeros((n_states, n_actions))

    def act(self, state: int, training: bool = True) -> int:
        if training and np.random.rand() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def learn(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
        next_action: int,
        done: bool,
    ):
        """Update Q-table using SARSA rule."""
        target = reward
        if not done:
            target += self.gamma * self.q_table[next_state, next_action]

        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])

    def end_episode(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


class MultiArmedBandit:
    """
    Multi-armed bandit for exploration/exploitation problems.

    Uses Upper Confidence Bound (UCB) algorithm.

    Usage:
        bandit = MultiArmedBandit(n_arms=10)
        for t in range(1000):
            arm = bandit.select_arm()
            reward = environment.pull(arm)
            bandit.update(arm, reward)
    """

    def __init__(self, n_arms: int, c: float = 2.0):
        self.n_arms = n_arms
        self.c = c
        self.counts = np.zeros(n_arms)
        self.values = np.zeros(n_arms)
        self.total_pulls = 0

    def select_arm(self) -> int:
        """Select arm using UCB1 algorithm."""
        # Play each arm at least once
        for arm in range(self.n_arms):
            if self.counts[arm] == 0:
                return arm

        # UCB1
        ucb_values = self.values + self.c * np.sqrt(
            np.log(self.total_pulls) / self.counts
        )
        return int(np.argmax(ucb_values))

    def update(self, arm: int, reward: float):
        """Update arm statistics."""
        self.counts[arm] += 1
        self.total_pulls += 1
        n = self.counts[arm]
        self.values[arm] += (reward - self.values[arm]) / n

    def get_best_arm(self) -> int:
        """Get the arm with highest estimated value."""
        return int(np.argmax(self.values))
