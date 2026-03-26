"""Tests for ml_utilities module."""

import pytest
from ml_utilities import (
    TrainValidateTestSplitter,
    CrossValidator,
    EvaluationMetrics,
    ModelPickler,
    SplitResult,
    train_validate_test_split,
)


class TestTrainValidateTestSplitter:
    """Tests for TrainValidateTestSplitter."""

    def test_init(self):
        """Test splitter initialization."""
        splitter = TrainValidateTestSplitter(test_size=0.2, val_size=0.1)
        assert splitter.test_size == 0.2
        assert splitter.val_size == 0.1

    def test_split(self):
        """Test basic split."""
        splitter = TrainValidateTestSplitter(test_size=0.2, val_size=0.1)
        X = list(range(100))
        
        result = splitter.split_single(X)
        
        assert isinstance(result, SplitResult)
        assert len(result.X_train) == 80
        assert len(result.X_test) == 20

    def test_split_with_y(self):
        """Test split with target variable."""
        splitter = TrainValidateTestSplitter(test_size=0.2)
        X = list(range(100))
        y = [i % 2 for i in range(100)]
        
        result = splitter.split_single(X, y)
        
        assert result.y_train is not None
        assert result.y_test is not None

    def test_split_three_way(self):
        """Test three-way split."""
        splitter = TrainValidateTestSplitter(test_size=0.2, val_size=0.1)
        X = list(range(100))
        
        X_train, X_val, X_test = splitter.split(X)
        
        assert len(X_train) > 0
        assert len(X_val) > 0
        assert len(X_test) > 0
        assert len(X_train) + len(X_val) + len(X_test) == 100


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics."""

    def test_accuracy(self):
        """Test accuracy calculation."""
        y_true = [1, 0, 1, 1, 0]
        y_pred = [1, 0, 1, 0, 0]
        
        acc = EvaluationMetrics.accuracy(y_true, y_pred)
        
        assert acc == 0.8

    def test_precision(self):
        """Test precision calculation."""
        y_true = [1, 0, 1, 1, 0]
        y_pred = [1, 0, 1, 0, 0]
        
        prec = EvaluationMetrics.precision(y_true, y_pred, pos_label=1)
        
        assert prec == 1.0

    def test_recall(self):
        """Test recall calculation."""
        y_true = [1, 0, 1, 1, 0]
        y_pred = [1, 0, 1, 0, 0]
        
        rec = EvaluationMetrics.recall(y_true, y_pred, pos_label=1)
        
        assert rec == 2/3

    def test_f1(self):
        """Test F1 score calculation."""
        y_true = [1, 0, 1, 1, 0]
        y_pred = [1, 0, 1, 0, 0]
        
        f1 = EvaluationMetrics.f1(y_true, y_pred, pos_label=1)
        
        assert 0 < f1 <= 1

    def test_mse(self):
        """Test MSE calculation."""
        y_true = [1, 2, 3, 4]
        y_pred = [1.1, 2.1, 2.9, 4.1]
        
        mse = EvaluationMetrics.mse(y_true, y_pred)
        
        assert mse < 0.1

    def test_mae(self):
        """Test MAE calculation."""
        y_true = [1, 2, 3, 4]
        y_pred = [1.1, 2.1, 2.9, 4.1]
        
        mae = EvaluationMetrics.mae(y_true, y_pred)
        
        assert mae < 0.2

    def test_r2_score(self):
        """Test R2 score calculation."""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1.1, 2.1, 2.9, 4.1, 4.9]
        
        r2 = EvaluationMetrics.r2_score(y_true, y_pred)
        
        assert 0 < r2 <= 1

    def test_classification_report(self):
        """Test classification report."""
        y_true = [1, 0, 1, 1, 0]
        y_pred = [1, 0, 1, 0, 0]
        
        report = EvaluationMetrics.classification_report(y_true, y_pred)
        
        assert "accuracy" in report
        assert 1 in report
        assert 0 in report


class TestModelPickler:
    """Tests for ModelPickler."""

    def test_save_load(self, tmp_path):
        """Test save and load."""
        model = {"key": "value", "number": 42}
        filepath = tmp_path / "model.pkl"
        
        ModelPickler.save(model, str(filepath))
        loaded = ModelPickler.load(str(filepath))
        
        assert loaded == model

    def test_save_with_metadata(self, tmp_path):
        """Test save with metadata."""
        model = {"key": "value"}
        filepath = tmp_path / "model.pkl"
        metadata = {"version": "1.0", "accuracy": 0.95}
        
        ModelPickler.save_with_metadata(model, str(filepath), metadata)
        loaded, loaded_meta = ModelPickler.load_with_metadata(str(filepath))
        
        assert loaded == model
        assert loaded_meta["version"] == "1.0"
        assert loaded_meta["accuracy"] == 0.95


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_train_validate_test_split(self):
        """Test convenience split function."""
        X = list(range(100))
        
        result = train_validate_test_split(X)
        
        assert len(result) == 3  # X_train, X_val, X_test
