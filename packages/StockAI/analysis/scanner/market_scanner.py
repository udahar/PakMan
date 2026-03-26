#!/usr/bin/env python3
"""
StockAI - Market Scanner & Anomaly Detector

Scan the market for opportunities, detect anomalies, and find relative strength.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketAnomaly:
    """A detected market anomaly."""

    anomaly_type: str
    symbol: str
    sector: str
    severity: float  # 0-1
    description: str
    signal: str  # BUY, SELL, WATCH
    details: Dict


@dataclass
class SectorRotation:
    """Sector rotation signal."""

    sector: str
    momentum: float
    relative_strength: float
    recommendation: str  # OVERWEIGHT, UNDERWEIGHT, NEUTRAL
    top_stocks: List[str]


class MarketScanner:
    """
    Scan the market for anomalies and opportunities.

    Features:
    - Biggest gainers/losers
    - Volume anomalies
    - Sector rotation
    - Relative strength detection
    - Volatility spikes
    """

    def __init__(self):
        self.anomalies: List[MarketAnomaly] = []
        self.sector_rotation: List[SectorRotation] = []

    def scan_biggest_movers(
        self, data: Dict[str, pd.DataFrame], top_n: int = 10
    ) -> Dict:
        """
        Find biggest gainers and losers.

        Args:
            data: Dictionary of symbol -> DataFrame
            top_n: Number to return

        Returns:
            Dictionary with gainers and losers
        """
        daily_changes = {}

        for symbol, df in data.items():
            if len(df) < 2:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            change = (latest["Close"] - prev["Close"]) / prev["Close"]
            daily_changes[symbol] = {
                "change": change,
                "volume": latest["Volume"],
                "price": latest["Close"],
            }

        # Sort by change
        sorted_changes = sorted(
            daily_changes.items(), key=lambda x: x[1]["change"], reverse=True
        )

        gainers = sorted_changes[:top_n]
        losers = sorted_changes[-top_n:][::-1]  # Reverse to show biggest drop first

        return {
            "gainers": [
                {
                    "symbol": symbol,
                    "change": data["change"],
                    "volume": data["volume"],
                    "price": data["price"],
                }
                for symbol, data in gainers
            ],
            "losers": [
                {
                    "symbol": symbol,
                    "change": data["change"],
                    "volume": data["volume"],
                    "price": data["price"],
                }
                for symbol, data in losers
            ],
        }

    def detect_volume_anomalies(
        self, data: Dict[str, pd.DataFrame], threshold: float = 2.0
    ) -> List[MarketAnomaly]:
        """
        Detect volume spikes (> threshold × average).

        Args:
            data: Dictionary of symbol -> DataFrame
            threshold: Volume ratio threshold

        Returns:
            List of volume anomalies
        """
        anomalies = []

        for symbol, df in data.items():
            if len(df) < 30:
                continue

            latest_volume = df["Volume"].iloc[-1]
            avg_volume = df["Volume"].rolling(20).mean().iloc[-1]

            volume_ratio = latest_volume / avg_volume

            if volume_ratio > threshold:
                # Check price direction
                price_change = (df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df[
                    "Close"
                ].iloc[-2]

                signal = (
                    "BUY"
                    if price_change > 0.02
                    else "SELL"
                    if price_change < -0.02
                    else "WATCH"
                )

                anomalies.append(
                    MarketAnomaly(
                        anomaly_type="volume_spike",
                        symbol=symbol,
                        sector="Unknown",
                        severity=min(1.0, volume_ratio / 5.0),
                        description=f"Volume spike: {volume_ratio:.1f}x average",
                        signal=signal,
                        details={
                            "volume_ratio": volume_ratio,
                            "price_change": price_change,
                            "latest_volume": latest_volume,
                            "avg_volume": avg_volume,
                        },
                    )
                )

        return anomalies

    def detect_volatility_spikes(
        self, data: Dict[str, pd.DataFrame], threshold: float = 2.0
    ) -> List[MarketAnomaly]:
        """
        Detect volatility spikes.

        Args:
            data: Dictionary of symbol -> DataFrame
            threshold: Volatility ratio threshold

        Returns:
            List of volatility anomalies
        """
        anomalies = []

        for symbol, df in data.items():
            if len(df) < 30:
                continue

            # Calculate daily volatility (high-low range)
            df_copy = df.copy()
            df_copy["daily_range"] = (df_copy["High"] - df_copy["Low"]) / df_copy[
                "Close"
            ]

            latest_vol = df_copy["daily_range"].iloc[-1]
            avg_vol = df_copy["daily_range"].rolling(20).mean().iloc[-1]

            vol_ratio = latest_vol / avg_vol

            if vol_ratio > threshold:
                anomalies.append(
                    MarketAnomaly(
                        anomaly_type="volatility_spike",
                        symbol=symbol,
                        sector="Unknown",
                        severity=min(1.0, vol_ratio / 3.0),
                        description=f"Volatility spike: {vol_ratio:.1f}x average",
                        signal="WATCH",
                        details={
                            "vol_ratio": vol_ratio,
                            "latest_range": latest_vol,
                            "avg_range": avg_vol,
                        },
                    )
                )

        return anomalies

    def detect_sector_rotation(
        self, sector_data: Dict[str, Dict[str, pd.DataFrame]]
    ) -> List[SectorRotation]:
        """
        Detect sector rotation signals.

        Args:
            sector_data: Dictionary of sector -> {symbol -> DataFrame}

        Returns:
            List of sector rotation signals
        """
        rotations = []

        sector_performance = {}

        # Calculate sector performance
        for sector, stocks in sector_data.items():
            returns = []

            for symbol, df in stocks.items():
                if len(df) < 21:  # Need ~1 month
                    continue

                # 1-month return
                return_1m = (df["Close"].iloc[-1] - df["Close"].iloc[-21]) / df[
                    "Close"
                ].iloc[-21]
                returns.append(return_1m)

            if returns:
                avg_return = np.mean(returns)
                sector_performance[sector] = avg_return

        # Calculate relative strength
        if sector_performance:
            avg_market_return = np.mean(list(sector_performance.values()))

            for sector, return_ in sector_performance.items():
                relative_strength = return_ - avg_market_return

                # Momentum (positive = strengthening)
                momentum = relative_strength

                # Recommendation
                if relative_strength > 0.05:
                    recommendation = "OVERWEIGHT"
                elif relative_strength < -0.05:
                    recommendation = "UNDERWEIGHT"
                else:
                    recommendation = "NEUTRAL"

                # Top stocks in sector
                top_stocks = []
                if sector in sector_data:
                    stock_returns = []
                    for symbol, df in sector_data[sector].items():
                        if len(df) >= 21:
                            ret = (df["Close"].iloc[-1] - df["Close"].iloc[-21]) / df[
                                "Close"
                            ].iloc[-21]
                            stock_returns.append((symbol, ret))

                    stock_returns.sort(key=lambda x: x[1], reverse=True)
                    top_stocks = [s[0] for s in stock_returns[:3]]

                rotations.append(
                    SectorRotation(
                        sector=sector,
                        momentum=momentum,
                        relative_strength=relative_strength,
                        recommendation=recommendation,
                        top_stocks=top_stocks,
                    )
                )

        # Sort by momentum
        rotations.sort(key=lambda r: r.momentum, reverse=True)

        return rotations

    def detect_relative_strength(
        self, data: Dict[str, pd.DataFrame], benchmark: pd.DataFrame = None
    ) -> List[MarketAnomaly]:
        """
        Detect stocks with relative strength vs market/sector.

        Args:
            data: Dictionary of symbol -> DataFrame
            benchmark: Benchmark DataFrame (e.g., SPY)

        Returns:
            List of relative strength anomalies
        """
        anomalies = []

        for symbol, df in data.items():
            if len(df) < 21:
                continue

            # Calculate 1-month return
            stock_return = (df["Close"].iloc[-1] - df["Close"].iloc[-21]) / df[
                "Close"
            ].iloc[-21]

            # Compare to benchmark if available
            if benchmark is not None and len(benchmark) >= 21:
                benchmark_return = (
                    benchmark["Close"].iloc[-1] - benchmark["Close"].iloc[-21]
                ) / benchmark["Close"].iloc[-21]
                relative_return = stock_return - benchmark_return
            else:
                relative_return = stock_return

            # Detect relative strength
            if relative_return > 0.10:  # Outperforming by >10%
                anomalies.append(
                    MarketAnomaly(
                        anomaly_type="relative_strength",
                        symbol=symbol,
                        sector="Unknown",
                        severity=min(1.0, relative_return / 0.20),
                        description=f"Strong relative strength: +{relative_return:.1%} vs benchmark",
                        signal="BUY",
                        details={
                            "stock_return": stock_return,
                            "benchmark_return": benchmark_return
                            if benchmark is not None
                            else None,
                            "relative_return": relative_return,
                        },
                    )
                )

            # Detect relative weakness
            elif relative_return < -0.10:  # Underperforming by >10%
                anomalies.append(
                    MarketAnomaly(
                        anomaly_type="relative_weakness",
                        symbol=symbol,
                        sector="Unknown",
                        severity=min(1.0, abs(relative_return) / 0.20),
                        description=f"Weak relative strength: {relative_return:.1%} vs benchmark",
                        signal="SELL",
                        details={
                            "stock_return": stock_return,
                            "benchmark_return": benchmark_return
                            if benchmark is not None
                            else None,
                            "relative_return": relative_return,
                        },
                    )
                )

        return anomalies

    def scan_all(
        self, data: Dict[str, pd.DataFrame], benchmark: pd.DataFrame = None
    ) -> Dict:
        """
        Run all scans.

        Args:
            data: Dictionary of symbol -> DataFrame
            benchmark: Optional benchmark DataFrame

        Returns:
            Dictionary with all scan results
        """
        results = {}

        # Biggest movers
        results["movers"] = self.scan_biggest_movers(data)

        # Volume anomalies
        results["volume_anomalies"] = self.detect_volume_anomalies(data)

        # Volatility spikes
        results["volatility_spikes"] = self.detect_volatility_spikes(data)

        # Relative strength
        results["relative_strength"] = self.detect_relative_strength(data, benchmark)

        return results

    def print_results(self, results: Dict):
        """Print scan results in readable format."""
        print("\n" + "=" * 90)
        print("  MARKET SCAN RESULTS")
        print("=" * 90)

        # Biggest movers
        print("\n📈 TOP GAINERS:")
        for gainer in results["movers"]["gainers"][:5]:
            print(
                f"  {gainer['symbol']}: {gainer['change']:+.1%} @ ${gainer['price']:.2f}"
            )

        print("\n📉 TOP LOSERS:")
        for loser in results["movers"]["losers"][:5]:
            print(
                f"  {loser['symbol']}: {loser['change']:+.1%} @ ${loser['price']:.2f}"
            )

        # Volume anomalies
        print(f"\n📊 VOLUME ANOMALIES ({len(results['volume_anomalies'])} found):")
        for anomaly in results["volume_anomalies"][:5]:
            print(f"  {anomaly.symbol}: {anomaly.description} → {anomaly.signal}")

        # Volatility spikes
        print(f"\n⚡ VOLATILITY SPIKES ({len(results['volatility_spikes'])} found):")
        for anomaly in results["volatility_spikes"][:5]:
            print(f"  {anomaly.symbol}: {anomaly.description}")

        # Relative strength
        print(f"\n💪 RELATIVE STRENGTH ({len(results['relative_strength'])} found):")
        for anomaly in results["relative_strength"][:5]:
            print(f"  {anomaly.symbol}: {anomaly.description} → {anomaly.signal}")


class AlfredMarketScanner:
    """
    Alfred's daily market scanner.

    Runs every day and outputs:
    - Top 5 rebound candidates
    - Top 5 momentum trades
    - Top undervalued long holds
    - Sector rotation alerts
    """

    def __init__(self):
        self.scanner = MarketScanner()

    def daily_scan(
        self, data: Dict[str, pd.DataFrame], benchmark: pd.DataFrame = None
    ) -> Dict:
        """
        Run daily market scan.

        Args:
            data: Dictionary of symbol -> DataFrame
            benchmark: Optional benchmark DataFrame

        Returns:
            Daily scan report
        """
        # Run all scans
        results = self.scanner.scan_all(data, benchmark)

        # Generate report
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "top_rebound_candidates": self._find_rebound_candidates(results),
            "top_momentum_trades": self._find_momentum_trades(results),
            "top_undervalued_holds": [],  # Would need fundamental data
            "sector_rotation_alerts": [],
            "market_anomalies": {
                "volume_spikes": len(results["volume_anomalies"]),
                "volatility_spikes": len(results["volatility_spikes"]),
                "relative_strength": len(results["relative_strength"]),
            },
        }

        return report

    def _find_rebound_candidates(self, results: Dict) -> List[Dict]:
        """Find mean reversion candidates (biggest losers with volume)."""
        candidates = []

        for loser in results["movers"]["losers"]:
            # Check if there's a volume anomaly
            volume_anomaly = next(
                (
                    a
                    for a in results["volume_anomalies"]
                    if a.symbol == loser["symbol"] and a.signal == "BUY"
                ),
                None,
            )

            if volume_anomaly:
                candidates.append(
                    {
                        "symbol": loser["symbol"],
                        "change": loser["change"],
                        "reason": "Heavy volume on decline (potential reversal)",
                    }
                )

        return candidates[:5]

    def _find_momentum_trades(self, results: Dict) -> List[Dict]:
        """Find momentum trades (biggest gainers with volume)."""
        candidates = []

        for gainer in results["movers"]["gainers"]:
            # Check if there's a volume anomaly
            volume_anomaly = next(
                (
                    a
                    for a in results["volume_anomalies"]
                    if a.symbol == gainer["symbol"] and gainer["change"] > 0.03
                ),
                None,
            )

            if volume_anomaly:
                candidates.append(
                    {
                        "symbol": gainer["symbol"],
                        "change": gainer["change"],
                        "reason": "Strong momentum with volume confirmation",
                    }
                )

        return candidates[:5]

    def print_daily_report(self, report: Dict):
        """Print daily scan report."""
        print("\n" + "=" * 90)
        print(f"  ALFRED DAILY MARKET SCAN - {report['date']}")
        print("=" * 90)

        print("\n🎯 TOP 5 REBOUND CANDIDATES:")
        for i, candidate in enumerate(report["top_rebound_candidates"], 1):
            print(f"  {i}. {candidate['symbol']}: {candidate['change']:+.1%}")
            print(f"     → {candidate['reason']}")

        print("\n🚀 TOP 5 MOMENTUM TRADES:")
        for i, candidate in enumerate(report["top_momentum_trades"], 1):
            print(f"  {i}. {candidate['symbol']}: {candidate['change']:+.1%}")
            print(f"     → {candidate['reason']}")

        print("\n📊 MARKET ANOMALIES:")
        print(f"  Volume Spikes: {report['market_anomalies']['volume_spikes']}")
        print(f"  Volatility Spikes: {report['market_anomalies']['volatility_spikes']}")
        print(
            f"  Relative Strength Signals: {report['market_anomalies']['relative_strength']}"
        )


# Example usage
def demo():
    """Demonstrate market scanner."""
    from ...data import StockDataLoader

    print("=" * 90)
    print("  StockAI - Market Scanner & Anomaly Detector")
    print("=" * 90)

    # Load data
    loader = StockDataLoader()

    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "NFLX"]

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

    # Run scanner
    scanner = MarketScanner()
    results = scanner.scan_all(data, benchmark)

    # Print results
    scanner.print_results(results)

    # Alfred daily scan
    print("\n" + "=" * 90)
    print("  ALFRED DAILY SCAN")
    print("=" * 90)

    alfred = AlfredMarketScanner()
    report = alfred.daily_scan(data, benchmark)
    alfred.print_daily_report(report)


if __name__ == "__main__":
    demo()
