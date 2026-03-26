"""
Feature extraction for anomaly detection.

Converts raw metrics into feature vectors for ML models.
"""
import logging
from typing import Dict, List, Any, Optional
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract features from metrics for anomaly detection.
    
    Computes derived features like:
    - z-scores
    - rolling statistics
    - deltas
    """
    
    def __init__(self, window_size: int = 20):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Size of sliding window for features
        """
        self.window_size = window_size
        self.history: Dict[str, deque] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    def extract(self, metrics: Dict[str, float]) -> List[float]:
        """
        Extract features from metrics.
        
        Args:
            metrics: Dictionary of metric name -> value
            
        Returns:
            Feature vector
        """
        features = []
        
        for name, value in sorted(metrics.items()):
            features.append(value)
            
            if name not in self.history:
                self.history[name] = deque(maxlen=self.window_size)
            
            self.history[name].append(value)
            
            z_score = self._compute_zscore(name, value)
            features.append(z_score)
            
            delta = self._compute_delta(name, value)
            features.append(delta)
            
            rolling_mean = self._compute_rolling_mean(name)
            features.append(rolling_mean)
            
            rolling_std = self._compute_rolling_std(name)
            features.append(rolling_std)
        
        return features
    
    def get_feature_names(self, metric_names: List[str]) -> List[str]:
        """
        Get feature names for metrics.
        
        Args:
            metric_names: List of metric names
            
        Returns:
            List of feature names
        """
        names = []
        for name in sorted(metric_names):
            names.extend([
                name,
                f"{name}_zscore",
                f"{name}_delta",
                f"{name}_rolling_mean",
                f"{name}_rolling_std",
            ])
        return names
    
    def _compute_zscore(self, name: str, value: float) -> float:
        """Compute z-score for a value."""
        if name not in self.baselines:
            return 0.0
        
        mean = self.baselines[name].get("mean", 0)
        std = self.baselines[name].get("std", 1)
        
        if std == 0:
            return 0.0
        
        return (value - mean) / std
    
    def _compute_delta(self, name: str, value: float) -> float:
        """Compute delta from previous value."""
        if name not in self.history or len(self.history[name]) < 2:
            return 0.0
        
        history_list = list(self.history[name])
        return value - history_list[-2]
    
    def _compute_rolling_mean(self, name: str) -> float:
        """Compute rolling mean."""
        if name not in self.history or len(self.history[name]) < 2:
            return 0.0
        
        return np.mean(list(self.history[name]))
    
    def _compute_rolling_std(self, name: str) -> float:
        """Compute rolling standard deviation."""
        if name not in self.history or len(self.history[name]) < 2:
            return 0.0
        
        return np.std(list(self.history[name]))
    
    def update_baseline(self, name: str, mean: float, std: float) -> None:
        """
        Update baseline statistics for a metric.
        
        Args:
            name: Metric name
            mean: Mean value
            std: Standard deviation
        """
        if name not in self.baselines:
            self.baselines[name] = {}
        
        self.baselines[name]["mean"] = mean
        self.baselines[name]["std"] = std


class RuntimeFeatureExtractor(FeatureExtractor):
    """
    Extended feature extractor for runtime metrics.
    
    Adds context-aware features for AI system metrics.
    """
    
    def extract_runtime(
        self,
        model: str,
        task_type: str,
        latency: float,
        score: float,
        tokens: int,
        success: bool,
    ) -> List[float]:
        """
        Extract features from runtime metrics.
        
        Args:
            model: Model name
            task_type: Task type
            latency: Response latency in ms
            score: Quality score
            tokens: Token count
            success: Whether request succeeded
            
        Returns:
            Feature vector
        """
        metrics = {
            "latency": latency,
            "score": score,
            "tokens": tokens,
            "success": 1.0 if success else 0.0,
        }
        
        features = self.extract(metrics)
        
        features.append(self._encode_model(model))
        features.append(self._encode_task(task_type))
        
        if "latency" in self.history and "score" in self.history:
            try:
                corr = self._compute_correlation("latency", "score")
                features.append(corr)
            except Exception:
                features.append(0.0)
        else:
            features.append(0.0)
        
        return features
    
    def _encode_model(self, model: str) -> float:
        """Encode model name as float."""
        model_hash = sum(ord(c) for c in model)
        return float(model_hash % 100) / 100.0
    
    def _encode_task(self, task: str) -> float:
        """Encode task type as float."""
        task_hash = sum(ord(c) for c in task)
        return float(task_hash % 100) / 100.0
    
    def _compute_correlation(self, metric1: str, metric2: str) -> float:
        """Compute correlation between two metrics."""
        if (metric1 not in self.history or 
            metric2 not in self.history or
            len(self.history[metric1]) < 5 or
            len(self.history[metric2]) < 5):
            return 0.0
        
        try:
            v1 = np.array(list(self.history[metric1]))
            v2 = np.array(list(self.history[metric2]))
            
            if np.std(v1) == 0 or np.std(v2) == 0:
                return 0.0
            
            corr = np.corrcoef(v1, v2)[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except Exception:
            return 0.0
