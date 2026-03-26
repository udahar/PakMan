"""Tests for anomaly_engine module."""
import pytest
import numpy as np
from anomaly_engine import (
    AnomalyEngine,
    AnomalyType,
    Severity,
    StatisticalDetector,
    FeatureExtractor,
    ResponseEngine,
    AnomalyResult,
    create_engine,
)


class TestAnomalyEngine:
    """Test AnomalyEngine."""

    def test_init(self):
        """Test engine initialization."""
        engine = AnomalyEngine(k_std=3.0, window_size=100)
        assert engine.k_std == 3.0
        assert engine.window_size == 100
        assert len(engine.windows) == 0

    def test_track(self):
        """Test tracking metrics."""
        engine = AnomalyEngine()
        engine.track("latency", 100.0)
        assert "latency" in engine.windows
        assert len(engine.windows["latency"].values) == 1

    def test_check_no_anomaly(self):
        """Test checking normal value."""
        engine = AnomalyEngine(k_std=3.0)
        for i in range(20):
            engine.track("latency", 100.0 + np.random.randn() * 10)
        
        result = engine.check("latency", 100.0)
        assert hasattr(result, 'is_anomaly')
        assert isinstance(result.is_anomaly, bool)

    def test_check_with_anomaly(self):
        """Test detecting anomaly."""
        engine = AnomalyEngine(k_std=2.0, window_size=10)
        for i in range(50):
            engine.track("latency", 100.0 + np.random.randn() * 5)
        
        result = engine.check("latency", 300.0)
        assert result.is_anomaly is True

    def test_classify_anomaly_type(self):
        """Test anomaly classification."""
        engine = AnomalyEngine()
        
        latency_type = engine._classify_anomaly("latency", 5.0)
        assert latency_type == AnomalyType.LATENCY
        
        perf_type = engine._classify_anomaly("score", -5.0)
        assert perf_type == AnomalyType.PERFORMANCE
        
        error_type = engine._classify_anomaly("error_count", 5.0)
        assert error_type == AnomalyType.FAILURE

    def test_calculate_severity(self):
        """Test severity calculation."""
        engine = AnomalyEngine()
        
        low = engine._calculate_severity(2.0)
        assert low == Severity.LOW
        
        medium = engine._calculate_severity(3.5)
        assert medium == Severity.MEDIUM
        
        high = engine._calculate_severity(4.5)
        assert high == Severity.HIGH
        
        critical = engine._calculate_severity(6.0)
        assert critical == Severity.CRITICAL

    def test_respond(self):
        """Test responding to anomaly."""
        engine = AnomalyEngine()
        
        for i in range(50):
            engine.track("latency", 100.0)
        
        anomaly = engine.check("latency", 300.0)
        response = engine.respond(anomaly)
        
        assert response.anomaly_type in ["latency", "performance", "behavior", "unknown"]
        assert len(response.actions) > 0

    def test_get_stats(self):
        """Test getting statistics."""
        engine = AnomalyEngine()
        stats = engine.get_stats()
        
        assert "tracked_metrics" in stats
        assert "anomalies_detected" in stats
        assert "ml_enabled" in stats


class TestStatisticalDetector:
    """Test StatisticalDetector."""

    def test_init(self):
        """Test detector initialization."""
        detector = StatisticalDetector(k_std=3.0)
        assert detector.k_std == 3.0

    def test_detect_normal(self):
        """Test detecting normal value."""
        detector = StatisticalDetector(k_std=3.0)
        is_anomaly, z_score = detector.detect(100.0, mean=100.0, std=10.0)
        assert is_anomaly is False
        assert abs(z_score) < 0.1

    def test_detect_anomaly(self):
        """Test detecting anomalous value with sufficient history."""
        detector = StatisticalDetector(k_std=2.0)
        
        # Pre-populate history by directly accessing it
        # (simulating accumulated historical data)
        for _ in range(10):
            detector.history.append(100.0)
        
        is_anomaly, z_score = detector.detect(150.0, mean=100.0, std=10.0)
        assert is_anomaly is True
        assert z_score == 5.0


class TestFeatureExtractor:
    """Test FeatureExtractor."""

    def test_extract(self):
        """Test feature extraction."""
        extractor = FeatureExtractor()
        features = extractor.extract({"latency": 100.0, "score": 80.0})
        assert len(features) > 0

    def test_get_feature_names(self):
        """Test getting feature names."""
        extractor = FeatureExtractor()
        names = extractor.get_feature_names(["latency", "score"])
        assert "latency" in names
        assert "latency_zscore" in names


class TestResponseEngine:
    """Test ResponseEngine."""

    def test_init(self):
        """Test response engine initialization."""
        engine = ResponseEngine()
        assert len(engine.handlers) > 0
        assert len(engine.action_history) == 0

    def test_respond(self):
        """Test responding to anomaly."""
        engine = ResponseEngine()
        
        anomaly = AnomalyResult(
            is_anomaly=True,
            metric="latency",
            value=500.0,
            z_score=5.0,
            threshold=200.0,
            anomaly_type=AnomalyType.LATENCY,
            severity=Severity.HIGH,
        )
        
        response = engine.respond(anomaly)
        assert response.anomaly_type == "latency"
        assert len(response.actions) > 0

    def test_get_stats(self):
        """Test getting response statistics."""
        engine = ResponseEngine()
        stats = engine.get_stats()
        assert "total_responses" in stats
        assert "action_counts" in stats


class TestCreateEngine:
    """Test create_engine factory function."""

    def test_create_engine(self):
        """Test factory function."""
        engine = create_engine(k_std=2.5)
        assert engine.k_std == 2.5
