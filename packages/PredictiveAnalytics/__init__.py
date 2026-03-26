"""
Predictive Analytics Module

Azure ML-adjacent predictive analytics for forecasting, classification, and regression.
Pure Python + NumPy — no Azure dependency required.

Includes:
- Time series forecasting (ARIMA-lite, moving averages, exponential smoothing)
- Anomaly prediction (predict failures before they happen)
- Trend analysis and forecasting
- Feature importance analysis
- Model selection helpers

Usage:
    from modules.predictive_analytics import TimeSeriesForecaster, TrendAnalyzer

    forecaster = TimeSeriesForecaster()
    forecast = forecaster.forecast(data, periods=30, method='exponential')
    print(forecast.predictions)
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Result from a forecasting operation."""

    predictions: np.ndarray
    confidence_lower: np.ndarray
    confidence_upper: np.ndarray
    method: str
    periods: int
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrendResult:
    """Result from trend analysis."""

    direction: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    r_squared: float
    forecast_next: float
    confidence: float


# ============================================================
# TIME SERIES FORECASTING
# ============================================================


class TimeSeriesForecaster:
    """
    Time series forecasting with multiple methods.

    Methods:
    - 'moving_average': Simple moving average
    - 'exponential': Exponential smoothing (Holt-Winters lite)
    - 'linear': Linear trend extrapolation
    - 'seasonal': Seasonal decomposition + trend

    Usage:
        forecaster = TimeSeriesForecaster()
        result = forecaster.forecast(data, periods=30, method='exponential')
    """

    def forecast(
        self,
        data: np.ndarray,
        periods: int = 30,
        method: str = "exponential",
        window: int = 7,
    ) -> ForecastResult:
        """
        Forecast future values.

        Args:
            data: Historical time series data
            periods: Number of future periods to forecast
            method: Forecasting method
            window: Window size for moving average methods

        Returns:
            ForecastResult with predictions and confidence intervals
        """
        data = np.asarray(data, dtype=float)

        if method == "moving_average":
            return self._moving_average(data, periods, window)
        elif method == "exponential":
            return self._exponential_smoothing(data, periods)
        elif method == "linear":
            return self._linear_forecast(data, periods)
        elif method == "seasonal":
            return self._seasonal_forecast(data, periods, window)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _moving_average(
        self, data: np.ndarray, periods: int, window: int
    ) -> ForecastResult:
        """Simple moving average forecast."""
        if len(data) < window:
            window = max(1, len(data))

        ma = np.convolve(data, np.ones(window) / window, mode="valid")

        # Last moving average value repeated
        last_ma = ma[-1]
        predictions = np.full(periods, last_ma)

        # Confidence based on recent volatility
        std = np.std(data[-window:])
        ci = 1.96 * std

        return ForecastResult(
            predictions=predictions,
            confidence_lower=predictions - ci,
            confidence_upper=predictions + ci,
            method="moving_average",
            periods=periods,
            metrics={"last_ma": last_ma, "window": window, "std": std},
        )

    def _exponential_smoothing(
        self,
        data: np.ndarray,
        periods: int,
        alpha: float = 0.3,
        beta: float = 0.1,
        gamma: float = 0.1,
    ) -> ForecastResult:
        """Holt-Winters exponential smoothing."""
        n = len(data)
        if n < 4:
            return self._linear_forecast(data, periods)

        # Simple exponential smoothing for level
        level = data[0]
        trend = (data[-1] - data[0]) / n if n > 1 else 0

        levels = [level]
        for i in range(1, n):
            new_level = alpha * data[i] + (1 - alpha) * (level + trend)
            trend = beta * (new_level - level) + (1 - beta) * trend
            level = new_level
            levels.append(level)

        # Forecast
        predictions = np.array([level + trend * (i + 1) for i in range(periods)])

        # Confidence intervals (widen over time)
        residuals = data - np.array(levels)
        std = np.std(residuals)
        multipliers = np.sqrt(np.arange(1, periods + 1))
        ci = 1.96 * std * multipliers

        return ForecastResult(
            predictions=predictions,
            confidence_lower=predictions - ci,
            confidence_upper=predictions + ci,
            method="exponential_smoothing",
            periods=periods,
            metrics={"level": level, "trend": trend, "alpha": alpha},
        )

    def _linear_forecast(self, data: np.ndarray, periods: int) -> ForecastResult:
        """Linear trend extrapolation."""
        n = len(data)
        x = np.arange(n)

        # Fit line
        coeffs = np.polyfit(x, data, 1)
        slope, intercept = coeffs[0], coeffs[1]

        # Predict
        future_x = np.arange(n, n + periods)
        predictions = slope * future_x + intercept

        # Confidence
        fitted = slope * x + intercept
        std = np.std(data - fitted)
        ci = 1.96 * std

        return ForecastResult(
            predictions=predictions,
            confidence_lower=predictions - ci,
            confidence_upper=predictions + ci,
            method="linear",
            periods=periods,
            metrics={"slope": slope, "intercept": intercept, "std": std},
        )

    def _seasonal_forecast(
        self, data: np.ndarray, periods: int, season_length: int = 7
    ) -> ForecastResult:
        """Seasonal decomposition + trend forecast."""
        n = len(data)
        if n < season_length * 2:
            return self._linear_forecast(data, periods)

        # Extract seasonal component
        n_seasons = n // season_length
        seasonal = np.zeros(season_length)
        for i in range(season_length):
            indices = [i + j * season_length for j in range(n_seasons)]
            seasonal[i] = np.mean(data[indices])

        # Normalize seasonal
        seasonal = seasonal - np.mean(seasonal)

        # Deseasonalize
        deseasonalized = data - np.tile(seasonal, n_seasons + 1)[:n]

        # Trend on deseasonalized
        trend_result = self._linear_forecast(deseasonalized, periods)

        # Re-seasonalize
        seasonal_forecast = np.tile(seasonal, (periods // season_length) + 1)[:periods]
        predictions = trend_result.predictions + seasonal_forecast

        std = np.std(data - (deseasonalized + np.tile(seasonal, n_seasons + 1)[:n]))
        ci = 1.96 * std

        return ForecastResult(
            predictions=predictions,
            confidence_lower=predictions - ci,
            confidence_upper=predictions + ci,
            method="seasonal",
            periods=periods,
            metrics={"season_length": season_length, "std": std},
        )

    def backtest(
        self, data: np.ndarray, periods: int = 10, method: str = "exponential"
    ) -> Dict[str, float]:
        """
        Backtest forecast accuracy on historical data.

        Holds out the last `periods` values and evaluates forecast quality.
        """
        if len(data) < periods + 10:
            return {"error": "Not enough data for backtest"}

        train = data[:-periods]
        actual = data[-periods:]

        result = self.forecast(train, periods, method)

        mae = np.mean(np.abs(result.predictions - actual))
        rmse = np.sqrt(np.mean((result.predictions - actual) ** 2))
        mape = np.mean(np.abs((actual - result.predictions) / (actual + 1e-10))) * 100

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 2),
            "method": method,
        }


