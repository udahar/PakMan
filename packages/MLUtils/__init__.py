"""
ML Utilities Module

Machine learning utilities including:
- Train/Validate/Test splitting
- Model pickling and serialization
- Model evaluation metrics
- Cross-validation helpers

Based on AI900 concepts and ML best practices.
"""

import logging
from typing import List, Tuple, Dict, Any, Callable

logger = logging.getLogger(__name__)

try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("numpy not available - ML utilities will have limited functionality")


@dataclass
class SplitResult:
    """Result from a train/test split"""

    X_train: Any
    X_test: Any
    y_train: Any
    y_test: Any


@dataclass
class CrossValidationResult:
    """Result from cross-validation"""

    fold_scores: List[float]
    mean_score: float
    std_score: float
    scores_by_fold: Dict[int, float]


class TrainValidateTestSplitter:
    """
    Split data into training, validation, and test sets.

    Usage:
        splitter = TrainValidateTestSplitter(test_size=0.2, val_size=0.1)
        X_train, X_val, X_test, y_train, y_val, y_test = splitter.split(X, y)
    """

    def __init__(
        self, test_size: float = 0.2, val_size: float = 0.1, random_state: int = 42
    ):
        """
        Initialize splitter.

        Args:
            test_size: Proportion of data for test set (0-1)
            val_size: Proportion of data for validation set (0-1)
            random_state: Random seed for reproducibility
        """
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state

    def split(self, X, y=None) -> Tuple:
        """
        Split data into train/val/test sets.

        Args:
            X: Features (array-like)
            y: Target variable (optional)

        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
            If y is None, returns (X_train, X_val, X_test)
        """
        if np is None:
            raise ImportError("numpy required for splitting")

        np.random.seed(self.random_state)

        n_samples = len(X) if hasattr(X, "__len__") else X.shape[0]

        # Calculate split indices
        test_end = int(n_samples * (1 - self.test_size))
        val_end = int(test_end * (1 - self.val_size / (1 - self.test_size)))

        # Shuffle indices
        indices = np.random.permutation(n_samples)

        train_idx = indices[:val_end]
        val_idx = indices[val_end:test_end]
        test_idx = indices[test_end:]

        # Split data
        X_train = self._index(X, train_idx)
        X_val = self._index(X, val_idx)
        X_test = self._index(X, test_idx)

        if y is not None:
            y_train = self._index(y, train_idx)
            y_val = self._index(y, val_idx)
            y_test = self._index(y, test_idx)
            return X_train, X_val, X_test, y_train, y_val, y_test

        return X_train, X_val, X_test

    def split_single(self, X, y=None, test_size: float = None) -> SplitResult:
        """
        Simple two-way split (train/test only).

        Args:
            X: Features
            y: Target (optional)
            test_size: Override test size for this split

        Returns:
            SplitResult with X_train, X_test, y_train, y_test
        """
        size = test_size or self.test_size

        if np is None:
            raise ImportError("numpy required for splitting")

        np.random.seed(self.random_state)

        n_samples = len(X) if hasattr(X, "__len__") else X.shape[0]
        indices = np.random.permutation(n_samples)

        split_point = int(n_samples * (1 - size))

        train_idx = indices[:split_point]
        test_idx = indices[split_point:]

        X_train = self._index(X, train_idx)
        X_test = self._index(X, test_idx)

        if y is not None:
            y_train = self._index(y, train_idx)
            y_test = self._index(y, test_idx)
            return SplitResult(X_train, X_test, y_train, y_test)

        return SplitResult(X_train, X_test, None, None)

    def _index(self, data, indices) -> Any:
        """Index into data"""
        if hasattr(data, "iloc"):
            return data.iloc[indices]
        elif hasattr(data, "__getitem__"):
            return data[indices]
        return data


