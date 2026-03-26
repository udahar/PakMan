"""
Train / Validate / Test Module

Full ML training pipeline for training models, validating with datasets,
and testing model performance. Azure ML adjacent.

Includes:
- Dataset management and splitting
- Training loops with early stopping
- Validation monitoring
- Test evaluation with full metrics
- Experiment tracking
- Hyperparameter search (grid + random)

Usage:
    from modules.train_validate_test import Experiment, Trainer, DatasetSplitter

    splitter = DatasetSplitter(test_size=0.2, val_size=0.1)
    splits = splitter.split(X, y)

    trainer = Trainer(model, loss_fn, optimizer)
    results = trainer.fit(splits, epochs=100)
    print(results.test_metrics)
"""

import numpy as np
import json
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DatasetSplit:
    """A train/val/test split."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray

    @property
    def sizes(self) -> Dict[str, int]:
        return {
            "train": len(self.X_train),
            "val": len(self.X_val),
            "test": len(self.X_test),
        }


@dataclass
class EpochResult:
    """Result from a single training epoch."""

    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    train_metrics: Dict[str, float] = field(default_factory=dict)
    val_metrics: Dict[str, float] = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class TrainingResult:
    """Complete training result."""

    epochs_run: int
    best_epoch: int
    train_loss_history: List[float]
    val_loss_history: List[float]
    test_metrics: Dict[str, float]
    total_time_ms: int
    early_stopped: bool
    best_model_state: Any = None


# ============================================================
# Dataset Splitter
# ============================================================


class DatasetSplitter:
    """
    Split data into train/val/test sets.

    Supports stratified splitting for classification.

    Usage:
        splitter = DatasetSplitter(test_size=0.2, val_size=0.15)
        splits = splitter.split(X, y, stratify=True)
        print(splits.sizes)  # {'train': 650, 'val': 150, 'test': 200}
    """

    def __init__(
        self, test_size: float = 0.2, val_size: float = 0.15, random_state: int = 42
    ):
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y: np.ndarray, stratify: bool = False
    ) -> DatasetSplit:
        """
        Split data into train/val/test.

        Args:
            X: Features
            y: Targets
            stratify: Use stratified splitting for class balance
        """
        rng = np.random.RandomState(self.random_state)
        n = len(X)

        if stratify and y.ndim == 1:
            return self._stratified_split(X, y, rng)

        indices = rng.permutation(n)

        test_end = int(n * (1 - self.test_size))
        val_end = int(test_end * (1 - self.val_size / (1 - self.test_size)))

        train_idx = indices[:val_end]
        val_idx = indices[val_end:test_end]
        test_idx = indices[test_end:]

        return DatasetSplit(
            X_train=X[train_idx],
            y_train=y[train_idx],
            X_val=X[val_idx],
            y_val=y[val_idx],
            X_test=X[test_idx],
            y_test=y[test_idx],
        )

    def _stratified_split(
        self, X: np.ndarray, y: np.ndarray, rng: np.random.RandomState
    ) -> DatasetSplit:
        """Stratified split maintaining class proportions."""
        classes = np.unique(y)
        train_idx, val_idx, test_idx = [], [], []

        for cls in classes:
            cls_indices = np.where(y == cls)[0]
            rng.shuffle(cls_indices)

            n_cls = len(cls_indices)
            test_end = int(n_cls * (1 - self.test_size))
            val_end = int(test_end * (1 - self.val_size / (1 - self.test_size)))

            train_idx.extend(cls_indices[:val_end])
            val_idx.extend(cls_indices[val_end:test_end])
            test_idx.extend(cls_indices[test_end:])

        return DatasetSplit(
            X_train=X[train_idx],
            y_train=y[train_idx],
            X_val=X[val_idx],
            y_val=y[val_idx],
            X_test=X[test_idx],
            y_test=y[test_idx],
        )


# ============================================================
# Metrics
# ============================================================


class Metrics:
    """Compute evaluation metrics."""

    @staticmethod
    def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(y_true == y_pred))

    @staticmethod
    def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean((y_true - y_pred) ** 2))

    @staticmethod
    def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    @staticmethod
    def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    @staticmethod
    def precision_recall_f1(
        y_true: np.ndarray, y_pred: np.ndarray, pos_label: int = 1
    ) -> Dict[str, float]:
        tp = np.sum((y_pred == pos_label) & (y_true == pos_label))
        fp = np.sum((y_pred == pos_label) & (y_true != pos_label))
        fn = np.sum((y_pred != pos_label) & (y_true == pos_label))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {"precision": precision, "recall": recall, "f1": f1}

    @staticmethod
    def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        classes = np.unique(np.concatenate([y_true, y_pred]))
        cm = np.zeros((len(classes), len(classes)), dtype=int)
        class_to_idx = {c: i for i, c in enumerate(classes)}
        for t, p in zip(y_true, y_pred):
            cm[class_to_idx[t]][class_to_idx[p]] += 1
        return cm

    @staticmethod
    def full_report(
        y_true: np.ndarray, y_pred: np.ndarray, task: str = "classification"
    ) -> Dict[str, Any]:
        """Generate a full metrics report."""
        if task == "regression":
            return {
                "mse": Metrics.mse(y_true, y_pred),
                "rmse": Metrics.rmse(y_true, y_pred),
                "mae": Metrics.mae(y_true, y_pred),
                "r2": Metrics.r2_score(y_true, y_pred),
            }
        else:
            report = {"accuracy": Metrics.accuracy(y_true, y_pred)}
            classes = np.unique(y_true)
            for cls in classes:
                prf = Metrics.precision_recall_f1(y_true, y_pred, pos_label=cls)
                report[f"class_{int(cls)}"] = prf
            report["confusion_matrix"] = Metrics.confusion_matrix(
                y_true, y_pred
            ).tolist()
            return report


# ============================================================
# Early Stopping
# ============================================================


class EarlyStopping:
    """
    Stop training when validation loss stops improving.

    Usage:
        es = EarlyStopping(patience=10, min_delta=0.001)
        for epoch in range(100):
            val_loss = validate()
            if es.should_stop(val_loss):
                print(f"Early stop at epoch {epoch}")
                break
    """

    def __init__(self, patience: int = 10, min_delta: float = 0.001, mode: str = "min"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_value = float("inf") if mode == "min" else float("-inf")
        self.wait = 0
        self.best_epoch = 0
        self.best_state = None

    def should_stop(self, value: float, epoch: int = 0) -> bool:
        """Check if training should stop."""
        improved = False

        if self.mode == "min":
            improved = value < self.best_value - self.min_delta
        else:
            improved = value > self.best_value + self.min_delta

        if improved:
            self.best_value = value
            self.wait = 0
            self.best_epoch = epoch
        else:
            self.wait += 1

        return self.wait >= self.patience

    def save_state(self, state: Any):
        """Save model state when improvement detected."""
        if self.wait == 0:
            self.best_state = state


# ============================================================
# Trainer
# ============================================================


class Trainer:
    """
    Train a model with validation monitoring and early stopping.

    Works with any model that has: forward(x), backward(grad),
    and an optimizer that has: step(layers).

    Usage:
        trainer = Trainer(model, loss_fn, optimizer)
        result = trainer.fit(splits, epochs=100, early_stopping=True)
        print(result.test_metrics)
    """

    def __init__(self, model, loss_fn, optimizer=None):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.history: List[EpochResult] = []

    def fit(
        self,
        splits: DatasetSplit,
        epochs: int = 100,
        batch_size: int = 32,
        early_stopping: bool = True,
        patience: int = 10,
        verbose: bool = True,
    ) -> TrainingResult:
        """
        Train the model.

        Args:
            splits: DatasetSplit with train/val/test data
            epochs: Maximum epochs
            batch_size: Mini-batch size
            early_stopping: Use early stopping
            patience: Early stopping patience
            verbose: Print progress
        """
        start_time = time.time()

        es = EarlyStopping(patience=patience) if early_stopping else None
        self.history = []
        best_model = None
        early_stopped = False

        for epoch in range(epochs):
            epoch_start = time.time()

            # Train
            train_loss, train_metrics = self._train_epoch(
                splits.X_train, splits.y_train, batch_size
            )

            # Validate
            val_loss, val_metrics = None, {}
            if splits.X_val is not None and len(splits.X_val) > 0:
                val_loss, val_metrics = self._evaluate(splits.X_val, splits.y_val)

            duration = int((time.time() - epoch_start) * 1000)

            result = EpochResult(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                train_metrics=train_metrics,
                val_metrics=val_metrics,
                duration_ms=duration,
            )
            self.history.append(result)

            if verbose and (epoch % max(1, epochs // 10) == 0 or epoch == epochs - 1):
                val_str = f" - val_loss: {val_loss:.6f}" if val_loss is not None else ""
                print(f"Epoch {epoch + 1}/{epochs} - loss: {train_loss:.6f}{val_str}")

            # Early stopping
            if es:
                check_val = val_loss if val_loss is not None else train_loss
                if es.should_stop(check_val, epoch):
                    early_stopped = True
                    best_model = es.best_state
                    if verbose:
                        print(
                            f"Early stopping at epoch {epoch + 1} (best: {es.best_epoch + 1})"
                        )
                    break

        # Final test evaluation
        test_metrics = {}
        if splits.X_test is not None and len(splits.X_test) > 0:
            _, test_metrics = self._evaluate(splits.X_test, splits.y_test)

        total_time = int((time.time() - start_time) * 1000)

        train_losses = [r.train_loss for r in self.history]
        val_losses = [r.val_loss for r in self.history if r.val_loss is not None]

        best_epoch = es.best_epoch if es else len(self.history) - 1

        return TrainingResult(
            epochs_run=len(self.history),
            best_epoch=best_epoch,
            train_loss_history=train_losses,
            val_loss_history=val_losses,
            test_metrics=test_metrics,
            total_time_ms=total_time,
            early_stopped=early_stopped,
            best_model_state=best_model,
        )

    def _train_epoch(
        self, X: np.ndarray, y: np.ndarray, batch_size: int
    ) -> Tuple[float, Dict]:
        """Run one training epoch."""
        n = len(X)
        indices = np.random.permutation(n)
        total_loss = 0.0
        n_batches = 0

        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            idx = indices[start:end]

            # Forward
            y_pred = self.model.forward(X[idx])
            loss = self.loss_fn.forward(y_pred, y[idx])
            total_loss += loss
            n_batches += 1

            # Backward
            grad = self.loss_fn.backward(y_pred, y[idx])
            self.model.backward(grad)

            # Update
            if self.optimizer and hasattr(self.model, "layers"):
                self.optimizer.step(self.model.layers)

        avg_loss = total_loss / max(n_batches, 1)
        return avg_loss, {}

    def _evaluate(self, X: np.ndarray, y: np.ndarray) -> Tuple[float, Dict]:
        """Evaluate on data."""
        y_pred = (
            self.model.predict(X)
            if hasattr(self.model, "predict")
            else self.model.forward(X)
        )
        loss = self.loss_fn.forward(y_pred, y)

        metrics = {}
        # Auto-detect task type
        if y_pred.ndim > 1 and y_pred.shape[1] > 1:
            preds = np.argmax(y_pred, axis=1)
            true = np.argmax(y, axis=1) if y.ndim > 1 else y
            metrics["accuracy"] = Metrics.accuracy(true, preds)
        elif np.all((y_pred >= 0) & (y_pred <= 1)):
            preds = (y_pred > 0.5).astype(int).flatten()
            true = y.flatten() if y.ndim > 1 else y
            metrics["accuracy"] = Metrics.accuracy(true, preds)

        return float(loss), metrics


# ============================================================
# Hyperparameter Search
# ============================================================


class HyperparameterSearch:
    """
    Search for optimal hyperparameters.

    Supports grid search and random search.

    Usage:
        search = HyperparameterSearch(param_grid={
            'lr': [0.001, 0.01, 0.1],
            'hidden_size': [8, 16, 32],
        })
        results = search.random_search(X, y, n_trials=20)
        print(results['best_params'])
    """

    def __init__(self, param_grid: Dict[str, List[Any]]):
        self.param_grid = param_grid
        self.results: List[Dict[str, Any]] = []

    def grid_search(
        self, X: np.ndarray, y: np.ndarray, evaluate_fn: Callable, n_folds: int = 3
    ) -> Dict[str, Any]:
        """
        Exhaustive grid search.

        Args:
            X: Features
            y: Targets
            evaluate_fn: Function(params, X_train, y_train, X_val, y_val) -> score
            n_folds: Cross-validation folds
        """
        import itertools

        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        all_combos = list(itertools.product(*values))

        best_score = float("-inf")
        best_params = {}

        for combo in all_combos:
            params = dict(zip(keys, combo))
            scores = []

            # Cross-validation
            fold_size = len(X) // n_folds
            for fold in range(n_folds):
                val_start = fold * fold_size
                val_end = val_start + fold_size

                X_val = X[val_start:val_end]
                y_val = y[val_start:val_end]
                X_train = np.concatenate([X[:val_start], X[val_end:]])
                y_train = np.concatenate([y[:val_start], y[val_end:]])

                score = evaluate_fn(params, X_train, y_train, X_val, y_val)
                scores.append(score)

            avg_score = np.mean(scores)
            self.results.append(
                {"params": params, "score": avg_score, "scores": scores}
            )

            if avg_score > best_score:
                best_score = avg_score
                best_params = params

        return {
            "best_params": best_params,
            "best_score": best_score,
            "all_results": self.results,
        }

    def random_search(
        self,
        X: np.ndarray,
        y: np.ndarray,
        evaluate_fn: Callable,
        n_trials: int = 20,
        n_folds: int = 3,
    ) -> Dict[str, Any]:
        """
        Random search over parameter space.
        """
        rng = np.random.RandomState(42)

        best_score = float("-inf")
        best_params = {}

        for trial in range(n_trials):
            # Sample random params
            params = {}
            for key, values in self.param_grid.items():
                params[key] = values[rng.randint(len(values))]

            # Evaluate
            fold_size = len(X) // n_folds
            scores = []
            for fold in range(n_folds):
                val_start = fold * fold_size
                val_end = val_start + fold_size
                X_val = X[val_start:val_end]
                y_val = y[val_start:val_end]
                X_train = np.concatenate([X[:val_start], X[val_end:]])
                y_train = np.concatenate([y[:val_start], y[val_end:]])

                score = evaluate_fn(params, X_train, y_train, X_val, y_val)
                scores.append(score)

            avg_score = np.mean(scores)
            self.results.append({"params": params, "score": avg_score, "trial": trial})

            if avg_score > best_score:
                best_score = avg_score
                best_params = params

        return {
            "best_params": best_params,
            "best_score": best_score,
            "all_results": self.results,
        }


# ============================================================
# Experiment Tracker
# ============================================================


class Experiment:
    """
    Track ML experiments with configs, metrics, and artifacts.

    Usage:
        exp = Experiment(name='xor_nn_v1')
        exp.log_params({'lr': 0.01, 'hidden': 16})
        exp.log_metrics({'accuracy': 0.95, 'loss': 0.05})
        exp.save('experiments/')
    """

    def __init__(self, name: str = None):
        self.name = name or f"exp_{int(time.time())}"
        self.params: Dict[str, Any] = {}
        self.metrics: Dict[str, float] = {}
        self.history: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()

    def log_params(self, params: Dict[str, Any]):
        """Log hyperparameters."""
        self.params.update(params)

    def log_metrics(self, metrics: Dict[str, float], step: int = None):
        """Log metrics at a given step."""
        entry = {"step": step, "timestamp": datetime.now().isoformat()}
        entry.update(metrics)
        self.history.append(entry)
        self.metrics.update(metrics)

    def log_epoch(self, epoch_result: EpochResult):
        """Log a training epoch result."""
        self.log_metrics(
            {
                "train_loss": epoch_result.train_loss,
                "val_loss": epoch_result.val_loss or 0,
                **epoch_result.train_metrics,
                **epoch_result.val_metrics,
            },
            step=epoch_result.epoch,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export experiment as dict."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "params": self.params,
            "metrics": self.metrics,
            "history": self.history,
        }

    def save(self, directory: str):
        """Save experiment to JSON file."""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.name}.json")
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, filepath: str) -> "Experiment":
        """Load experiment from file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        exp = cls(name=data["name"])
        exp.params = data.get("params", {})
        exp.metrics = data.get("metrics", {})
        exp.history = data.get("history", [])
        exp.created_at = data.get("created_at", "")
        return exp

    def summary(self) -> str:
        """Print experiment summary."""
        lines = [
            f"Experiment: {self.name}",
            f"Created: {self.created_at}",
            f"Params: {self.params}",
            f"Final Metrics: {self.metrics}",
            f"History entries: {len(self.history)}",
        ]
        return "\n".join(lines)
