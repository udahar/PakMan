"""Tests for learning_types module."""
import pytest
import numpy as np
from learning_types import (
    SupervisedLearner,
    LinearRegression,
    LogisticRegression,
    DecisionTree,
    KMeansClusterer,
    PCAReducer,
    QLearningAgent,
    SARSAAgent,
    MultiArmedBandit,
)


class TestSupervisedLearner:
    """Test SupervisedLearner."""

    def test_fit_linear(self):
        """Test linear regression fitting."""
        learner = SupervisedLearner(model_type="linear")
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])
        learner.fit(X, y)
        assert learner.model is not None

    def test_predict(self):
        """Test prediction."""
        learner = SupervisedLearner(model_type="linear")
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])
        learner.fit(X, y)
        pred = learner.predict(np.array([[7]]))
        assert pred.shape == (1,)


class TestLinearRegression:
    """Test LinearRegression."""

    def test_fit(self):
        """Test linear regression fitting."""
        model = LinearRegression()
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])
        model.fit(X, y)
        assert model.weights is not None

    def test_predict(self):
        """Test prediction."""
        model = LinearRegression()
        X = np.array([[1], [2], [3]])
        y = np.array([1, 2, 3])
        model.fit(X, y)
        pred = model.predict(np.array([[4]]))
        assert pred[0] > 0


class TestLogisticRegression:
    """Test LogisticRegression."""

    def test_fit(self):
        """Test logistic regression fitting."""
        model = LogisticRegression(epochs=100)
        X = np.array([[1, 2], [2, 1], [3, 4], [4, 3]])
        y = np.array([0, 0, 1, 1])
        model.fit(X, y)
        assert model.weights is not None

    def test_predict(self):
        """Test binary prediction."""
        model = LogisticRegression(epochs=50)
        X = np.array([[1, 2], [2, 1], [3, 4], [4, 3]])
        y = np.array([0, 0, 1, 1])
        model.fit(X, y)
        pred = model.predict(X)
        assert pred.shape == y.shape


class TestDecisionTree:
    """Test DecisionTree."""

    def test_fit(self):
        """Test decision tree fitting."""
        tree = DecisionTree(max_depth=3)
        X = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
        y = np.array([0, 1, 1, 0])
        tree.fit(X, y)
        assert tree.tree is not None

    def test_predict(self):
        """Test prediction."""
        tree = DecisionTree()
        X = np.array([[1, 0], [0, 1]])
        y = np.array([0, 1])
        tree.fit(X, y)
        pred = tree.predict(X)
        assert len(pred) == len(y)


class TestKMeansClusterer:
    """Test KMeansClusterer."""

    def test_fit(self):
        """Test KMeans fitting."""
        km = KMeansClusterer(n_clusters=2)
        X = np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])
        km.fit(X)
        assert km.centroids is not None

    def test_predict(self):
        """Test cluster prediction."""
        km = KMeansClusterer(n_clusters=2)
        X = np.array([[1, 2], [1, 4], [10, 2], [10, 4]])
        km.fit(X)
        labels = km.predict(X)
        assert len(labels) == len(X)
        assert set(labels).issubset({0, 1})

    def test_fit_predict(self):
        """Test fit_predict."""
        km = KMeansClusterer(n_clusters=2)
        X = np.array([[1, 2], [10, 2]])
        labels = km.fit_predict(X)
        assert len(labels) == len(X)


class TestPCAReducer:
    """Test PCAReducer."""

    def test_fit_transform(self):
        """Test PCA fit_transform."""
        pca = PCAReducer(n_components=2)
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
        result = pca.fit_transform(X)
        assert result.shape[1] == 2

    def test_inverse_transform(self):
        """Test inverse transform."""
        pca = PCAReducer(n_components=2)
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        X_reduced = pca.fit_transform(X)
        X_restored = pca.inverse_transform(X_reduced)
        assert X_restored.shape == X.shape


class TestQLearningAgent:
    """Test QLearningAgent."""

    def test_init(self):
        """Test agent initialization."""
        agent = QLearningAgent(n_states=10, n_actions=4)
        assert agent.q_table.shape == (10, 4)

    def test_act(self):
        """Test action selection."""
        agent = QLearningAgent(n_states=5, n_actions=3)
        action = agent.act(state=0, training=False)
        assert 0 <= action < 3

    def test_learn(self):
        """Test Q-learning update."""
        agent = QLearningAgent(n_states=5, n_actions=3)
        agent.learn(state=0, action=1, reward=1.0, next_state=1, done=False)
        assert agent.q_table[0, 1] > 0


class TestSARSAAgent:
    """Test SARSAAgent."""

    def test_init(self):
        """Test SARSA agent initialization."""
        agent = SARSAAgent(n_states=10, n_actions=4)
        assert agent.q_table.shape == (10, 4)


class TestMultiArmedBandit:
    """Test MultiArmedBandit."""

    def test_init(self):
        """Test bandit initialization."""
        bandit = MultiArmedBandit(n_arms=5)
        assert bandit.n_arms == 5

    def test_select_arm(self):
        """Test arm selection."""
        bandit = MultiArmedBandit(n_arms=3)
        arm = bandit.select_arm()
        assert 0 <= arm < 3

    def test_update(self):
        """Test reward update."""
        bandit = MultiArmedBandit(n_arms=3)
        bandit.update(arm=0, reward=1.0)
        assert bandit.counts[0] == 1
        assert bandit.total_pulls == 1