class CrossValidator:
    """
    K-fold cross-validation helper.

    Usage:
        cv = CrossValidator(n_folds=5)
        results = cv.validate(model, X, y, scoring='accuracy')
    """

    def __init__(self, n_folds: int = 5, random_state: int = 42):
        self.n_folds = n_folds
        self.random_state = random_state

    def validate(
        self, model, X, y, scoring: Callable = None, fit_kwargs: Dict = None
    ) -> CrossValidationResult:
        """
        Run k-fold cross-validation.

        Args:
            model: Model to validate (must have fit/predict or score)
            X: Features
            y: Target
            scoring: Scoring function (model.score by default)
            fit_kwargs: Additional arguments for model.fit

        Returns:
            CrossValidationResult with fold scores and statistics
        """
        if np is None:
            raise ImportError("numpy required for cross-validation")

        np.random.seed(self.random_state)

        n_samples = len(X) if hasattr(X, "__len__") else X.shape[0]
        indices = np.random.permutation(n_samples)

        # Create fold indices
        fold_size = n_samples // self.n_folds
        folds = []

        for i in range(self.n_folds):
            start = i * fold_size
            end = start + fold_size if i < self.n_folds - 1 else n_samples
            test_idx = indices[start:end]
            train_idx = np.concatenate([indices[:start], indices[end:]])
            folds.append((train_idx, test_idx))

        fit_kwargs = fit_kwargs or {}
        fold_scores = []

        for fold_idx, (train_idx, test_idx) in enumerate(folds):
            X_train = self._index(X, train_idx)
            X_test = self._index(X, test_idx)
            y_train = self._index(y, train_idx)
            y_test = self._index(y, test_idx)

            # Clone model for this fold
            fold_model = self._clone_model(model)

            # Fit and score
            fold_model.fit(X_train, y_train, **fit_kwargs)

            if scoring:
                score = scoring(fold_model, X_test, y_test)
            elif hasattr(fold_model, "score"):
                score = fold_model.score(X_test, y_test)
            else:
                raise ValueError(
                    "Model must have score() method or provide scoring function"
                )

            fold_scores.append(score)

        return CrossValidationResult(
            fold_scores=fold_scores,
            mean_score=np.mean(fold_scores),
            std_score=np.std(fold_scores),
            scores_by_fold={i: s for i, s in enumerate(fold_scores)},
        )

    def _index(self, data, indices) -> Any:
        """Index into data"""
        if hasattr(data, "iloc"):
            return data.iloc[indices]
        elif hasattr(data, "__getitem__"):
            return data[indices]
        return data

    def _clone_model(self, model):
        """Clone a model for cross-validation"""
        try:
            from sklearn.base import clone

            return clone(model)
        except:
            # Fallback: just return same model (won't work for some algorithms)
            return model


class EvaluationMetrics:
    """
    Common ML evaluation metrics.

    Usage:
        metrics = EvaluationMetrics()

        # Classification
        print(metrics.accuracy(y_true, y_pred))
        print(metrics.precision(y_true, y_pred))
        print(metrics.recall(y_true, y_pred))
        print(metrics.f1(y_true, y_pred))
        print(metrics.confusion_matrix(y_true, y_pred))

        # Regression
        print(metrics.mse(y_true, y_pred))
        print(metrics.rmse(y_true, y_pred))
        print(metrics.mae(y_true, y_pred))
        print(metrics.r2_score(y_true, y_pred))
    """

    @staticmethod
    def accuracy(y_true, y_pred) -> float:
        """Calculate accuracy score"""
        if np is None:
            raise ImportError("numpy required")
        return np.mean(y_true == y_pred)

    @staticmethod
    def precision(y_true, y_pred, pos_label: int = 1) -> float:
        """Calculate precision score"""
        if np is None:
            raise ImportError("numpy required")
        true_positives = np.sum((y_pred == pos_label) & (y_true == pos_label))
        predicted_positives = np.sum(y_pred == pos_label)
        return true_positives / predicted_positives if predicted_positives > 0 else 0

    @staticmethod
    def recall(y_true, y_pred, pos_label: int = 1) -> float:
        """Calculate recall score"""
        if np is None:
            raise ImportError("numpy required")
        true_positives = np.sum((y_pred == pos_label) & (y_true == pos_label))
        actual_positives = np.sum(y_true == pos_label)
        return true_positives / actual_positives if actual_positives > 0 else 0

    @staticmethod
    def f1(y_true, y_pred, pos_label: int = 1) -> float:
        """Calculate F1 score"""
        p = EvaluationMetrics.precision(y_true, y_pred, pos_label)
        r = EvaluationMetrics.recall(y_true, y_pred, pos_label)
        return 2 * p * r / (p + r) if (p + r) > 0 else 0

    @staticmethod
    def confusion_matrix(y_true, y_pred) -> np.ndarray:
        """Calculate confusion matrix"""
        if np is None:
            raise ImportError("numpy required")

        classes = np.unique(np.concatenate([y_true, y_pred]))
        n_classes = len(classes)
        cm = np.zeros((n_classes, n_classes), dtype=int)

        class_to_idx = {c: i for i, c in enumerate(classes)}

        for true, pred in zip(y_true, y_pred):
            cm[class_to_idx[true]][class_to_idx[pred]] += 1

        return cm

    @staticmethod
    def mse(y_true, y_pred) -> float:
        """Mean squared error"""
        if np is None:
            raise ImportError("numpy required")
        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def rmse(y_true, y_pred) -> float:
        """Root mean squared error"""
        return np.sqrt(EvaluationMetrics.mse(y_true, y_pred))

    @staticmethod
    def mae(y_true, y_pred) -> float:
        """Mean absolute error"""
        if np is None:
            raise ImportError("numpy required")
        return np.mean(np.abs(y_true - y_pred))

    @staticmethod
    def r2_score(y_true, y_pred) -> float:
        """R-squared (coefficient of determination)"""
        if np is None:
            raise ImportError("numpy required")

        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    @staticmethod
    def classification_report(y_true, y_pred) -> Dict[str, Any]:
        """Generate classification report"""
        if np is None:
            raise ImportError("numpy required")

        classes = np.unique(y_true)
        report = {}

        for cls in classes:
            y_true_cls = y_true == cls
            y_pred_cls = y_pred == cls

            tp = np.sum(y_true_cls & y_pred_cls)
            fp = np.sum(~y_true_cls & y_pred_cls)
            fn = np.sum(y_true_cls & ~y_pred_cls)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            report[int(cls)] = {
                "precision": precision,
                "recall": recall,
                "f1-score": f1,
                "support": int(np.sum(y_true_cls)),
            }

        # Overall metrics
        report["accuracy"] = EvaluationMetrics.accuracy(y_true, y_pred)

        return report


