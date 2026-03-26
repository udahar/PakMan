#!/usr/bin/env python3
"""
StockAI - Institutional Signals

Hedge fund signals that measure behavior, not just price.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class InstitutionalSignal:
    """An institutional-grade trading signal."""

    signal_type: str
    symbol: str
    strength: float  # 0-100
    score: float
    interpretation: str
    action: str  # BUY, SELL, WATCH
    details: Dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class InstitutionalSignals:
    """
    Calculate institutional-grade signals.

    Three powerful signals:
    1. Volume Shock (Institutional Footprints)
    2. Relative Strength vs Market
    3. Volatility Contraction (Energy Build-Up)
    """

    def __init__(self):
        self.signals: List[InstitutionalSignal] = []

    def calculate_volume_shock(
        self, df: pd.DataFrame, symbol: str, threshold: float = 3.0
    ) -> Optional[InstitutionalSignal]:
        """
        Detect volume shock - institutional footprints.

        Big funds cannot hide volume. When they enter/exit,
        the tape shows it.

        Signal:
        - volume_ratio > 3 (today vs 30-day avg)
        - AND price change < 2%

        Interpretation:
        Huge buying/selling but price barely moves.
        Someone big is quietly accumulating shares.
        Often precedes multi-week runs.

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            threshold: Volume ratio threshold

        Returns:
            InstitutionalSignal if detected, None otherwise
        """
        if len(df) < 35:  # Need 30 days + buffer
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Calculate volume ratio
        volume_30d_avg = df["Volume"].rolling(30).mean().iloc[-2]  # Yesterday's avg
        volume_today = latest["Volume"]
        volume_ratio = volume_today / volume_30d_avg if volume_30d_avg > 0 else 0

        # Calculate price change
        price_change = (latest["Close"] - prev["Close"]) / prev["Close"]

        # Check for volume shock
        if volume_ratio > threshold and abs(price_change) < 0.02:
            # Determine if accumulation or distribution
            if latest["Close"] > prev["Close"]:
                action = "BUY"
                interpretation = f"Huge volume ({volume_ratio:.1f}x) with price up {price_change:.1%} - Institutional accumulation"
            else:
                action = "SELL"
                interpretation = f"Huge volume ({volume_ratio:.1f}x) with price down {price_change:.1%} - Institutional distribution"

            # Calculate strength
            strength = min(100, (volume_ratio / threshold) * 50)

            return InstitutionalSignal(
                signal_type="volume_shock",
                symbol=symbol,
                strength=strength,
                score=volume_ratio,
                interpretation=interpretation,
                action=action,
                details={
                    "volume_ratio": volume_ratio,
                    "volume_today": volume_today,
                    "volume_30d_avg": volume_30d_avg,
                    "price_change": price_change,
                    "threshold": threshold,
                },
            )

        return None

    def calculate_relative_strength(
        self,
        df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        symbol: str,
        period: int = 30,
    ) -> Optional[InstitutionalSignal]:
        """
        Calculate relative strength vs market.

        Not just "is stock going up" but "is it outperforming the market?"

        Signal:
        - stock_return_30d - SP500_return_30d

        Example:
        - Stock +5%, S&P500 -3% → Relative Strength = +8%

        Stocks that consistently outperform tend to keep outperforming
        because institutions rotate capital into strength.

        Args:
            df: Stock DataFrame
            benchmark_df: Benchmark DataFrame (e.g., SPY)
            symbol: Stock symbol
            period: Lookback period (days)

        Returns:
            InstitutionalSignal with relative strength
        """
        if len(df) < period + 5 or len(benchmark_df) < period + 5:
            return None

        # Calculate stock return
        stock_return = (df["Close"].iloc[-1] - df["Close"].iloc[-period]) / df[
            "Close"
        ].iloc[-period]

        # Calculate benchmark return
        benchmark_return = (
            benchmark_df["Close"].iloc[-1] - benchmark_df["Close"].iloc[-period]
        ) / benchmark_df["Close"].iloc[-period]

        # Calculate relative strength
        relative_strength = stock_return - benchmark_return

        # Determine action
        if relative_strength > 0.10:  # Outperforming by >10%
            action = "BUY"
            interpretation = f"Strong relative strength: +{relative_strength:.1%} vs market over {period} days"
            strength = min(100, relative_strength * 500)
        elif relative_strength > 0.05:  # Outperforming by >5%
            action = "WATCH"
            interpretation = (
                f"Moderate relative strength: +{relative_strength:.1%} vs market"
            )
            strength = min(100, relative_strength * 400)
        elif relative_strength < -0.10:  # Underperforming by >10%
            action = "SELL"
            interpretation = (
                f"Weak relative strength: {relative_strength:.1%} vs market"
            )
            strength = min(100, abs(relative_strength) * 500)
        else:
            action = "WATCH"
            interpretation = (
                f"Neutral relative strength: {relative_strength:.1%} vs market"
            )
            strength = 50

        return InstitutionalSignal(
            signal_type="relative_strength",
            symbol=symbol,
            strength=strength,
            score=relative_strength,
            interpretation=interpretation,
            action=action,
            details={
                "stock_return": stock_return,
                "benchmark_return": benchmark_return,
                "relative_strength": relative_strength,
                "period": period,
            },
        )

    def calculate_volatility_contraction(
        self, df: pd.DataFrame, symbol: str, lookback: int = 10
    ) -> Optional[InstitutionalSignal]:
        """
        Detect volatility contraction - energy build-up.

        Subtle but deadly accurate signal.

        Signal:
        - Daily range shrinking for 10-15 days
        - AND volume slowly rising

        Calculation:
        - range = high - low
        - range_trend = slope of range over last 10 days

        Look for:
        - range_trend < 0 (contracting)
        - volume_trend > 0 (accumulating)

        Interpretation:
        Stock is quieting down while buyers accumulate.
        When breakout comes, it can be explosive.

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            lookback: Lookback period for trend

        Returns:
            InstitutionalSignal if detected, None otherwise
        """
        if len(df) < lookback + 5:
            return None

        # Calculate daily range
        df_copy = df.copy()
        df_copy["range"] = df_copy["High"] - df_copy["Low"]
        df_copy["range_pct"] = df_copy["range"] / df_copy["Close"]

        # Calculate range trend (slope over last N days)
        recent_ranges = df_copy["range_pct"].iloc[-lookback:].values
        if len(recent_ranges) >= lookback:
            # Simple linear regression slope
            x = np.arange(len(recent_ranges))
            y = recent_ranges

            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            range_trend = slope
        else:
            return None

        # Calculate volume trend
        recent_volumes = df["Volume"].iloc[-lookback:].values
        x = np.arange(len(recent_volumes))
        y = np.log(recent_volumes)  # Log scale for volume

        volume_slope = np.polyfit(x, y, 1)[0]
        volume_trend = volume_slope

        # Check for volatility contraction pattern
        if range_trend < 0 and volume_trend > 0:
            # Calculate contraction ratio
            avg_range_recent = np.mean(recent_ranges)
            avg_range_old = np.mean(
                df_copy["range_pct"].iloc[-lookback * 2 : -lookback].values
            )

            contraction_ratio = (
                avg_range_recent / avg_range_old if avg_range_old > 0 else 1
            )

            # Calculate strength
            strength = min(100, (1 - contraction_ratio) * 200 + volume_trend * 100)

            return InstitutionalSignal(
                signal_type="volatility_contraction",
                symbol=symbol,
                strength=strength,
                score=(1 - contraction_ratio) * 100,
                interpretation=f"Volatility contracting ({contraction_ratio:.1f}x) while volume rises - Energy building for breakout",
                action="BUY",
                details={
                    "range_trend": range_trend,
                    "volume_trend": volume_trend,
                    "contraction_ratio": contraction_ratio,
                    "avg_range_recent": avg_range_recent,
                    "avg_range_old": avg_range_old,
                    "lookback": lookback,
                },
            )

        return None

    def calculate_all_signals(
        self, df: pd.DataFrame, symbol: str, benchmark_df: pd.DataFrame = None
    ) -> List[InstitutionalSignal]:
        """
        Calculate all institutional signals for a stock.

        Args:
            df: Stock DataFrame
            symbol: Stock symbol
            benchmark_df: Optional benchmark DataFrame

        Returns:
            List of detected signals
        """
        signals = []

        # 1. Volume Shock
        volume_signal = self.calculate_volume_shock(df, symbol)
        if volume_signal:
            signals.append(volume_signal)

        # 2. Relative Strength
        if benchmark_df is not None:
            rs_signal = self.calculate_relative_strength(df, benchmark_df, symbol)
            if rs_signal:
                signals.append(rs_signal)

        # 3. Volatility Contraction
        vc_signal = self.calculate_volatility_contraction(df, symbol)
        if vc_signal:
            signals.append(vc_signal)

        return signals

    def calculate_combined_score(self, signals: List[InstitutionalSignal]) -> float:
        """
        Calculate combined score from multiple signals.

        Score = relative_strength + volume_shock + volatility_contraction

        Args:
            signals: List of signals

        Returns:
            Combined score (0-100)
        """
        if not signals:
            return 0

        # Weight by signal type
        weights = {
            "volume_shock": 0.35,
            "relative_strength": 0.35,
            "volatility_contraction": 0.30,
        }

        score = 0
        total_weight = 0

        for signal in signals:
            weight = weights.get(signal.signal_type, 0.2)
            score += signal.strength * weight
            total_weight += weight

        return score / total_weight if total_weight > 0 else 0

    def scan_multiple_stocks(
        self, data: Dict[str, pd.DataFrame], benchmark_df: pd.DataFrame = None
    ) -> Dict[str, List[InstitutionalSignal]]:
        """
        Scan multiple stocks for institutional signals.

        Args:
            data: Dictionary of symbol -> DataFrame
            benchmark_df: Optional benchmark DataFrame

        Returns:
            Dictionary of symbol -> signals
        """
        all_signals = {}

        for symbol, df in data.items():
            signals = self.calculate_all_signals(df, symbol, benchmark_df)
            if signals:
                all_signals[symbol] = signals

        return all_signals

    def rank_stocks_by_score(
        self, all_signals: Dict[str, List[InstitutionalSignal]]
    ) -> List[Tuple[str, float, List[InstitutionalSignal]]]:
        """
        Rank stocks by combined score.

        Args:
            all_signals: Dictionary of symbol -> signals

        Returns:
            List of (symbol, score, signals) tuples, sorted by score
        """
        ranked = []

        for symbol, signals in all_signals.items():
            score = self.calculate_combined_score(signals)
            ranked.append((symbol, score, signals))

        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def print_signals(self, all_signals: Dict[str, List[InstitutionalSignal]]):
        """Print signals in readable format."""
        if not all_signals:
            print("No institutional signals detected")
            return

        print("\n" + "=" * 90)
        print("  INSTITUTIONAL SIGNALS")
        print("=" * 90)

        for symbol, signals in all_signals.items():
            print(f"\n{symbol}:")

            for signal in signals:
                emoji = (
                    "🟢"
                    if signal.action == "BUY"
                    else "🔴"
                    if signal.action == "SELL"
                    else "🟡"
                )

                print(f"  {emoji} {signal.signal_type.upper()}")
                print(f"     Strength: {signal.strength:.0f}/100")
                print(f"     Action: {signal.action}")
                print(f"     {signal.interpretation}")

                if signal.signal_type == "volume_shock":
                    print(f"     Volume: {signal.details['volume_ratio']:.1f}x average")
                elif signal.signal_type == "relative_strength":
                    print(f"     vs Market: {signal.details['relative_strength']:+.1%}")
                elif signal.signal_type == "volatility_contraction":
                    print(
                        f"     Contraction: {signal.details['contraction_ratio']:.1f}x"
                    )

    def print_ranked_stocks(
        self,
        ranked: List[Tuple[str, float, List[InstitutionalSignal]]],
        top_n: int = 10,
    ):
        """Print top ranked stocks."""
        print("\n" + "=" * 90)
        print(f"  TOP {top_n} RANKED STOCKS")
        print("=" * 90)
        print("\nRank  Symbol  Score  Signals")
        print("-" * 90)

        for i, (symbol, score, signals) in enumerate(ranked[:top_n], 1):
            signal_types = ", ".join([s.signal_type[:15] for s in signals])
            print(f"{i:4}  {symbol:6}  {score:5.0f}  {signal_types}")


# Example usage
def demo():
    """Demonstrate institutional signals."""
    from ...data import StockDataLoader

    print("=" * 90)
    print("  StockAI - Institutional Signals")
    print("=" * 90)

    # Load data
    loader = StockDataLoader()

    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "META", "NFLX", "AMD"]

    try:
        data = loader.load_multiple(symbols, period="3mo")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Load benchmark (SPY)
    try:
        benchmark = loader.load_yahoo("SPY", period="3mo")
    except:
        benchmark = None

    # Calculate signals
    analyzer = InstitutionalSignals()
    all_signals = analyzer.scan_multiple_stocks(data, benchmark)

    # Print signals
    analyzer.print_signals(all_signals)

    # Rank stocks
    ranked = analyzer.rank_stocks_by_score(all_signals)
    analyzer.print_ranked_stocks(ranked)

    print("\n" + "=" * 90)
    print("  ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    demo()
