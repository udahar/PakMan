#!/usr/bin/env python3
"""
Stock Analyzer - Core Analysis Engine

Analyze stock data, identify patterns, calculate metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockMetrics:
    """Calculated metrics for a stock."""

    symbol: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    avg_daily_return: float
    win_rate: float
    avg_gain: float
    avg_loss: float
    current_price: float
    price_52w_high: float
    price_52w_low: float


class StockAnalyzer:
    """
    Analyze stock data and calculate metrics.

    Features:
    - Technical indicators
    - Risk metrics
    - Pattern recognition
    - Performance analysis
    """

    def __init__(self):
        self._data: Dict[str, pd.DataFrame] = {}
        self._metrics: Dict[str, StockMetrics] = {}

    def load_data(self, data: Dict[str, pd.DataFrame]):
        """
        Load stock data for analysis.

        Args:
            data: Dictionary of symbol -> DataFrame
        """
        self._data = data

    def analyze_symbol(self, symbol: str, df: pd.DataFrame) -> StockMetrics:
        """
        Analyze a single stock symbol.

        Args:
            symbol: Stock symbol
            df: DataFrame with stock data

        Returns:
            StockMetrics object
        """
        # Calculate returns
        df = df.copy()
        df["Daily_Return"] = df["Close"].pct_change()

        # Total return
        total_return = (df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1

        # Annualized return
        years = len(df) / 252  # Trading days per year
        annualized_return = (1 + total_return) ** (1 / years) - 1

        # Volatility (annualized)
        volatility = df["Daily_Return"].std() * np.sqrt(252)

        # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Maximum drawdown
        cumulative = (1 + df["Daily_Return"]).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Average daily return
        avg_daily_return = df["Daily_Return"].mean()

        # Win rate
        positive_days = (df["Daily_Return"] > 0).sum()
        total_days = df["Daily_Return"].notna().sum()
        win_rate = positive_days / total_days if total_days > 0 else 0

        # Average gain/loss
        gains = df["Daily_Return"][df["Daily_Return"] > 0]
        losses = df["Daily_Return"][df["Daily_Return"] < 0]
        avg_gain = gains.mean() if len(gains) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0

        # Current price
        current_price = df["Close"].iloc[-1]

        # 52-week high/low
        if len(df) >= 252:
            recent_year = df["Close"].iloc[-252:]
            price_52w_high = recent_year.max()
            price_52w_low = recent_year.min()
        else:
            price_52w_high = df["Close"].max()
            price_52w_low = df["Close"].min()

        metrics = StockMetrics(
            symbol=symbol,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            avg_daily_return=avg_daily_return,
            win_rate=win_rate,
            avg_gain=avg_gain,
            avg_loss=avg_loss,
            current_price=current_price,
            price_52w_high=price_52w_high,
            price_52w_low=price_52w_low,
        )

        self._metrics[symbol] = metrics

        return metrics

    def analyze_all(self) -> Dict[str, StockMetrics]:
        """
        Analyze all loaded stocks.

        Returns:
            Dictionary of symbol -> StockMetrics
        """
        results = {}

        for symbol, df in self._data.items():
            try:
                metrics = self.analyze_symbol(symbol, df)
                results[symbol] = metrics
                print(f"[OK] Analyzed {symbol}: {metrics.sharpe_ratio:.2f} Sharpe")
            except Exception as e:
                print(f"[FAIL] Failed to analyze {symbol}: {e}")

        return results

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with indicators added
        """
        result = df.copy()

        # Moving averages
        result["SMA_20"] = result["Close"].rolling(window=20).mean()
        result["SMA_50"] = result["Close"].rolling(window=50).mean()
        result["SMA_200"] = result["Close"].rolling(window=252).mean()

        # EMA
        result["EMA_12"] = result["Close"].ewm(span=12).mean()
        result["EMA_26"] = result["Close"].ewm(span=26).mean()

        # RSI
        delta = result["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        result["MACD"] = result["EMA_12"] - result["EMA_26"]
        result["MACD_Signal"] = result["MACD"].ewm(span=9).mean()

        # Bollinger Bands
        result["BB_Middle"] = result["Close"].rolling(window=20).mean()
        result["BB_Std"] = result["Close"].rolling(window=20).std()
        result["BB_Upper"] = result["BB_Middle"] + (result["BB_Std"] * 2)
        result["BB_Lower"] = result["BB_Middle"] - (result["BB_Std"] * 2)

        # Volume MA
        result["Volume_MA"] = result["Volume"].rolling(window=20).mean()

        return result

    def get_top_performers(
        self, metric: str = "sharpe_ratio", top_n: int = 10
    ) -> List[StockMetrics]:
        """
        Get top performing stocks by metric.

        Args:
            metric: Metric to sort by
            top_n: Number of stocks to return

        Returns:
            List of StockMetrics objects
        """
        if not self._metrics:
            self.analyze_all()

        sorted_metrics = sorted(
            self._metrics.values(), key=lambda m: getattr(m, metric), reverse=True
        )

        return sorted_metrics[:top_n]

    def get_recommendations(self, top_n: int = 20) -> List[Dict]:
        """
        Generate stock recommendations.

        Combines multiple metrics for ranking:
        - Sharpe ratio (risk-adjusted return)
        - Total return
        - Win rate
        - Low volatility

        Args:
            top_n: Number of recommendations

        Returns:
            List of recommendation dictionaries
        """
        if not self._metrics:
            self.analyze_all()

        recommendations = []

        for symbol, metrics in self._metrics.items():
            # Composite score
            score = (
                metrics.sharpe_ratio * 0.4
                + metrics.total_return * 0.3
                + metrics.win_rate * 0.2
                + (1 - abs(metrics.avg_loss)) * 0.1
            )

            # Risk score (lower is better)
            risk_score = (
                metrics.volatility * 0.4
                + abs(metrics.max_drawdown) * 0.4
                + (1 - metrics.win_rate) * 0.2
            )

            recommendations.append(
                {
                    "symbol": symbol,
                    "score": score,
                    "risk_score": risk_score,
                    "metrics": metrics,
                    "recommendation": "BUY" if score > 0.5 else "HOLD",
                }
            )

        # Sort by score
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return recommendations[:top_n]

    def get_metrics(self, symbol: str) -> Optional[StockMetrics]:
        """Get metrics for a symbol."""
        return self._metrics.get(symbol)


# Example usage
def demo():
    """Demonstrate stock analysis."""
    print("=" * 60)
    print("  StockAI Analyzer - Demo")
    print("=" * 60)

    from ..data import StockDataLoader

    # Load data
    loader = StockDataLoader()

    # Try to load some stocks
    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "AMZN"]
    data = loader.load_multiple(symbols, period="5y")

    if not data:
        print("\nNo data loaded. Install yfinance: pip install yfinance")
        return

    # Analyze
    analyzer = StockAnalyzer()
    analyzer.load_data(data)

    print("\nAnalyzing stocks...")
    metrics = analyzer.analyze_all()

    # Show results
    print("\n" + "=" * 60)
    print("  Analysis Results")
    print("=" * 60)

    for symbol, m in metrics.items():
        print(f"\n{symbol}:")
        print(f"  Price: ${m.current_price:.2f}")
        print(f"  Total Return: {m.total_return:.1%}")
        print(f"  Annualized: {m.annualized_return:.1%}")
        print(f"  Sharpe Ratio: {m.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {m.max_drawdown:.1%}")
        print(f"  Win Rate: {m.win_rate:.1%}")

    # Top performers
    print("\n" + "=" * 60)
    print("  Top Performers (by Sharpe Ratio)")
    print("=" * 60)

    top = analyzer.get_top_performers("sharpe_ratio", top_n=5)
    for i, m in enumerate(top, 1):
        print(f"  {i}. {m.symbol}: {m.sharpe_ratio:.2f}")

    # Recommendations
    print("\n" + "=" * 60)
    print("  Top Recommendations")
    print("=" * 60)

    recs = analyzer.get_recommendations(top_n=10)
    for i, rec in enumerate(recs, 1):
        m = rec["metrics"]
        print(
            f"  {i}. {m.symbol}: Score={rec['score']:.2f}, Risk={rec['risk_score']:.2f} → {rec['recommendation']}"
        )


if __name__ == "__main__":
    demo()