class ModelPickler:
    """
    Utilities for pickling and unpickling ML models.

    Usage:
        pickler = ModelPickler()

        # Save model
        pickler.save(model, "model.pkl")

        # Load model
        model = pickler.load("model.pkl")

        # Save with metadata
        pickler.save_with_metadata(model, "model.pkl", {
            "version": "1.0",
            "accuracy": 0.95
        })
    """

    @staticmethod
    def save(model, filepath: str, protocol: int = -1):
        """
        Save model to disk.

        Args:
            model: Model to save
            filepath: Path to save to
            protocol: Pickle protocol (-1 for latest)
        """
        import os
        import pickle

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        with open(filepath, "wb") as f:
            pickle.dump(model, f, protocol=protocol)

    @staticmethod
    def load(filepath: str):
        """
        Load model from disk.

        Args:
            filepath: Path to load from

        Returns:
            Loaded model
        """
        import pickle

        with open(filepath, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def save_with_metadata(model, filepath: str, metadata: Dict[str, Any]):
        """
        Save model with metadata.

        Metadata is stored in a separate .meta file alongside the model.
        """
        import json

        ModelPickler.save(model, filepath)

        meta_path = filepath + ".meta"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

    @staticmethod
    def load_with_metadata(filepath: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Load model and metadata.

        Returns:
            Tuple of (model, metadata)
        """
        import json

        model = ModelPickler.load(filepath)

        meta_path = filepath + ".meta"
        metadata = {}

        import os

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)

        return model, metadata

    @staticmethod
    def save_joblib(model, filepath: str):
        """Save model using joblib (better for large numpy arrays)"""
        import os
        import joblib

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(model, filepath)

    @staticmethod
    def load_joblib(filepath: str):
        """Load model using joblib"""
        import joblib

        return joblib.load(filepath)


# Convenience function
def train_validate_test_split(
    X, y=None, test_size: float = 0.2, val_size: float = 0.1, random_state: int = 42
):
    """
    Convenience function for train/val/test split.

    Returns:
        If y provided: (X_train, X_val, X_test, y_train, y_val, y_test)
        If y is None: (X_train, X_val, X_test)
    """
    splitter = TrainValidateTestSplitter(test_size, val_size, random_state)
    return splitter.split(X, y)


def cross_validate(
    model, X, y, n_folds: int = 5, scoring=None
) -> CrossValidationResult:
    """
    Convenience function for cross-validation.
    """
    cv = CrossValidator(n_folds)
    return cv.validate(model, X, y, scoring)
