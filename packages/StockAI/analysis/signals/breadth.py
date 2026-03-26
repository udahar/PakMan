#!/usr/bin/env python3
"""
StockAI - Market Breadth Analysis

Fourth institutional signal: Market Breadth Divergence

Measures market health by tracking how many stocks participate in moves.
Indexes can lie - breadth tells the truth.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class BreadthData:
    """Daily breadth data."""

    date: datetime
    advancing: int
    declining: int
    unchanged: int
    new_highs: int
    new_lows: int
    adv_decline_ratio: float
    nh_nl_ratio: float


@dataclass
class MarketHealth:
    """Market health assessment."""

    date: datetime
    health_score: float  # 0-100
    breadth_trend: str  # IMPROVING, NEUTRAL, WEAKENING
    participation: str  # STRONG, MODERATE, WEAK
    divergence: Optional[str]  # BULLISH, BEARISH, NONE
    signals: List[str]


@dataclass
class SectorBreadth:
    """Sector-level breadth."""

    sector: str
    advancing: int
    declining: int
    strength: float
    percent_above_ma50: float
    percent_above_ma200: float


class MarketBreadthAnalyzer:
    """
    Analyze market breadth - the fourth institutional signal.

    Why it works:
    - Indexes can hide reality (weighted toward few giants)
    - Breadth shows true market health
    - Divergences often predict turning points

    Key metrics:
    - Advance/Decline ratio
    - New Highs/New Lows ratio
    - Percent above MA50/MA200
    - Sector participation
    """

    def __init__(self):
        self.breadth_history: List[BreadthData] = []
        self.sector_data: Dict[str, Dict[str, pd.DataFrame]] = {}

    def set_sector_mapping(self, sector_stocks: Dict[str, List[str]]):
        """
        Set sector to stocks mapping.

        Args:
            sector_stocks: Dictionary of sector -> list of stock symbols
        """
        self.sector_mapping = sector_stocks

    def calculate_daily_breadth(
        self, data: Dict[str, pd.DataFrame], date: datetime = None
    ) -> BreadthData:
        """
        Calculate daily market breadth.

        Args:
            data: Dictionary of symbol -> DataFrame
            date: Date to calculate for (default: latest)

        Returns:
            BreadthData with all metrics
        """
        advancing = 0
        declining = 0
        unchanged = 0
        new_highs = 0
        new_lows = 0

        for symbol, df in data.items():
            if len(df) < 2:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # Advance/Decline
            price_change = latest["Close"] - prev["Close"]

            if price_change > 0.01:  # Advancing
                advancing += 1
            elif price_change < -0.01:  # Declining
                declining += 1
            else:  # Unchanged
                unchanged += 1

            # New Highs/Lows (using 252 days for 52-week)
            if len(df) >= 252:
                high_52w = df["High"].rolling(252).max().iloc[-1]
                low_52w = df["Low"].rolling(252).min().iloc[-1]

                if latest["High"] >= high_52w * 0.98:  # Within 2% of 52-week high
                    new_highs += 1

                if latest["Low"] <= low_52w * 1.02:  # Within 2% of 52-week low
                    new_lows += 1

        # Calculate ratios
        adv_decline_ratio = advancing / declining if declining > 0 else advancing
        nh_nl_ratio = new_highs / new_lows if new_lows > 0 else new_highs

        return BreadthData(
            date=date or datetime.now(),
            advancing=advancing,
            declining=declining,
            unchanged=unchanged,
            new_highs=new_highs,
            new_lows=new_lows,
            adv_decline_ratio=adv_decline_ratio,
            nh_nl_ratio=nh_nl_ratio,
        )

    def calculate_breadth_history(
        self, data: Dict[str, pd.DataFrame], days: int = 30
    ) -> List[BreadthData]:
        """
        Calculate breadth history for multiple days.

        Args:
            data: Dictionary of symbol -> DataFrame
            days: Number of days to calculate

        Returns:
            List of BreadthData
        """
        history = []

        # Get date range from first stock
        if not data:
            return history

        first_df = list(data.values())[0]
        if len(first_df) < days:
            days = len(first_df)

        for i in range(-days, 0):
            # Extract data for this day
            daily_data = {}

            for symbol, df in data.items():
                if len(df) >= abs(i):
                    daily_data[symbol] = df.iloc[i : i + 1]

            if daily_data:
                # Get date from first available stock
                first_key = list(daily_data.keys())[0]
                date = daily_data[first_key].index[0]
                breadth = self.calculate_daily_breadth(daily_data, date)
                history.append(breadth)

        self.breadth_history = history
        return history

    def detect_divergence(
        self, index_data: pd.DataFrame, breadth_history: List[BreadthData] = None
    ) -> Optional[str]:
        """
        Detect market breadth divergence.

        Bearish Divergence:
        - Index rising
        - BUT advancing stocks decreasing

        Bullish Divergence:
        - Index falling
        - BUT advancing stocks increasing

        Args:
            index_data: Index DataFrame (e.g., SPY)
            breadth_history: List of BreadthData

        Returns:
            'BULLISH', 'BEARISH', or None
        """
        if breadth_history is None:
            breadth_history = self.breadth_history

        if len(breadth_history) < 10 or len(index_data) < 10:
            return None

        # Calculate index trend (5-day return)
        index_return = (
            index_data["Close"].iloc[-1] - index_data["Close"].iloc[-5]
        ) / index_data["Close"].iloc[-5]

        # Calculate breadth trend (advancing stocks)
        recent_adv = np.mean([b.advancing for b in breadth_history[-5:]])
        old_adv = np.mean([b.advancing for b in breadth_history[-10:-5]])

        breadth_trend = (recent_adv - old_adv) / old_adv if old_adv > 0 else 0

        # Detect divergence
        if index_return > 0.02 and breadth_trend < -0.10:
            # Index up but breadth weakening
            return "BEARISH"

        elif index_return < -0.02 and breadth_trend > 0.10:
            # Index down but breadth improving
            return "BULLISH"

        return None

    def calculate_percent_above_ma(
        self, data: Dict[str, pd.DataFrame], period: int = 50
    ) -> float:
        """
        Calculate percent of stocks above moving average.

        Args:
            data: Dictionary of symbol -> DataFrame
            period: MA period (50 or 200)

        Returns:
            Percentage of stocks above MA
        """
        above_count = 0
        total = 0

        for symbol, df in data.items():
            if len(df) < period + 5:
                continue

            latest_close = df["Close"].iloc[-1]
            ma = df["Close"].rolling(period).mean().iloc[-1]

            if latest_close > ma:
                above_count += 1

            total += 1

        return (above_count / total * 100) if total > 0 else 0

    def calculate_sector_breadth(
        self, sector_data: Dict[str, Dict[str, pd.DataFrame]]
    ) -> List[SectorBreadth]:
        """
        Calculate breadth by sector.

        Args:
            sector_data: Dictionary of sector -> {symbol -> DataFrame}

        Returns:
            List of SectorBreadth
        """
        sector_breadth = []

        for sector, stocks in sector_data.items():
            advancing = 0
            declining = 0
            above_ma50 = 0
            above_ma200 = 0
            total = 0

            for symbol, df in stocks.items():
                if len(df) < 2:
                    continue

                latest = df.iloc[-1]
                prev = df.iloc[-2]

                # Advance/Decline
                if latest["Close"] > prev["Close"]:
                    advancing += 1
                elif latest["Close"] < prev["Close"]:
                    declining += 1

                # Above MA
                if len(df) >= 55:
                    ma50 = df["Close"].rolling(50).mean().iloc[-1]
                    if latest["Close"] > ma50:
                        above_ma50 += 1

                if len(df) >= 257:
                    ma200 = df["Close"].rolling(200).mean().iloc[-1]
                    if latest["Close"] > ma200:
                        above_ma200 += 1

                total += 1

            strength = (advancing - declining) / total if total > 0 else 0

            sector_breadth.append(
                SectorBreadth(
                    sector=sector,
                    advancing=advancing,
                    declining=declining,
                    strength=strength,
                    percent_above_ma50=(above_ma50 / total * 100) if total > 0 else 0,
                    percent_above_ma200=(above_ma200 / total * 100) if total > 0 else 0,
                )
            )

        # Sort by strength
        sector_breadth.sort(key=lambda s: s.strength, reverse=True)

        return sector_breadth

    def calculate_market_health(
        self, data: Dict[str, pd.DataFrame], index_data: pd.DataFrame = None
    ) -> MarketHealth:
        """
        Calculate overall market health score.

        Args:
            data: Dictionary of symbol -> DataFrame
            index_data: Optional index DataFrame for divergence

        Returns:
            MarketHealth assessment
        """
        # Calculate current breadth
        breadth = self.calculate_daily_breadth(data)

        # Calculate health score components
        score = 50  # Base score

        # Advance/Decline ratio (max +20)
        if breadth.adv_decline_ratio > 2.0:
            score += 20
        elif breadth.adv_decline_ratio > 1.5:
            score += 15
        elif breadth.adv_decline_ratio > 1.0:
            score += 10
        elif breadth.adv_decline_ratio < 0.5:
            score -= 20
        elif breadth.adv_decline_ratio < 0.75:
            score -= 15

        # NH/NL ratio (max +20)
        if breadth.nh_nl_ratio > 3.0:
            score += 20
        elif breadth.nh_nl_ratio > 2.0:
            score += 15
        elif breadth.nh_nl_ratio > 1.0:
            score += 10
        elif breadth.nh_nl_ratio < 0.5:
            score -= 20
        elif breadth.nh_nl_ratio < 0.75:
            score -= 15

        # Percent above MA50 (max +20)
        pct_above_ma50 = self.calculate_percent_above_ma(data, 50)
        if pct_above_ma50 > 70:
            score += 20
        elif pct_above_ma50 > 50:
            score += 10
        elif pct_above_ma50 < 30:
            score -= 20
        elif pct_above_ma50 < 50:
            score -= 10

        # Percent above MA200 (max +20)
        pct_above_ma200 = self.calculate_percent_above_ma(data, 200)
        if pct_above_ma200 > 70:
            score += 20
        elif pct_above_ma200 > 50:
            score += 10
        elif pct_above_ma200 < 30:
            score -= 20
        elif pct_above_ma200 < 50:
            score -= 10

        # Clamp score
        score = min(100, max(0, score))

        # Determine breadth trend
        if len(self.breadth_history) >= 5:
            recent_adv = np.mean([b.advancing for b in self.breadth_history[-5:]])
            old_adv = (
                np.mean([b.advancing for b in self.breadth_history[-10:-5]])
                if len(self.breadth_history) >= 10
                else recent_adv
            )

            if recent_adv > old_adv * 1.1:
                breadth_trend = "IMPROVING"
            elif recent_adv < old_adv * 0.9:
                breadth_trend = "WEAKENING"
            else:
                breadth_trend = "NEUTRAL"
        else:
            breadth_trend = "NEUTRAL"

        # Determine participation
        if breadth.adv_decline_ratio > 2.0:
            participation = "STRONG"
        elif breadth.adv_decline_ratio > 1.0:
            participation = "MODERATE"
        else:
            participation = "WEAK"

        # Detect divergence
        divergence = (
            self.detect_divergence(index_data) if index_data is not None else None
        )

        # Build signals list
        signals = []

        if breadth.adv_decline_ratio > 2.0:
            signals.append(f"Strong A/D ratio: {breadth.adv_decline_ratio:.1f}")

        if breadth.nh_nl_ratio > 3.0:
            signals.append(f"Strong NH/NL: {breadth.nh_nl_ratio:.1f}")

        if pct_above_ma50 < 30:
            signals.append(f"Oversold: Only {pct_above_ma50:.0f}% above MA50")

        if pct_above_ma50 > 70:
            signals.append(f"Overbought: {pct_above_ma50:.0f}% above MA50")

        if divergence:
            signals.append(f"{divergence} divergence detected")

        return MarketHealth(
            date=datetime.now(),
            health_score=score,
            breadth_trend=breadth_trend,
            participation=participation,
            divergence=divergence,
            signals=signals,
        )

    def print_breadth_report(
        self,
        breadth: BreadthData,
        health: MarketHealth,
        sector_breadth: List[SectorBreadth] = None,
    ):
        """Print comprehensive breadth report."""
        print("\n" + "=" * 90)
        print("  MARKET BREADTH ANALYSIS")
        print("=" * 90)

        # Daily breadth
        print(f"\n📊 Daily Breadth ({breadth.date.strftime('%Y-%m-%d')}):")
        print(f"  Advancing:  {breadth.advancing:,}")
        print(f"  Declining:  {breadth.declining:,}")
        print(f"  Unchanged:  {breadth.unchanged:,}")
        print(f"  New Highs:  {breadth.new_highs:,}")
        print(f"  New Lows:   {breadth.new_lows:,}")
        print(f"\n  A/D Ratio:  {breadth.adv_decline_ratio:.2f}")
        print(f"  NH/NL Ratio: {breadth.nh_nl_ratio:.2f}")

        # Market health
        print(f"\n💚 Market Health Score: {health.health_score:.0f}/100")
        print(f"  Breadth Trend:   {health.breadth_trend}")
        print(f"  Participation:   {health.participation}")

        if health.divergence:
            emoji = "🟢" if health.divergence == "BULLISH" else "🔴"
            print(f"  {emoji} {health.divergence} DIVERGENCE DETECTED")

        if health.signals:
            print(f"\n  Signals:")
            for signal in health.signals:
                print(f"    • {signal}")

        # Sector breadth
        if sector_breadth:
            print(f"\n🏢 Sector Breadth:")
            for sector in sector_breadth[:5]:
                emoji = (
                    "🟢"
                    if sector.strength > 0
                    else "🔴"
                    if sector.strength < 0
                    else "🟡"
                )
                print(
                    f"  {emoji} {sector.sector:15} +{sector.advancing:3} / -{sector.declining:3} | "
                    f"{sector.percent_above_ma50:.0f}% > MA50 | {sector.percent_above_ma200:.0f}% > MA200"
                )

        # Interpretation
        print(f"\n📈 Interpretation:")

        if health.health_score > 70:
            print("  Market is HEALTHY - Broad participation, strong breadth")
        elif health.health_score > 50:
            print("  Market is MODERATE - Mixed signals")
        else:
            print("  Market is WEAK - Poor participation, weak breadth")

        if health.divergence == "BEARISH":
            print("\n  ⚠️  WARNING: Bearish divergence - Index may be misleading")
            print("      Only large caps holding index up while breadth weakens")
        elif health.divergence == "BULLISH":
            print("\n  ✅ OPPORTUNITY: Bullish divergence - Bottom may be forming")
            print("      Internal strength improving despite index decline")


# Example usage
def demo():
    """Demonstrate market breadth analysis."""
    from ...data import StockDataLoader

    print("=" * 90)
    print("  StockAI - Market Breadth Analysis")
    print("=" * 90)

    # Load data
    loader = StockDataLoader()

    # Define sectors
    sectors = {
        "Technology": [
            "AAPL",
            "GOOGL",
            "MSFT",
            "NVDA",
            "META",
            "NFLX",
            "AMD",
            "INTC",
            "CRM",
            "ORCL",
        ],
        "Consumer": ["AMZN", "TSLA", "WMT", "HD", "MCD", "NKE", "SBUX", "DIS"],
        "Financial": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW"],
        "Healthcare": ["JNJ", "PFE", "UNH", "MRK", "ABBV", "TMO", "ABT", "DHR"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "OXY", "EOG", "MPC"],
    }

    # Load all stocks
    all_symbols = []
    for stocks in sectors.values():
        all_symbols.extend(stocks)

    try:
        data = loader.load_multiple(all_symbols, period="1y")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Load index (SPY)
    try:
        index_data = loader.load_yahoo("SPY", period="1y")
    except:
        index_data = None

    # Create analyzer
    analyzer = MarketBreadthAnalyzer()
    analyzer.set_sector_mapping(sectors)

    # Calculate breadth history (simplified - just last 10 days)
    print("\n📊 Calculating breadth history...")
    try:
        analyzer.calculate_breadth_history(data, days=10)
    except Exception as e:
        print(f"Note: Breadth history calculation skipped ({e})")

    # Calculate current breadth
    breadth = analyzer.calculate_daily_breadth(data)

    # Calculate market health
    health = analyzer.calculate_market_health(data, index_data)

    # Calculate sector breadth
    sector_data = {
        sector: {sym: data[sym] for sym in stocks if sym in data}
        for sector, stocks in sectors.items()
    }
    sector_breadth = analyzer.calculate_sector_breadth(sector_data)

    # Print report
    analyzer.print_breadth_report(breadth, health, sector_breadth)

    print("\n" + "=" * 90)
    print("  ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    demo()