# ============================================================
# TREND ANALYSIS
# ============================================================


class TrendAnalyzer:
    """
    Analyze trends in data series.

    Usage:
        analyzer = TrendAnalyzer()
        trend = analyzer.analyze(sales_data)
        print(trend.direction)  # 'increasing'
        print(trend.forecast_next)  # 42500.5
    """

    def analyze(self, data: np.ndarray, lookback: int = None) -> TrendResult:
        """
        Analyze trend in data.

        Args:
            data: Time series data
            lookback: Number of recent points to analyze (None = all)
        """
        data = np.asarray(data, dtype=float)

        if lookback:
            data = data[-lookback:]

        n = len(data)
        if n < 3:
            return TrendResult(
                direction="stable",
                slope=0.0,
                r_squared=0.0,
                forecast_next=data[-1] if n > 0 else 0.0,
                confidence=0.0,
            )

        x = np.arange(n)

        # Linear regression
        slope, intercept = np.polyfit(x, data, 1)
        fitted = slope * x + intercept

        # R-squared
        ss_res = np.sum((data - fitted) ** 2)
        ss_tot = np.sum((data - np.mean(data)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Direction
        pct_change = (slope * n) / (np.mean(data) + 1e-10) * 100
        if pct_change > 5:
            direction = "increasing"
        elif pct_change < -5:
            direction = "decreasing"
        else:
            direction = "stable"

        # Forecast next point
        forecast_next = slope * n + intercept

        # Confidence based on R-squared and data size
        confidence = min(r_squared * (n / (n + 10)), 1.0)

        return TrendResult(
            direction=direction,
            slope=round(slope, 6),
            r_squared=round(r_squared, 4),
            forecast_next=round(forecast_next, 4),
            confidence=round(confidence, 4),
        )

    def detect_change_points(self, data: np.ndarray, window: int = 5) -> List[int]:
        """
        Detect points where the trend changes significantly.

        Returns indices of change points.
        """
        data = np.asarray(data, dtype=float)
        n = len(data)

        if n < window * 2:
            return []

        change_points = []

        for i in range(window, n - window):
            before = data[i - window : i]
            after = data[i : i + window]

            mean_before = np.mean(before)
            mean_after = np.mean(after)
            pooled_std = np.sqrt((np.var(before) + np.var(after)) / 2)

            if pooled_std > 0:
                effect_size = abs(mean_after - mean_before) / pooled_std
                if effect_size > 1.5:  # Significant change
                    change_points.append(i)

        return change_points


# ============================================================
# ANOMALY PREDICTION
# ============================================================


class AnomalyPredictor:
    """
    Predict anomalies before they happen using statistical methods.

    Based on the SemanticFinder anomaly_engine spec:
    "learn normal behavior → flag deviations → trigger action"

    Usage:
        predictor = AnomalyPredictor()
        predictor.fit(historical_data)
        warning = predictor.check(new_value)
        # {'is_warning': True, 'z_score': 3.2, 'predicted_anomaly': True}
    """

    def __init__(self, z_threshold: float = 2.5, window: int = 20):
        logger.debug(f"Initializing AnomalyPredictor with z_threshold={z_threshold}")
        self.z_threshold = z_threshold
        self.window = window
        self._mean = 0.0
        self._std = 1.0
        self._history = []
        self._fitted = False

    def fit(self, data: np.ndarray):
        """Fit on historical data."""
        data = np.asarray(data, dtype=float)
        self._mean = np.mean(data)
        self._std = np.std(data)
        if self._std == 0:
            self._std = 1.0
        self._history = list(data[-self.window :])
        self._fitted = True
        logger.info(f"AnomalyPredictor fitted on {len(data)} samples")

    def check(self, value: float) -> Dict[str, Any]:
        """
        Check if a new value is anomalous.

        Returns dict with:
        - is_anomaly: bool
        - z_score: float
        - severity: 'normal', 'warning', 'critical'
        - predicted_failure: bool (trend suggests failure coming)
        """
        if not self._fitted:
            return {
                "is_anomaly": False,
                "z_score": 0,
                "severity": "normal",
                "predicted_failure": False,
            }

        z_score = (value - self._mean) / self._std

        # Check for trend toward anomaly
        self._history.append(value)
        if len(self._history) > self.window:
            self._history = self._history[-self.window :]

        recent = (
            np.array(self._history[-5:])
            if len(self._history) >= 5
            else np.array(self._history)
        )
        trend_z = (recent - self._mean) / self._std

        # Predict failure: trend consistently getting worse
        predicted_failure = False
        if len(trend_z) >= 3:
            if np.all(np.diff(trend_z) > 0) and trend_z[-1] > 1.5:
                predicted_failure = True  # Trending toward anomaly
            elif np.all(np.diff(trend_z) < 0) and trend_z[-1] < -1.5:
                predicted_failure = True  # Trending toward anomaly (low side)

        if abs(z_score) > self.z_threshold:
            severity = "critical"
            logger.warning(f"CRITICAL anomaly detected: z_score={z_score:.3f}")
        elif abs(z_score) > self.z_threshold * 0.7:
            severity = "warning"
            logger.debug(f"Warning anomaly detected: z_score={z_score:.3f}")
        else:
            severity = "normal"

        return {
            "is_anomaly": abs(z_score) > self.z_threshold,
            "z_score": round(z_score, 3),
            "severity": severity,
            "predicted_failure": predicted_failure,
        }

    def update(self, value: float):
        """Update statistics with a new (normal) value."""
        self._history.append(value)
        if len(self._history) > self.window:
            self._history = self._history[-self.window :]
        self._mean = np.mean(self._history)
        self._std = np.std(self._history)
        if self._std == 0:
            self._std = 1.0


# ============================================================
# FEATURE IMPORTANCE
# ============================================================


class FeatureImportanceAnalyzer:
    """
    Analyze feature importance for predictive models.

    Uses correlation-based and variance-based importance scores.
    """

    @staticmethod
    def correlation_importance(X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Feature importance based on absolute correlation with target."""
        importances = np.zeros(X.shape[1])
        for i in range(X.shape[1]):
            if np.std(X[:, i]) > 0 and np.std(y) > 0:
                importances[i] = abs(np.corrcoef(X[:, i], y)[0, 1])
            else:
                importances[i] = 0
        # Normalize
        total = np.sum(importances)
        if total > 0:
            importances = importances / total
        return importances

    @staticmethod
    def variance_importance(X: np.ndarray) -> np.ndarray:
        """Feature importance based on variance (higher variance = more informative)."""
        variances = np.var(X, axis=0)
        total = np.sum(variances)
        if total > 0:
            return variances / total
        return np.zeros(X.shape[1])

    @staticmethod
    def rank_features(
        X: np.ndarray, y: np.ndarray, feature_names: List[str] = None
    ) -> List[Tuple[str, float]]:
        """Rank features by combined importance score."""
        n_features = X.shape[1]
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]

        corr = FeatureImportanceAnalyzer.correlation_importance(X, y)
        var = FeatureImportanceAnalyzer.variance_importance(X)

        combined = corr * 0.7 + var * 0.3

        ranked = sorted(zip(feature_names, combined), key=lambda x: x[1], reverse=True)
        return ranked


# Convenience function
def forecast(data, periods=30, method="exponential"):
    """Quick forecast of time series data."""
    forecaster = TimeSeriesForecaster()
    return forecaster.forecast(np.asarray(data), periods, method)
