"""
Anomaly Engine - Self-aware system for detecting abnormal behavior

Detects anomalies in AI system behavior including:
- Performance anomalies (model suddenly worse)
- Latency anomalies (response time spikes)
- Routing anomalies (fallback loops)
- Failure anomalies (repeated errors)
- Behavior anomalies (unusual patterns)

Based on SemanticFinder/anomaly_engine spec.

Usage:
    from anomaly_engine import AnomalyEngine

    engine = AnomalyEngine()
    engine.track(metric_name="latency", value=1500, context={"model": "qwen"})
    
    result = engine.check("latency", 1500)
    if result.is_anomaly:
        engine.respond(result)
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

from .detector import StatisticalDetector, MLDetector, AnomalyResult
from .features import FeatureExtractor
from .response import ResponseEngine, AnomalyResponse

__all__ = [
    "AnomalyEngine",
    "AnomalyResult",
    "AnomalyResponse",
    "StatisticalDetector",
    "MLDetector",
    "FeatureExtractor",
    "ResponseEngine",
    "AnomalyType",
    "Severity",
]

__version__ = "1.0.0"


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    PERFORMANCE = "performance"
    LATENCY = "latency"
    ROUTING = "routing"
    FAILURE = "failure"
    BEHAVIOR = "behavior"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricWindow:
    """Sliding window for metric tracking."""
    name: str
    values: List[float] = field(default_factory=list)
    max_size: int = 100
    
    def add(self, value: float) -> None:
        """Add a value to the window."""
        self.values.append(value)
        if len(self.values) > self.max_size:
            self.values.pop(0)
    
    def mean(self) -> float:
        """Get mean of window."""
        return sum(self.values) / len(self.values) if self.values else 0.0
    
    def std(self) -> float:
        """Get standard deviation of window."""
        if len(self.values) < 2:
            return 0.0
        mean = self.mean()
        variance = sum((x - mean) ** 2 for x in self.values) / len(self.values)
        return variance ** 0.5


class AnomalyEngine:
    """
    Main anomaly detection engine.
    
    Learns "normal behavior" → flags deviations → triggers actions.
    
    Usage:
        engine = AnomalyEngine()
        
        # Track metrics
        engine.track("latency", 1200, {"model": "qwen"})
        engine.track("score", 82, {"task": "code"})
        
        # Check for anomalies
        result = engine.check("latency", 1500)
        if result.is_anomaly:
            response = engine.respond(result)
    """
    
    def __init__(
        self,
        k_std: float = 3.0,
        window_size: int = 100,
        use_ml: bool = False,
    ):
        """
        Initialize the anomaly engine.
        
        Args:
            k_std: Number of standard deviations for threshold
            window_size: Size of sliding window for baseline
            use_ml: Use ML-based detection (requires sklearn)
        """
        logger.info(f"Initializing AnomalyEngine (k_std={k_std}, window={window_size})")
        self.k_std = k_std
        self.window_size = window_size
        self.use_ml = use_ml
        
        self.windows: Dict[str, MetricWindow] = {}
        self.statistical_detector = StatisticalDetector(k_std=k_std)
        self.ml_detector: Optional[MLDetector] = None
        self.feature_extractor = FeatureExtractor()
        self.response_engine = ResponseEngine()
        
        self.history: List[AnomalyResult] = []
    
    def track(
        self,
        metric_name: str,
        value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a metric value.
        
        Args:
            metric_name: Name of the metric (e.g., "latency", "score")
            value: Metric value
            context: Additional context (model, task, etc.)
        """
        if metric_name not in self.windows:
            self.windows[metric_name] = MetricWindow(
                name=metric_name,
                max_size=self.window_size,
            )
        
        self.windows[metric_name].add(value)
        logger.debug(f"Tracked {metric_name}={value}")
    
    def check(
        self,
        metric_name: str,
        value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> AnomalyResult:
        """
        Check if a value is anomalous.
        
        Args:
            metric_name: Name of the metric
            value: Value to check
            context: Additional context
            
        Returns:
            AnomalyResult with detection details
        """
        if metric_name not in self.windows:
            logger.warning(f"Metric {metric_name} not tracked yet")
            return AnomalyResult(
                is_anomaly=False,
                metric=metric_name,
                value=value,
                anomaly_type=AnomalyType.UNKNOWN,
                severity=Severity.LOW,
                z_score=0.0,
                threshold=0.0,
                context=context or {},
            )
        
        window = self.windows[metric_name]
        z_score = self._calculate_zscore(value, window)
        threshold = window.mean() + self.k_std * window.std()
        
        anomaly_type = self._classify_anomaly(metric_name, z_score)
        severity = self._calculate_severity(z_score)
        is_anomaly = abs(z_score) > self.k_std and len(window.values) >= 10
        
        result = AnomalyResult(
            is_anomaly=is_anomaly,
            metric=metric_name,
            value=value,
            z_score=z_score,
            threshold=threshold,
            mean=window.mean(),
            std=window.std(),
            anomaly_type=anomaly_type,
            severity=severity,
            context=context or {},
        )
        
        if is_anomaly:
            logger.warning(
                f"Anomaly detected: {metric_name}={value} "
                f"(z={z_score:.2f}, threshold={threshold:.2f})"
            )
            self.history.append(result)
        
        return result
    
    def check_ml(
        self,
        features: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> AnomalyResult:
        """
        Check using ML-based detection.
        
        Requires sklearn and sufficient training data.
        
        Args:
            features: Feature dictionary
            context: Additional context
            
        Returns:
            AnomalyResult
        """
        if not self.use_ml or self.ml_detector is None:
            logger.warning("ML detection not enabled or not trained")
            return AnomalyResult(
                is_anomaly=False,
                metric="ml",
                value=0.0,
                anomaly_type=AnomalyType.UNKNOWN,
                severity=Severity.LOW,
                z_score=0.0,
                threshold=0.0,
                context=context or {},
            )
        
        feature_vector = self.feature_extractor.extract(features)
        result = self.ml_detector.predict(feature_vector)
        result.context = context or {}
        return result
    
    def respond(self, anomaly: AnomalyResult) -> AnomalyResponse:
        """
        Respond to an anomaly.
        
        Args:
            anomaly: The anomaly result
            
        Returns:
            Response actions taken
        """
        return self.response_engine.respond(anomaly)
    
    def train_ml(self, X: List[Dict[str, float]], y: List[int]) -> None:
        """
        Train ML detector.
        
        Args:
            X: List of feature dictionaries
            y: Labels (0=normal, 1=anomaly)
        """
        if not self.use_ml:
            logger.warning("ML not enabled")
            return
        
        self.ml_detector = MLDetector()
        features = [self.feature_extractor.extract(f) for f in X]
        self.ml_detector.fit(features, y)
        logger.info(f"ML detector trained on {len(X)} samples")
    
    def _calculate_zscore(self, value: float, window: MetricWindow) -> float:
        """Calculate z-score for a value."""
        if window.std() == 0:
            return 0.0
        return (value - window.mean()) / window.std()
    
    def _classify_anomaly(self, metric: str, z_score: float) -> AnomalyType:
        """Classify the type of anomaly based on metric name."""
        metric_lower = metric.lower()
        
        if "latency" in metric_lower or "response" in metric_lower or "time" in metric_lower:
            return AnomalyType.LATENCY
        elif "score" in metric_lower or "quality" in metric_lower or "accuracy" in metric_lower:
            return AnomalyType.PERFORMANCE
        elif "error" in metric_lower or "fail" in metric_lower:
            return AnomalyType.FAILURE
        elif "route" in metric_lower or "fallback" in metric_lower:
            return AnomalyType.ROUTING
        else:
            return AnomalyType.BEHAVIOR
    
    def _calculate_severity(self, z_score: float) -> Severity:
        """Calculate severity based on z-score."""
        abs_z = abs(z_score)
        if abs_z > 5:
            return Severity.CRITICAL
        elif abs_z > 4:
            return Severity.HIGH
        elif abs_z > 3:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "tracked_metrics": list(self.windows.keys()),
            "anomalies_detected": len(self.history),
            "recent_anomalies": [
                {"metric": a.metric, "type": a.anomaly_type.value, "severity": a.severity.value}
                for a in self.history[-10:]
            ],
            "ml_enabled": self.use_ml,
            "ml_trained": self.ml_detector is not None,
        }


def create_engine(**kwargs) -> AnomalyEngine:
    """Factory function to create an anomaly engine."""
    return AnomalyEngine(**kwargs)
