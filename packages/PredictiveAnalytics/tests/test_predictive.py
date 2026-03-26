"""Tests for predictive_analytics module."""
import pytest
import numpy as np
from predictive_analytics import (
    TimeSeriesForecaster,
    TrendAnalyzer,
    AnomalyPredictor,
    FeatureImportanceAnalyzer,
    ForecastResult,
    forecast,
)


class TestTimeSeriesForecaster:
    """Test TimeSeriesForecaster."""

    def test_moving_average_forecast(self):
        """Test moving average forecasting."""
        forecaster = TimeSeriesForecaster()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = forecaster.forecast(data, periods=3, method="moving_average")
        assert isinstance(result, ForecastResult)
        assert len(result.predictions) == 3

    def test_exponential_forecast(self):
        """Test exponential smoothing."""
        forecaster = TimeSeriesForecaster()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = forecaster.forecast(data, periods=3, method="exponential")
        assert isinstance(result, ForecastResult)

    def test_linear_forecast(self):
        """Test linear forecasting."""
        forecaster = TimeSeriesForecaster()
        data = np.array([1, 2, 3, 4, 5])
        result = forecaster.forecast(data, periods=2, method="linear")
        assert len(result.predictions) == 2

    def test_seasonal_forecast(self):
        """Test seasonal forecasting."""
        forecaster = TimeSeriesForecaster()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
        result = forecaster.forecast(data, periods=7, method="seasonal")
        assert len(result.predictions) == 7

    def test_backtest(self):
        """Test backtesting."""
        forecaster = TimeSeriesForecaster()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        result = forecaster.backtest(data, periods=3)
        assert "mae" in result
        assert "rmse" in result


class TestTrendAnalyzer:
    """Test TrendAnalyzer."""

    def test_analyze_increasing(self):
        """Test increasing trend detection."""
        analyzer = TrendAnalyzer()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = analyzer.analyze(data)
        assert result.direction == "increasing"
        assert result.slope > 0

    def test_analyze_decreasing(self):
        """Test decreasing trend detection."""
        analyzer = TrendAnalyzer()
        data = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        result = analyzer.analyze(data)
        assert result.direction == "decreasing"
        assert result.slope < 0

    def test_analyze_stable(self):
        """Test stable trend detection."""
        analyzer = TrendAnalyzer()
        data = np.array([5, 5, 5, 5, 5])
        result = analyzer.analyze(data)
        assert result.direction == "stable"

    def test_detect_change_points(self):
        """Test change point detection."""
        analyzer = TrendAnalyzer()
        data = np.array([1, 2, 1, 2, 1, 10, 11, 10, 11])
        changes = analyzer.detect_change_points(data, window=2)
        assert isinstance(changes, list)


class TestAnomalyPredictor:
    """Test AnomalyPredictor."""

    def test_init(self):
        """Test initialization."""
        predictor = AnomalyPredictor(z_threshold=2.5)
        assert predictor.z_threshold == 2.5

    def test_fit(self):
        """Test fitting on data."""
        predictor = AnomalyPredictor()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        predictor.fit(data)
        assert predictor._fitted

    def test_check_normal(self):
        """Test checking normal value."""
        predictor = AnomalyPredictor()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        predictor.fit(data)
        result = predictor.check(5.5)
        assert "is_anomaly" in result
        assert "z_score" in result

    def test_check_anomaly(self):
        """Test checking anomalous value."""
        predictor = AnomalyPredictor(z_threshold=1.0)
        data = np.array([1, 2, 3, 4, 5])
        predictor.fit(data)
        result = predictor.check(100)
        assert result["is_anomaly"] or result["z_score"] > 1.0

    def test_update(self):
        """Test updating with new value."""
        predictor = AnomalyPredictor()
        data = np.array([1, 2, 3, 4, 5])
        predictor.fit(data)
        predictor.update(6)


class TestFeatureImportanceAnalyzer:
    """Test FeatureImportanceAnalyzer."""

    def test_correlation_importance(self):
        """Test correlation-based importance."""
        X = np.array([[1, 2], [2, 4], [3, 6], [4, 8]])
        y = np.array([1, 2, 3, 4])
        importance = FeatureImportanceAnalyzer.correlation_importance(X, y)
        assert len(importance) == 2

    def test_variance_importance(self):
        """Test variance-based importance."""
        X = np.array([[1, 2], [2, 4], [3, 6], [4, 8]])
        importance = FeatureImportanceAnalyzer.variance_importance(X)
        assert len(importance) == 2

    def test_rank_features(self):
        """Test feature ranking."""
        X = np.array([[1, 2], [2, 4], [3, 6], [4, 8]])
        y = np.array([1, 2, 3, 4])
        ranked = FeatureImportanceAnalyzer.rank_features(X, y, ["feature1", "feature2"])
        assert len(ranked) == 2


class TestForecastConvenience:
    """Test forecast convenience function."""

    def test_forecast(self):
        """Test forecast convenience function."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = forecast(data, periods=3)
        assert isinstance(result, ForecastResult)
