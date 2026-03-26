#!/usr/bin/env python3
"""
StockAI - Day Trading & Swing Trading Analysis

Mean reversion, momentum, and gap reversal strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TradingSignal:
    """A trading signal with details."""

    symbol: str
    strategy: str  # mean_reversion, momentum, gap_reversal
    action: str  # BUY, SELL, SHORT
    strength: float  # 0-1 signal strength
    entry_price: float
    target_price: float
    stop_loss: float
    timeframe: str  # intraday, swing_3d, swing_5d
    reasoning: List[str]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DayTradingAnalyzer:
    """
    Analyze stocks for day trading and swing trading opportunities.

    Strategies:
    - Mean Reversion (oversold bounce)
    - Momentum Trading (breakout continuation)
    - Gap Reversal (gap fill plays)
    """

    def __init__(self):
        self.signals: List[TradingSignal] = []

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(
        self, prices: pd.Series
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower

    def detect_volume_spike(
        self, df: pd.DataFrame, threshold: float = 1.5
    ) -> pd.Series:
        """Detect volume spikes (> threshold × average)."""
        avg_volume = df["Volume"].rolling(window=20).mean()
        volume_ratio = df["Volume"] / avg_volume
        return volume_ratio > threshold

    def mean_reversion_scan(
        self, df: pd.DataFrame, symbol: str
    ) -> Optional[TradingSignal]:
        """
        Scan for mean reversion opportunities.

        Buy when:
        - Stock down >5-10% in one day
        - RSI < 30 (oversold)
        - Volume spike > 1.5× average
        - Price far below 20-day MA
        """
        if len(df) < 30:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Calculate indicators
        rsi = self.calculate_rsi(df["Close"]).iloc[-1]
        ma_20 = df["Close"].rolling(20).mean().iloc[-1]
        volume_spike = self.detect_volume_spike(df).iloc[-1]

        # Daily change
        daily_change = (latest["Close"] - prev["Close"]) / prev["Close"]

        # 5-day change
        if len(df) >= 5:
            change_5d = (latest["Close"] - df.iloc[-5]["Close"]) / df.iloc[-5]["Close"]
        else:
            change_5d = 0

        # Distance from MA20
        distance_from_ma = (latest["Close"] - ma_20) / ma_20

        # Check buy signals
        buy_signals = []

        if daily_change < -0.05:  # Down >5%
            buy_signals.append(f"Daily drop: {daily_change:.1%}")

        if rsi < 30:
            buy_signals.append(f"RSI oversold: {rsi:.1f}")

        if volume_spike:
            volume_ratio = latest["Volume"] / df["Volume"].rolling(20).mean().iloc[-1]
            buy_signals.append(f"Volume spike: {volume_ratio:.1f}x")

        if distance_from_ma < -0.05:  # 5% below MA20
            buy_signals.append(f"Below MA20: {distance_from_ma:.1%}")

        if len(buy_signals) >= 2:
            # Calculate target and stop
            target_price = latest["Close"] * 1.05  # 5% rebound
            stop_loss = latest["Close"] * 0.95  # 5% stop

            strength = min(1.0, len(buy_signals) / 4.0)

            return TradingSignal(
                symbol=symbol,
                strategy="mean_reversion",
                action="BUY",
                strength=strength,
                entry_price=latest["Close"],
                target_price=target_price,
                stop_loss=stop_loss,
                timeframe="swing_3d",
                reasoning=buy_signals,
            )

        return None

    def momentum_scan(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        Scan for momentum trading opportunities.

        Buy when:
        - Price breaks 20-day high
        - Volume > 2× average
        - Trend slope positive
        """
        if len(df) < 30:
            return None

        latest = df.iloc[-1]

        # Calculate indicators
        high_20 = df["High"].rolling(20).max().iloc[-1]
        ma_20 = df["Close"].rolling(20).mean().iloc[-1]
        ma_50 = df["Close"].rolling(50).mean().iloc[-1]
        volume_ratio = latest["Volume"] / df["Volume"].rolling(20).mean().iloc[-1]

        # Trend slope (5-day)
        if len(df) >= 5:
            trend_slope = (latest["Close"] - df.iloc[-5]["Close"]) / df.iloc[-5][
                "Close"
            ]
        else:
            trend_slope = 0

        # Check breakout signals
        buy_signals = []

        if latest["Close"] > high_20:
            buy_signals.append(f"Broke 20-day high: ${high_20:.2f}")

        if volume_ratio > 2.0:
            buy_signals.append(f"Volume surge: {volume_ratio:.1f}x")

        if trend_slope > 0.05:  # 5% uptrend
            buy_signals.append(f"Positive trend: {trend_slope:.1%}")

        if ma_20 > ma_50:
            buy_signals.append("MA20 > MA50 (bullish)")

        if len(buy_signals) >= 2:
            target_price = latest["Close"] * 1.08  # 8% continuation
            stop_loss = latest["Close"] * 0.94  # 6% stop

            strength = min(1.0, len(buy_signals) / 4.0)

            return TradingSignal(
                symbol=symbol,
                strategy="momentum",
                action="BUY",
                strength=strength,
                entry_price=latest["Close"],
                target_price=target_price,
                stop_loss=stop_loss,
                timeframe="swing_5d",
                reasoning=buy_signals,
            )

        return None

    def gap_reversal_scan(
        self, df: pd.DataFrame, symbol: str
    ) -> Optional[TradingSignal]:
        """
        Scan for gap reversal opportunities.

        Gap up > 4% → Short when momentum stalls
        Gap down > 4% → Buy if reversal starts
        """
        if len(df) < 3:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Opening gap (using previous close vs current open)
        gap_percent = (latest["Open"] - prev["Close"]) / prev["Close"]

        # Current day direction
        day_change = (latest["Close"] - latest["Open"]) / latest["Open"]

        signals = []

        if gap_percent > 0.04:  # Gap up >4%
            if day_change < -0.02:  # Reversing down
                signals.append(f"Gap up {gap_percent:.1%}, reversing {day_change:.1%}")

                return TradingSignal(
                    symbol=symbol,
                    strategy="gap_reversal",
                    action="SHORT",
                    strength=0.7,
                    entry_price=latest["Close"],
                    target_price=latest["Close"] * 0.95,
                    stop_loss=latest["Close"] * 1.03,
                    timeframe="intraday",
                    reasoning=signals,
                )

        elif gap_percent < -0.04:  # Gap down >4%
            if day_change > 0.02:  # Reversing up
                signals.append(
                    f"Gap down {gap_percent:.1%}, reversing {day_change:.1%}"
                )

                return TradingSignal(
                    symbol=symbol,
                    strategy="gap_reversal",
                    action="BUY",
                    strength=0.7,
                    entry_price=latest["Close"],
                    target_price=latest["Close"] * 1.05,
                    stop_loss=latest["Close"] * 0.97,
                    timeframe="intraday",
                    reasoning=signals,
                )

        return None

    def scan_all_strategies(self, df: pd.DataFrame, symbol: str) -> List[TradingSignal]:
        """Run all trading strategies on a stock."""
        signals = []

        # Mean reversion
        mr_signal = self.mean_reversion_scan(df, symbol)
        if mr_signal:
            signals.append(mr_signal)

        # Momentum
        mom_signal = self.momentum_scan(df, symbol)
        if mom_signal:
            signals.append(mom_signal)

        # Gap reversal
        gap_signal = self.gap_reversal_scan(df, symbol)
        if gap_signal:
            signals.append(gap_signal)

        return signals

    def scan_multiple_stocks(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[TradingSignal]]:
        """Scan multiple stocks for trading opportunities."""
        all_signals = {}

        for symbol, df in data.items():
            signals = self.scan_all_strategies(df, symbol)
            if signals:
                all_signals[symbol] = signals

        return all_signals

    def get_top_signals(
        self, data: Dict[str, pd.DataFrame], top_n: int = 10
    ) -> List[TradingSignal]:
        """Get top N trading signals across all stocks."""
        all_signals = []

        for symbol, df in data.items():
            signals = self.scan_all_strategies(df, symbol)
            all_signals.extend(signals)

        # Sort by strength
        all_signals.sort(key=lambda s: s.strength, reverse=True)

        return all_signals[:top_n]

    def print_signals(self, signals: List[TradingSignal]):
        """Print trading signals in readable format."""
        if not signals:
            print("No trading signals found")
            return

        print("\n" + "=" * 80)
        print("  TRADING SIGNALS")
        print("=" * 80)

        for signal in signals:
            action_emoji = (
                "🟢"
                if signal.action == "BUY"
                else "🔴"
                if signal.action == "SELL"
                else "🟡"
            )

            print(f"\n{action_emoji} {signal.symbol} - {signal.strategy.upper()}")
            print(f"   Action: {signal.action}")
            print(f"   Strength: {signal.strength:.0%}")
            print(f"   Entry: ${signal.entry_price:.2f}")
            print(
                f"   Target: ${signal.target_price:.2f} ({(signal.target_price / signal.entry_price - 1):+.1%})"
            )
            print(
                f"   Stop: ${signal.stop_loss:.2f} ({(signal.stop_loss / signal.entry_price - 1):+.1%})"
            )
            print(f"   Timeframe: {signal.timeframe}")
            print(f"   Reasoning:")
            for reason in signal.reasoning:
                print(f"     • {reason}")


# Example usage
def demo():
    """Demonstrate day trading analysis."""
    from ...data import StockDataLoader

    print("=" * 80)
    print("  StockAI - Day Trading Analysis")
    print("=" * 80)

    # Load data
    loader = StockDataLoader()

    try:
        # Load recent daily data
        data = loader.load_multiple(["AAPL", "GOOGL", "NVDA", "TSLA"], period="3mo")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Analyze
    analyzer = DayTradingAnalyzer()

    # Get top signals
    top_signals = analyzer.get_top_signals(data, top_n=10)

    # Print
    analyzer.print_signals(top_signals)

    print("\n" + "=" * 80)
    print("  ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    demo()
