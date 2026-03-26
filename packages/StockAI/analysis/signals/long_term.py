#!/usr/bin/env python3
"""
StockAI - Long-Term Hold Analysis

Fundamental analysis for long-term investment decisions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LongTermRating:
    """Long-term investment rating for a stock."""

    symbol: str
    overall_score: float  # 0-100
    rating: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL

    # Component scores (0-100)
    financial_strength: float
    growth_score: float
    valuation_score: float
    momentum_score: float

    # Key metrics
    revenue_growth: float
    eps_growth: float
    fcf_yield: float
    pe_ratio: float
    peg_ratio: float
    debt_to_equity: float
    institutional_ownership: float

    # Price data
    current_price: float
    price_52w_high: float
    price_52w_low: float
    distance_from_52w_high: float

    reasoning: List[str]


class LongTermAnalyzer:
    """
    Analyze stocks for long-term investment.

    Factors:
    - Financial strength (revenue, EPS, FCF, debt)
    - Growth (revenue growth, EPS growth)
    - Valuation (P/E, PEG, P/S)
    - Momentum (52-week trend, institutional ownership)
    """

    def __init__(self):
        self.ratings: List[LongTermRating] = []

    def calculate_financial_strength(self, info: Dict) -> float:
        """
        Calculate financial strength score (0-100).

        Based on:
        - Profitability
        - Debt levels
        - Cash flow
        """
        score = 50  # Base score

        # Profit margin
        profit_margin = info.get("profitMargins", 0)
        if profit_margin and profit_margin > 0:
            score += min(20, profit_margin * 100)  # Up to +20

        # Operating margin
        op_margin = info.get("operatingMargins", 0)
        if op_margin and op_margin > 0.15:
            score += 10  # +10 for strong ops

        # Debt to equity
        debt_equity = info.get("debtToEquity", 100)
        if debt_equity and debt_equity < 50:
            score += 10  # +10 for low debt
        elif debt_equity and debt_equity > 200:
            score -= 20  # -20 for high debt

        # Current ratio
        current_ratio = info.get("currentRatio", 1)
        if current_ratio and current_ratio > 1.5:
            score += 10  # +10 for good liquidity

        return min(100, max(0, score))

    def calculate_growth_score(self, info: Dict, df: pd.DataFrame) -> float:
        """
        Calculate growth score (0-100).

        Based on:
        - Revenue growth
        - EPS growth
        - Price momentum
        """
        score = 50  # Base

        # Revenue growth (if available)
        revenue_growth = info.get("revenueGrowth", 0)
        if revenue_growth and revenue_growth > 0.10:
            score += min(30, revenue_growth * 100)  # Up to +30
        elif revenue_growth and revenue_growth < 0:
            score -= 20

        # EPS growth
        eps_growth = info.get("earningsGrowth", 0)
        if eps_growth and eps_growth > 0.15:
            score += min(20, eps_growth * 100)  # Up to +20

        # Price momentum (6-month)
        if len(df) >= 126:  # ~6 months
            momentum_6m = (df["Close"].iloc[-1] - df["Close"].iloc[-126]) / df[
                "Close"
            ].iloc[-126]
            if momentum_6m > 0.20:
                score += 15
            elif momentum_6m < -0.20:
                score -= 15

        return min(100, max(0, score))

    def calculate_valuation_score(self, info: Dict) -> float:
        """
        Calculate valuation score (0-100).

        Based on:
        - P/E ratio
        - PEG ratio
        - Price/Sales
        """
        score = 50  # Base

        # P/E ratio
        pe_ratio = info.get("trailingPE", 25)
        if pe_ratio and pe_ratio < 15:
            score += 20  # Undervalued
        elif pe_ratio and pe_ratio > 40:
            score -= 20  # Overvalued

        # Forward P/E
        forward_pe = info.get("forwardPE", 20)
        if forward_pe and forward_pe < 15:
            score += 15
        elif forward_pe and forward_pe > 30:
            score -= 15

        # PEG ratio
        peg = info.get("pegRatio", 1.5)
        if peg and peg < 1.0:
            score += 20  # Good value for growth
        elif peg and peg > 2.0:
            score -= 20  # Expensive for growth

        # Price/Sales
        ps_ratio = info.get("priceToBook", 3)
        if ps_ratio and ps_ratio < 2:
            score += 10

        return min(100, max(0, score))

    def calculate_momentum_score(self, info: Dict, df: pd.DataFrame) -> float:
        """
        Calculate momentum score (0-100).

        Based on:
        - 52-week trend
        - Distance from highs
        - Institutional ownership
        """
        score = 50  # Base

        # 52-week high/low
        high_52w = info.get("fiftyTwoWeekHigh", df["High"].max())
        low_52w = info.get("fiftyTwoWeekLow", df["Low"].min())
        current = df["Close"].iloc[-1]

        # Distance from 52-week high
        distance_from_high = (current - high_52w) / high_52w
        if distance_from_high > -0.10:  # Within 10% of high
            score += 20
        elif distance_from_high < -0.30:  # Down >30% from high
            score -= 20

        # Above 200-day MA
        if len(df) >= 252:
            ma_200 = df["Close"].rolling(252).mean().iloc[-1]
            if current > ma_200:
                score += 15

        # Institutional ownership
        inst_ownership = info.get("institutionalOwnership", 0.50)
        if inst_ownership and inst_ownership > 0.70:
            score += 10  # High institutional confidence
        elif inst_ownership and inst_ownership < 0.30:
            score -= 10

        return min(100, max(0, score))

    def analyze_stock(
        self, symbol: str, df: pd.DataFrame, info: Dict
    ) -> LongTermRating:
        """
        Perform comprehensive long-term analysis on a stock.

        Args:
            symbol: Stock symbol
            df: Price data DataFrame
            info: Company info dictionary from yfinance

        Returns:
            LongTermRating with scores and reasoning
        """
        # Calculate component scores
        financial_strength = self.calculate_financial_strength(info)
        growth_score = self.calculate_growth_score(info, df)
        valuation_score = self.calculate_valuation_score(info)
        momentum_score = self.calculate_momentum_score(info, df)

        # Overall score (weighted average)
        overall_score = (
            financial_strength * 0.30
            + growth_score * 0.30
            + valuation_score * 0.25
            + momentum_score * 0.15
        )

        # Determine rating
        if overall_score >= 80:
            rating = "STRONG_BUY"
        elif overall_score >= 65:
            rating = "BUY"
        elif overall_score >= 50:
            rating = "HOLD"
        elif overall_score >= 35:
            rating = "SELL"
        else:
            rating = "STRONG_SELL"

        # Extract key metrics
        current_price = df["Close"].iloc[-1]
        high_52w = (
            info.get("fiftyTwoWeekHigh", df["High"].max())
            if len(df) >= 252
            else df["High"].max()
        )
        low_52w = (
            info.get("fiftyTwoWeekLow", df["Low"].min())
            if len(df) >= 252
            else df["Low"].min()
        )

        revenue_growth = info.get("revenueGrowth", 0) or 0
        eps_growth = info.get("earningsGrowth", 0) or 0
        pe_ratio = info.get("trailingPE", 0) or 0
        peg_ratio = info.get("pegRatio", 0) or 0
        debt_equity = info.get("debtToEquity", 0) or 0
        inst_ownership = info.get("institutionalOwnership", 0) or 0

        # FCF yield (approximation)
        fcf_yield = (
            info.get("freeCashflow", 0) / info.get("marketCap", 1)
            if info.get("freeCashflow") and info.get("marketCap")
            else 0
        )

        # Build reasoning
        reasoning = []

        if financial_strength >= 70:
            reasoning.append(f"Strong financials (score: {financial_strength:.0f})")
        elif financial_strength < 40:
            reasoning.append(f"Weak financials (score: {financial_strength:.0f})")

        if growth_score >= 70:
            reasoning.append(
                f"Strong growth: {revenue_growth:.1%} revenue, {eps_growth:.1%} EPS"
            )
        elif growth_score < 40:
            reasoning.append(f"Weak growth: {revenue_growth:.1%} revenue")

        if valuation_score >= 70:
            reasoning.append(
                f"Attractive valuation (P/E: {pe_ratio:.1f}, PEG: {peg_ratio:.1f})"
            )
        elif valuation_score < 40:
            reasoning.append(f"Expensive valuation (P/E: {pe_ratio:.1f})")

        if momentum_score >= 70:
            reasoning.append("Positive momentum")
        elif momentum_score < 40:
            reasoning.append("Negative momentum")

        return LongTermRating(
            symbol=symbol,
            overall_score=overall_score,
            rating=rating,
            financial_strength=financial_strength,
            growth_score=growth_score,
            valuation_score=valuation_score,
            momentum_score=momentum_score,
            revenue_growth=revenue_growth,
            eps_growth=eps_growth,
            fcf_yield=fcf_yield,
            pe_ratio=pe_ratio,
            peg_ratio=peg_ratio,
            debt_to_equity=debt_equity,
            institutional_ownership=inst_ownership,
            current_price=current_price,
            price_52w_high=high_52w,
            price_52w_low=low_52w,
            distance_from_52w_high=(current_price - high_52w) / high_52w
            if high_52w
            else 0,
            reasoning=reasoning,
        )

    def analyze_multiple(
        self, data: Dict[str, pd.DataFrame], info_dict: Dict[str, Dict]
    ) -> List[LongTermRating]:
        """Analyze multiple stocks for long-term investment."""
        ratings = []

        for symbol, df in data.items():
            info = info_dict.get(symbol, {})
            rating = self.analyze_stock(symbol, df, info)
            ratings.append(rating)

        # Sort by overall score
        ratings.sort(key=lambda r: r.overall_score, reverse=True)

        self.ratings = ratings
        return ratings

    def get_top_picks(self, n: int = 10) -> List[LongTermRating]:
        """Get top N long-term picks."""
        return [r for r in self.ratings if r.rating in ["STRONG_BUY", "BUY"]][:n]

    def print_ratings(self, ratings: List[LongTermRating]):
        """Print ratings in readable format."""
        if not ratings:
            print("No ratings available")
            return

        print("\n" + "=" * 90)
        print("  LONG-TERM INVESTMENT RATINGS")
        print("=" * 90)

        for rating in ratings:
            rating_emoji = {
                "STRONG_BUY": "🟢",
                "BUY": "🟢",
                "HOLD": "🟡",
                "SELL": "🔴",
                "STRONG_SELL": "🔴",
            }.get(rating.rating, "⚪")

            print(f"\n{rating_emoji} {rating.symbol} - {rating.rating}")
            print(f"   Overall Score: {rating.overall_score:.0f}/100")
            print(f"   Financial Strength: {rating.financial_strength:.0f}/100")
            print(f"   Growth Score: {rating.growth_score:.0f}/100")
            print(f"   Valuation Score: {rating.valuation_score:.0f}/100")
            print(f"   Momentum Score: {rating.momentum_score:.0f}/100")
            print(f"   ")
            print(f"   Key Metrics:")
            print(
                f"     P/E: {rating.pe_ratio:.1f} | PEG: {rating.peg_ratio:.1f} | D/E: {rating.debt_to_equity:.1f}"
            )
            print(
                f"     Revenue Growth: {rating.revenue_growth:.1%} | EPS Growth: {rating.eps_growth:.1%}"
            )
            print(
                f"     Price: ${rating.current_price:.2f} | 52W High: ${rating.price_52w_high:.2f}"
            )
            print(f"   ")
            print(f"   Reasoning:")
            for reason in rating.reasoning:
                print(f"     • {reason}")


# Example usage
def demo():
    """Demonstrate long-term analysis."""
    from ...data import StockDataLoader

    print("=" * 90)
    print("  StockAI - Long-Term Investment Analysis")
    print("=" * 90)

    # Load data
    loader = StockDataLoader()

    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "AMZN", "JPM", "XOM", "JNJ"]

    try:
        data = loader.load_multiple(symbols, period="2y")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Get company info (simplified - in production would fetch from yfinance)
    info_dict = {}

    # Analyze
    analyzer = LongTermAnalyzer()
    ratings = analyzer.analyze_multiple(data, info_dict)

    # Print
    analyzer.print_ratings(ratings)

    # Top picks
    print("\n" + "=" * 90)
    print("  TOP LONG-TERM PICKS")
    print("=" * 90)

    top_picks = analyzer.get_top_picks(5)
    for pick in top_picks:
        print(f"  {pick.symbol}: {pick.rating} (Score: {pick.overall_score:.0f})")

    print("\n" + "=" * 90)
    print("  ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    demo()
