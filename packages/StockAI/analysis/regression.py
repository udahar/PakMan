"""
Regression Analytics for StockAI

Price prediction, trend regression, factor analysis, and correlation modeling.
Linear, polynomial, and multiple regression for stock data.

Usage:
    from StockAI.analysis.regression import RegressionAnalyzer

    ra = RegressionAnalyzer()
    result = ra.linear_regression(df)
    print(result.slope, result.r_squared, result.predictions)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class RegressionResult:
    """Result from a regression analysis."""

    slope: float
    intercept: float
    r_squared: float
    adj_r_squared: float
    std_error: float
    predictions: np.ndarray
    residuals: np.ndarray
    coefficients: Dict[str, float]
    forecast: Optional[np.ndarray] = None
    confidence_lower: Optional[np.ndarray] = None
    confidence_upper: Optional[np.ndarray] = None


@dataclass
class FactorAnalysis:
    """Correlation and factor analysis between stocks."""

    correlations: pd.DataFrame
    top_correlations: List[Tuple[str, str, float]]
    beta: Dict[str, float]
    r_squared_vs_market: Dict[str, float]
    factor_loadings: Optional[Dict[str, Dict[str, float]]] = None


class RegressionAnalyzer:
    """
    Regression analysis for stock data.

    Supports:
    - Linear regression (price vs time)
    - Polynomial regression (quadratic, cubic trends)
    - Multiple regression (volume, volatility as predictors)
    - Rolling regression (time-varying relationships)
    - Factor analysis (cross-stock correlations, beta)
    - Forecasting with confidence intervals

    Usage:
        ra = RegressionAnalyzer()
        result = ra.linear_regression(df)
        print(f"Slope: {result.slope:.4f}, R²: {result.r_squared:.3f}")

        forecast = ra.forecast_price(df, days=30)
        print(f"30-day forecast: {forecast}")
    """

    def linear_regression(
        self, df: pd.DataFrame, y_col: str = "Close", x_col: str = None
    ) -> RegressionResult:
        """
        Fit linear regression: y = slope * x + intercept.

        Args:
            df: DataFrame with stock data
            y_col: Column to predict (default: Close)
            x_col: Column for x-axis (default: sequential index)

        Returns:
            RegressionResult with fitted model
        """
        y = df[y_col].values.astype(float)

        if x_col:
            x = df[x_col].values.astype(float)
        else:
            x = np.arange(len(y), dtype=float)

        # Remove NaN
        mask = ~(np.isnan(y) | np.isnan(x))
        x, y = x[mask], y[mask]

        # Fit
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs[0], coeffs[1]

        predictions = slope * x + intercept
        residuals = y - predictions

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        n = len(y)
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - 2) if n > 2 else r_squared

        # Standard error
        std_error = np.sqrt(ss_res / (n - 2)) if n > 2 else 0

        return RegressionResult(
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            adj_r_squared=adj_r_squared,
            std_error=std_error,
            predictions=predictions,
            residuals=residuals,
            coefficients={"slope": slope, "intercept": intercept},
        )

    def polynomial_regression(
        self, df: pd.DataFrame, degree: int = 2, y_col: str = "Close"
    ) -> RegressionResult:
        """
        Fit polynomial regression.

        Args:
            df: DataFrame with stock data
            degree: Polynomial degree (2=quadratic, 3=cubic)
            y_col: Column to predict
        """
        y = df[y_col].values.astype(float)
        x = np.arange(len(y), dtype=float)

        mask = ~np.isnan(y)
        x, y = x[mask], y[mask]

        coeffs = np.polyfit(x, y, degree)
        predictions = np.polyval(coeffs, x)
        residuals = y - predictions

        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        n = len(y)
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - degree - 1)

        coeff_dict = {f"x^{i}": c for i, c in enumerate(reversed(coeffs))}

        return RegressionResult(
            slope=coeffs[0],
            intercept=coeffs[-1],
            r_squared=r_squared,
            adj_r_squared=adj_r_squared,
            std_error=np.sqrt(ss_res / (n - degree - 1)) if n > degree + 1 else 0,
            predictions=predictions,
            residuals=residuals,
            coefficients=coeff_dict,
        )

    def multiple_regression(
        self, df: pd.DataFrame, y_col: str = "Close", x_cols: List[str] = None
    ) -> RegressionResult:
        """
        Multiple regression with volume, volatility, etc. as predictors.

        Args:
            df: DataFrame with stock data
            y_col: Target column
            x_cols: Predictor columns (default: Volume + returns + volatility)
        """
        df = df.copy()

        if x_cols is None:
            # Build features from OHLCV
            df["Returns"] = df["Close"].pct_change()
            df["Volatility"] = df["Returns"].rolling(20).std()
            df["Volume_Change"] = (
                df["Volume"].pct_change() if "Volume" in df.columns else 0
            )
            df["High_Low_Range"] = (df["High"] - df["Low"]) / df["Close"]
            df["Price_MA20"] = df["Close"].rolling(20).mean()
            df["Price_vs_MA"] = (df["Close"] - df["Price_MA20"]) / df["Price_MA20"]
            x_cols = ["Volume_Change", "Volatility", "High_Low_Range", "Price_vs_MA"]

        # Build matrix
        available_cols = [c for c in x_cols if c in df.columns]
        df_clean = df[[y_col] + available_cols].dropna()

        if len(df_clean) < 10:
            # Fall back to simple linear
            return self.linear_regression(df, y_col)

        y = df_clean[y_col].values
        X = df_clean[available_cols].values

        # Add intercept
        X_b = np.column_stack([np.ones(len(X)), X])

        # Normal equation
        try:
            beta = np.linalg.lstsq(X_b, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            return self.linear_regression(df, y_col)

        predictions = X_b @ beta
        residuals = y - predictions

        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        n, p = X_b.shape
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)

        coeff_dict = {"intercept": beta[0]}
        for i, col in enumerate(available_cols):
            coeff_dict[col] = beta[i + 1]

        return RegressionResult(
            slope=beta[1] if len(beta) > 1 else 0,
            intercept=beta[0],
            r_squared=r_squared,
            adj_r_squared=adj_r_squared,
            std_error=np.sqrt(ss_res / (n - p)) if n > p else 0,
            predictions=predictions,
            residuals=residuals,
            coefficients=coeff_dict,
        )

    def rolling_regression(
        self, df: pd.DataFrame, window: int = 60, y_col: str = "Close"
    ) -> pd.DataFrame:
        """
        Rolling window regression to detect changing relationships.

        Returns DataFrame with rolling slope, R², and intercept over time.
        """
        y = df[y_col].values
        results = []

        for i in range(window, len(y)):
            window_y = y[i - window : i]
            x = np.arange(window, dtype=float)

            coeffs = np.polyfit(x, window_y, 1)
            predictions = coeffs[0] * x + coeffs[1]

            ss_res = np.sum((window_y - predictions) ** 2)
            ss_tot = np.sum((window_y - np.mean(window_y)) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            results.append(
                {
                    "date": df.index[i],
                    "slope": coeffs[0],
                    "intercept": coeffs[1],
                    "r_squared": r2,
                }
            )

        return pd.DataFrame(results).set_index("date")

    def forecast_price(
        self,
        df: pd.DataFrame,
        days: int = 30,
        method: str = "linear",
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Forecast future prices with confidence intervals.

        Args:
            df: DataFrame with stock data
            days: Number of days to forecast
            method: 'linear', 'polynomial', or 'exponential'
            confidence: Confidence level (0.95 = 95%)

        Returns:
            Dict with predictions, confidence intervals, and stats
        """
        y = df["Close"].values.astype(float)
        y = y[~np.isnan(y)]
        n = len(y)
        x = np.arange(n, dtype=float)

        if method == "polynomial":
            result = self.polynomial_regression(df, degree=2)
            future_x = np.arange(n, n + days)
            predictions = np.polyval(np.polyfit(x, y, 2), future_x)
        else:
            result = self.linear_regression(df)
            future_x = np.arange(n, n + days)
            predictions = result.slope * future_x + result.intercept

        # Confidence intervals (widen over time)
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        se = result.std_error
        multipliers = np.sqrt(1 + np.arange(1, days + 1) / n)
        ci = z * se * multipliers

        last_date = df.index[-1]

        return {
            "predictions": predictions,
            "confidence_lower": predictions - ci,
            "confidence_upper": predictions + ci,
            "last_price": y[-1],
            "predicted_end": predictions[-1],
            "predicted_change_pct": (predictions[-1] / y[-1] - 1) * 100,
            "method": method,
            "r_squared": result.r_squared,
            "days": days,
        }

    def factor_analysis(
        self, data: Dict[str, pd.DataFrame], benchmark_symbol: str = None
    ) -> FactorAnalysis:
        """
        Cross-stock correlation and factor analysis.

        Args:
            data: Dict of symbol -> DataFrame
            benchmark_symbol: Benchmark for beta calculation (e.g., 'SPY')

        Returns:
            FactorAnalysis with correlations, betas, and factor loadings
        """
        # Build returns matrix
        returns = {}
        for symbol, df in data.items():
            if "Close" in df.columns:
                returns[symbol] = df["Close"].pct_change().dropna()

        returns_df = pd.DataFrame(returns).dropna()

        # Correlation matrix
        corr_matrix = returns_df.corr()

        # Top correlations
        pairs = []
        symbols = corr_matrix.columns.tolist()
        for i, s1 in enumerate(symbols):
            for j, s2 in enumerate(symbols):
                if i < j:
                    corr = corr_matrix.loc[s1, s2]
                    if not np.isnan(corr):
                        pairs.append((s1, s2, round(corr, 4)))

        pairs.sort(key=lambda x: abs(x[2]), reverse=True)

        # Beta calculation (vs benchmark or market average)
        betas = {}
        r_squared_market = {}

        if benchmark_symbol and benchmark_symbol in returns_df.columns:
            market_returns = returns_df[benchmark_symbol]
            for symbol in returns_df.columns:
                if symbol != benchmark_symbol:
                    stock_returns = returns_df[symbol]
                    cov = np.cov(stock_returns, market_returns)
                    var_market = np.var(market_returns)
                    beta = cov[0, 1] / var_market if var_market > 0 else 1.0

                    # R² vs market
                    corr = np.corrcoef(stock_returns, market_returns)[0, 1]
                    r2 = corr**2 if not np.isnan(corr) else 0

                    betas[symbol] = round(beta, 3)
                    r_squared_market[symbol] = round(r2, 3)

        return FactorAnalysis(
            correlations=corr_matrix,
            top_correlations=pairs[:20],
            beta=betas,
            r_squared_vs_market=r_squared_market,
        )

    def residual_analysis(
        self, df: pd.DataFrame, y_col: str = "Close"
    ) -> Dict[str, Any]:
        """
        Analyze regression residuals for patterns.

        Useful for detecting:
        - Autocorrelation (residuals not random)
        - Heteroscedasticity (changing variance)
        - Outliers (unusual price moves)
        """
        result = self.linear_regression(df, y_col)
        residuals = result.residuals

        # Residual stats
        mean_resid = np.mean(residuals)
        std_resid = np.std(residuals)

        # Outliers (>3 std from mean)
        outlier_mask = np.abs(residuals - mean_resid) > 3 * std_resid
        n_outliers = np.sum(outlier_mask)

        # Autocorrelation (lag-1)
        if len(residuals) > 2:
            autocorr = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
        else:
            autocorr = 0

        # Heteroscedasticity: split residuals into halves, compare variance
        mid = len(residuals) // 2
        var_first = np.var(residuals[:mid])
        var_second = np.var(residuals[mid:])
        het_ratio = var_second / var_first if var_first > 0 else 1.0

        # Durbin-Watson approximation
        diff_resid = np.diff(residuals)
        dw = (
            np.sum(diff_resid**2) / np.sum(residuals**2)
            if np.sum(residuals**2) > 0
            else 2
        )

        return {
            "mean_residual": round(mean_resid, 6),
            "std_residual": round(std_resid, 4),
            "n_outliers": int(n_outliers),
            "outlier_indices": np.where(outlier_mask)[0].tolist(),
            "autocorrelation_lag1": round(float(autocorr), 4),
            "durbin_watson": round(dw, 4),
            "heteroscedasticity_ratio": round(het_ratio, 4),
            "residuals_normal": abs(autocorr) < 0.1 and 1.5 < dw < 2.5,
        }

    def print_regression_report(self, result: RegressionResult, symbol: str = "Stock"):
        """Print a formatted regression report."""
        print(f"\n{'=' * 60}")
        print(f"  Regression Analysis: {symbol}")
        print(f"{'=' * 60}")
        print(f"  Slope:          {result.slope:.6f}")
        print(f"  Intercept:      {result.intercept:.4f}")
        print(f"  R-squared:      {result.r_squared:.4f}")
        print(f"  Adj R-squared:  {result.adj_r_squared:.4f}")
        print(f"  Std Error:      {result.std_error:.4f}")
        print(f"\n  Coefficients:")
        for name, val in result.coefficients.items():
            print(f"    {name}: {val:.6f}")


# Convenience functions
def linear_regression(df, y_col="Close"):
    """Quick linear regression on stock data."""
    return RegressionAnalyzer().linear_regression(df, y_col)


def forecast_price(df, days=30, method="linear"):
    """Quick price forecast."""
    return RegressionAnalyzer().forecast_price(df, days, method)
