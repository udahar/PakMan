import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from .models import AnomalyType, StockAnomaly

class StockAnomalyDetector:
    """
    Detect anomalies in stock time series data.

    Methods:
    - Z-score based price/volume spikes
    - Rolling volatility regime detection
    - Gap detection (overnight moves)
    - Trend break detection (structural changes)
    - Isolation-style outlier scoring

    Usage:
        detector = StockAnomalyDetector(z_threshold=2.5)
        anomalies = detector.detect_all(df, symbol='AAPL')

        for a in anomalies:
            print(f"[{a.severity}] {a.date}: {a.description}")
    """

    def __init__(self, z_threshold: float = 2.5, lookback: int = 60):
        self.z_threshold = z_threshold
        self.lookback = lookback

    def detect_all(self, df: pd.DataFrame, symbol: str = "") -> List[StockAnomaly]:
        """
        Run all anomaly detectors on stock data.

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol for labeling

        Returns:
            List of StockAnomaly objects, sorted by severity
        """
        anomalies = []

        anomalies.extend(self.detect_price_anomalies(df, symbol))
        anomalies.extend(self.detect_volume_anomalies(df, symbol))
        anomalies.extend(self.detect_volatility_anomalies(df, symbol))
        anomalies.extend(self.detect_gaps(df, symbol))
        anomalies.extend(self.detect_trend_breaks(df, symbol))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 4))

        return anomalies

    def detect_price_anomalies(
        self, df: pd.DataFrame, symbol: str = ""
    ) -> List[StockAnomaly]:
        """Detect price spikes and crashes."""
        anomalies = []
        close = df["Close"].values
        returns = np.diff(close) / close[:-1]

        if len(returns) < self.lookback:
            return anomalies

        for i in range(self.lookback, len(returns)):
            window = returns[max(0, i - self.lookback) : i]
            mean_ret = np.mean(window)
            std_ret = np.std(window)

            if std_ret == 0:
                continue

            z = (returns[i] - mean_ret) / std_ret

            if z > self.z_threshold:
                severity = "critical" if z > 4 else "high" if z > 3 else "medium"
                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.PRICE_SPIKE.value,
                        date=df.index[i + 1],
                        symbol=symbol,
                        severity=severity,
                        z_score=round(z, 3),
                        description=f"Price spike: +{returns[i]:.2%} (expected: {mean_ret:.2%})",
                        value=returns[i],
                        expected_value=mean_ret,
                        details={
                            "price": close[i + 1],
                            "prev_price": close[i],
                            "change_pct": round(returns[i] * 100, 2),
                        },
                    )
                )

            elif z < -self.z_threshold:
                severity = "critical" if z < -4 else "high" if z < -3 else "medium"
                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.PRICE_CRASH.value,
                        date=df.index[i + 1],
                        symbol=symbol,
                        severity=severity,
                        z_score=round(z, 3),
                        description=f"Price crash: {returns[i]:.2%} (expected: {mean_ret:.2%})",
                        value=returns[i],
                        expected_value=mean_ret,
                        details={
                            "price": close[i + 1],
                            "prev_price": close[i],
                            "change_pct": round(returns[i] * 100, 2),
                        },
                    )
                )

        return anomalies

    def detect_volume_anomalies(
        self, df: pd.DataFrame, symbol: str = ""
    ) -> List[StockAnomaly]:
        """Detect volume surges and dry-ups."""
        anomalies = []

        if "Volume" not in df.columns:
            return anomalies

        volume = df["Volume"].values.astype(float)

        if len(volume) < self.lookback:
            return anomalies

        # Log volume for better distribution
        log_vol = np.log1p(volume)

        for i in range(self.lookback, len(volume)):
            window = log_vol[max(0, i - self.lookback) : i]
            mean_vol = np.mean(window)
            std_vol = np.std(window)

            if std_vol == 0:
                continue

            z = (log_vol[i] - mean_vol) / std_vol

            if z > self.z_threshold:
                ratio = volume[i] / np.mean(volume[max(0, i - self.lookback) : i])
                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.VOLUME_SURGE.value,
                        date=df.index[i],
                        symbol=symbol,
                        severity="high" if z > 3.5 else "medium",
                        z_score=round(z, 3),
                        description=f"Volume surge: {ratio:.1f}x average ({volume[i]:,.0f} shares)",
                        value=volume[i],
                        expected_value=np.mean(volume[max(0, i - self.lookback) : i]),
                        details={"volume_ratio": round(ratio, 2)},
                    )
                )

            elif z < -self.z_threshold:
                ratio = volume[i] / np.mean(volume[max(0, i - self.lookback) : i])
                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.VOLUME_DRY_UP.value,
                        date=df.index[i],
                        symbol=symbol,
                        severity="low",
                        z_score=round(z, 3),
                        description=f"Volume dry-up: {ratio:.1%} of average ({volume[i]:,.0f} shares)",
                        value=volume[i],
                        expected_value=np.mean(volume[max(0, i - self.lookback) : i]),
                        details={"volume_ratio": round(ratio, 2)},
                    )
                )

        return anomalies

    def detect_volatility_anomalies(
        self, df: pd.DataFrame, symbol: str = ""
    ) -> List[StockAnomaly]:
        """Detect volatility spikes and regime changes."""
        anomalies = []
        close = df["Close"].values
        returns = np.diff(close) / close[:-1]

        if len(returns) < self.lookback * 2:
            return anomalies

        # Rolling volatility
        vol_window = 20
        rolling_vol = pd.Series(returns).rolling(vol_window).std().values * np.sqrt(252)

        # Detect volatility spikes
        vol_lookback = self.lookback
        for i in range(vol_lookback, len(rolling_vol)):
            if np.isnan(rolling_vol[i]):
                continue

            window = rolling_vol[max(0, i - vol_lookback) : i]
            window = window[~np.isnan(window)]

            if len(window) < 10:
                continue

            mean_vol = np.mean(window)
            std_vol = np.std(window)

            if std_vol == 0:
                continue

            z = (rolling_vol[i] - mean_vol) / std_vol

            if z > self.z_threshold:
                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.VOLATILITY_SPIKE.value,
                        date=df.index[i + 1] if i + 1 < len(df.index) else df.index[-1],
                        symbol=symbol,
                        severity="high" if z > 3.5 else "medium",
                        z_score=round(z, 3),
                        description=f"Volatility spike: {rolling_vol[i]:.1%} annualized (avg: {mean_vol:.1%})",
                        value=rolling_vol[i],
                        expected_value=mean_vol,
                        details={
                            "current_vol": round(rolling_vol[i], 4),
                            "avg_vol": round(mean_vol, 4),
                        },
                    )
                )

        # Detect regime changes (significant shift in volatility level)
        half = len(rolling_vol) // 2
        if half > vol_window:
            first_half = rolling_vol[:half]
            second_half = rolling_vol[half:]
            first_clean = first_half[~np.isnan(first_half)]
            second_clean = second_half[~np.isnan(second_half)]

            if len(first_clean) > 10 and len(second_clean) > 10:
                mean_first = np.mean(first_clean)
                mean_second = np.mean(second_clean)
                ratio = mean_second / mean_first if mean_first > 0 else 1

                if ratio > 2.0 or ratio < 0.5:
                    anomalies.append(
                        StockAnomaly(
                            type=AnomalyType.VOLATILITY_REGIME_CHANGE.value,
                            date=df.index[half],
                            symbol=symbol,
                            severity="high",
                            z_score=round(abs(ratio - 1), 3),
                            description=f"Volatility regime change: {ratio:.1f}x shift",
                            value=mean_second,
                            expected_value=mean_first,
                            details={
                                "before_vol": round(mean_first, 4),
                                "after_vol": round(mean_second, 4),
                                "ratio": round(ratio, 2),
                            },
                        )
                    )

        return anomalies

    def detect_gaps(self, df: pd.DataFrame, symbol: str = "") -> List[StockAnomaly]:
        """Detect gap up/down (overnight moves)."""
        anomalies = []

        if "Open" not in df.columns or "Close" not in df.columns:
            return anomalies

        opens = df["Open"].values
        prev_close = df["Close"].shift(1).values
        gaps = (opens - prev_close) / prev_close

        if len(gaps) < self.lookback:
            return anomalies

        for i in range(1, len(gaps)):
            if np.isnan(gaps[i]) or np.isnan(prev_close[i]):
                continue

            # Calculate z-score of gap
            start = max(0, i - self.lookback)
            window = gaps[start:i]
            window = window[~np.isnan(window)]

            if len(window) < 10 or np.std(window) == 0:
                continue

            z = (gaps[i] - np.mean(window)) / np.std(window)

            if abs(z) > self.z_threshold:
                if gaps[i] > 0:
                    anomaly_type = AnomalyType.GAP_UP.value
                    desc = f"Gap up: +{gaps[i]:.2%}"
                else:
                    anomaly_type = AnomalyType.GAP_DOWN.value
                    desc = f"Gap down: {gaps[i]:.2%}"

                severity = (
                    "critical" if abs(z) > 4 else "high" if abs(z) > 3 else "medium"
                )

                anomalies.append(
                    StockAnomaly(
                        type=anomaly_type,
                        date=df.index[i],
                        symbol=symbol,
                        severity=severity,
                        z_score=round(z, 3),
                        description=desc,
                        value=gaps[i],
                        expected_value=np.mean(window),
                        details={
                            "open": opens[i],
                            "prev_close": prev_close[i],
                            "gap_pct": round(gaps[i] * 100, 2),
                        },
                    )
                )

        return anomalies

    def detect_trend_breaks(
        self, df: pd.DataFrame, symbol: str = "", window: int = 60
    ) -> List[StockAnomaly]:
        """
        Detect structural breaks in trend.

        Uses CUSUM-like approach to detect when price breaks
        away from its established trend.
        """
        anomalies = []
        close = df["Close"].values

        if len(close) < window * 2:
            return anomalies

        # Fit trend on rolling windows and check for breaks
        for i in range(window, len(close) - window // 2):
            # Trend in first half of window
            pre_trend = close[i - window : i]
            x = np.arange(len(pre_trend))
            slope, intercept = np.polyfit(x, pre_trend, 1)

            # Expected value based on trend
            expected = slope * window + intercept
            actual = close[i]

            if expected == 0:
                continue

            deviation = (actual - expected) / expected

            # Calculate significance
            residuals = pre_trend - (slope * x + intercept)
            std = np.std(residuals)

            if std == 0:
                continue

            z = (actual - expected) / std

            if abs(z) > self.z_threshold:
                direction = "upward" if z > 0 else "downward"
                severity = (
                    "critical" if abs(z) > 4 else "high" if abs(z) > 3 else "medium"
                )

                anomalies.append(
                    StockAnomaly(
                        type=AnomalyType.TREND_BREAK.value,
                        date=df.index[i],
                        symbol=symbol,
                        severity=severity,
                        z_score=round(z, 3),
                        description=f"Trend break ({direction}): price {actual:.2f} vs expected {expected:.2f} ({deviation:+.1%})",
                        value=actual,
                        expected_value=expected,
                        details={
                            "trend_slope": round(slope, 4),
                            "deviation_pct": round(deviation * 100, 2),
                            "direction": direction,
                        },
                    )
                )

        # Deduplicate (keep most significant per cluster)
        return self._deduplicate(anomalies)

    def isolation_score(self, values: np.ndarray, idx: int) -> float:
        """
        Compute isolation-style anomaly score for a single point.

        Higher score = more anomalous.
        """
        if len(values) < 10:
            return 0.0

        val = values[idx]
        sorted_vals = np.sort(values)

        # Find position in sorted array
        rank = np.searchsorted(sorted_vals, val)

        # Check distance to nearest neighbors
        left_idx = max(0, rank - 3)
        right_idx = min(len(sorted_vals), rank + 3)
        neighbors = sorted_vals[left_idx:right_idx]

        if len(neighbors) < 2:
            return 0.0

        distances = np.abs(neighbors - val)
        avg_dist = np.mean(distances[distances > 0]) if np.any(distances > 0) else 0

        # Normalize by IQR
        q75, q25 = np.percentile(values, [75, 25])
        iqr = q75 - q25

        if iqr == 0:
            return 0.0

        return avg_dist / iqr

    def get_summary(self, anomalies: List[StockAnomaly]) -> Dict[str, Any]:
        """Summarize anomalies."""
        by_type = {}
        by_severity = {}

        for a in anomalies:
            by_type[a.type] = by_type.get(a.type, 0) + 1
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

        return {
            "total": len(anomalies),
            "by_type": by_type,
            "by_severity": by_severity,
            "critical_count": by_severity.get("critical", 0),
            "high_count": by_severity.get("high", 0),
            "most_recent": anomalies[0].__dict__ if anomalies else None,
        }

    def print_anomaly_report(
        self, anomalies: List[StockAnomaly], symbol: str = "", max_show: int = 20
    ):
        """Print a formatted anomaly report."""
        print(f"\n{'=' * 70}")
        print(f"  Anomaly Report: {symbol or 'Stock'}")
        print(f"{'=' * 70}")

        if not anomalies:
            print("  No anomalies detected.")
            return

        summary = self.get_summary(anomalies)
        print(f"  Total anomalies: {summary['total']}")
        print(f"  Critical: {summary['critical_count']}")
        print(f"  High: {summary['high_count']}")

        print(
            f"\n  {'Date':<12} {'Type':<22} {'Severity':<10} {'Z-Score':>8}  Description"
        )
        print(f"  {'-' * 70}")

        for a in anomalies[:max_show]:
            date_str = str(a.date)[:10] if hasattr(a.date, "__str__") else str(a.date)
            print(
                f"  {date_str:<12} {a.type:<22} {a.severity:<10} {a.z_score:>8.2f}  {a.description}"
            )

        if len(anomalies) > max_show:
            print(f"  ... and {len(anomalies) - max_show} more")

    def _deduplicate(
        self, anomalies: List[StockAnomaly], min_gap: int = 5
    ) -> List[StockAnomaly]:
        """Remove duplicate anomalies that are too close together."""
        if not anomalies:
            return anomalies

        keep = [anomalies[0]]
        for a in anomalies[1:]:
            # Check if this is far enough from last kept anomaly
            if hasattr(a, "date") and hasattr(keep[-1], "date"):
                try:
                    diff = abs((a.date - keep[-1].date).days)
                    if diff >= min_gap or a.severity in ("critical", "high"):
                        keep.append(a)
                    elif a.z_score > keep[-1].z_score:
                        keep[-1] = a
                except (TypeError, AttributeError):
                    keep.append(a)
            else:
                keep.append(a)

        return keep


# Convenience functions
def detect_anomalies(df, symbol="", z_threshold=2.5):
    """Quick anomaly detection on stock data."""
    detector = StockAnomalyDetector(z_threshold=z_threshold)
    return detector.detect_all(df, symbol)


def anomaly_score(df, symbol=""):
    """Quick anomaly scoring."""
    detector = StockAnomalyDetector()
    anomalies = detector.detect_all(df, symbol)
    return detector.get_summary(anomalies)


