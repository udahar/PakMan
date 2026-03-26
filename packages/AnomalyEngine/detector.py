"""
Anomaly detection implementations.

Statistical and ML-based anomaly detection.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class AnomalyResult:
    """Result from anomaly detection."""
    is_anomaly: bool
    metric: str
    value: float
    anomaly_type: Any
    severity: Any
    z_score: float
    threshold: float
    mean: float = 0.0
    std: float = 0.0
    score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly": self.is_anomaly,
            "metric": self.metric,
            "value": self.value,
            "type": self.anomaly_type.value if hasattr(self.anomaly_type, 'value') else str(self.anomaly_type),
            "severity": self.severity.value if hasattr(self.severity, 'value') else str(self.severity),
            "z_score": round(self.z_score, 3),
            "threshold": round(self.threshold, 3),
            "context": self.context,
        }


class StatisticalDetector:
    """
    Statistical anomaly detector using z-score.
    
    Simple and fast - good for univariate metrics.
    
    Rule: if |value - mean| > k * std → anomaly
    """
    
    def __init__(self, k_std: float = 3.0):
        """
        Initialize statistical detector.
        
        Args:
            k_std: Number of standard deviations for threshold
        """
        self.k_std = k_std
        self.history: List[float] = []
    
    def detect(self, value: float, mean: float, std: float) -> Tuple[bool, float]:
        """
        Detect if value is anomalous.
        
        Args:
            value: Value to check
            mean: Historical mean
            std: Historical standard deviation
            
        Returns:
            Tuple of (is_anomaly, z_score)
        """
        if std == 0 or len(self.history) < 10:
            return False, 0.0
        
        z_score = (value - mean) / std
        is_anomaly = abs(z_score) > self.k_std
        
        self.history.append(value)
        if len(self.history) > 1000:
            self.history.pop(0)
        
        return is_anomaly, z_score


class MLDetector:
    """
    ML-based anomaly detector using Isolation Forest.
    
    Better for multivariate anomaly detection.
    """
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize ML detector.
        
        Args:
            contamination: Expected proportion of anomalies
        """
        self.contamination = contamination
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.is_fitted = False
        self.feature_names: List[str] = []
        
        if not HAS_SKLEARN:
            logger.warning("sklearn not available, ML detection disabled")
    
    def fit(self, X: List[List[float]], y: Optional[List[int]] = None) -> None:
        """
        Fit the detector on normal data.
        
        Args:
            X: Feature vectors
            y: Labels (optional, uses unsupervised if None)
        """
        if not HAS_SKLEARN:
            logger.error("sklearn required for ML detection")
            return
        
        X_array = np.array(X)
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        self.feature_names = [f"feature_{i}" for i in range(X_array.shape[1])]
        
        if y is None:
            y = [1] * len(X)
        
        if len(X) < 20:
            logger.warning("Insufficient data for ML training, using statistical fallback")
            self.is_fitted = False
            return
        
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100,
        )
        
        try:
            self.model.fit(X_array)
            self.is_fitted = True
            logger.info(f"ML detector fitted on {len(X)} samples")
        except Exception as e:
            logger.error(f"ML training failed: {e}")
            self.is_fitted = False
    
    def predict(self, features: List[float]) -> AnomalyResult:
        """
        Predict if features are anomalous.
        
        Args:
            features: Feature vector
            
        Returns:
            AnomalyResult
        """
        if not self.is_fitted or self.model is None:
            return AnomalyResult(
                is_anomaly=False,
                metric="ml",
                value=0.0,
                anomaly_type="unknown",
                severity="low",
                z_score=0.0,
                threshold=0.0,
            )
        
        X = np.array(features).reshape(1, -1)
        
        try:
            prediction = self.model.predict(X)[0]
            score = self.model.decision_function(X)[0]
            
            is_anomaly = prediction == -1
            
            if hasattr(self, '_default_result'):
                result = self._default_result
            else:
                from . import AnomalyType, Severity
                result = AnomalyResult(
                    is_anomaly=is_anomaly,
                    metric="ml",
                    value=score,
                    anomaly_type=AnomalyType.UNKNOWN,
                    severity=Severity.MEDIUM if is_anomaly else Severity.LOW,
                    z_score=0.0,
                    threshold=0.0,
                    score=score,
                )
                self._default_result = result
            
            result.is_anomaly = is_anomaly
            result.score = score
            return result
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return AnomalyResult(
                is_anomaly=False,
                metric="ml",
                value=0.0,
                anomaly_type="unknown",
                severity="low",
                z_score=0.0,
                threshold=0.0,
            )
    
    def predict_batch(self, X: List[List[float]]) -> List[int]:
        """
        Predict on batch of samples.
        
        Args:
            X: List of feature vectors
            
        Returns:
            List of predictions (1=normal, -1=anomaly)
        """
        if not self.is_fitted or self.model is None:
            return [1] * len(X)
        
        X_array = np.array(X)
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        return self.model.predict(X_array).tolist()


class MultivariateDetector:
    """
    Detect anomalies where combination of values is wrong
    even if individual values look fine.
    
    Uses Mahalanobis distance for multivariate detection.
    """
    
    def __init__(self, threshold: float = 3.0):
        """
        Initialize multivariate detector.
        
        Args:
            threshold: Mahalanobis distance threshold
        """
        self.threshold = threshold
        self.mean: Optional[np.ndarray] = None
        self.cov_inv: Optional[np.ndarray] = None
        self.is_fitted = False
    
    def fit(self, X: List[List[float]]) -> None:
        """
        Fit on normal data.
        
        Args:
            X: Feature matrix
        """
        X_array = np.array(X)
        
        if len(X_array) < 10:
            logger.warning("Insufficient data for multivariate detection")
            return
        
        self.mean = np.mean(X_array, axis=0)
        
        try:
            cov = np.cov(X_array, rowvar=False)
            self.cov_inv = np.linalg.inv(cov)
            self.is_fitted = True
            logger.info(f"Multivariate detector fitted on {len(X)} samples")
        except np.linalg.LinAlgError:
            logger.error("Singular covariance matrix")
            self.is_fitted = False
    
    def detect(self, x: List[float]) -> Tuple[bool, float]:
        """
        Detect multivariate anomaly.
        
        Args:
            x: Feature vector
            
        Returns:
            Tuple of (is_anomaly, mahalanobis_distance)
        """
        if not self.is_fitted or self.mean is None or self.cov_inv is None:
            return False, 0.0
        
        x_array = np.array(x)
        diff = x_array - self.mean
        
        try:
            mahal = np.sqrt(diff @ self.cov_inv @ diff.T)
            is_anomaly = mahal > self.threshold
            return is_anomaly, float(mahal)
        except Exception:
            return False, 0.0
