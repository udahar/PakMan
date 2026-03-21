#!/usr/bin/env python3
"""
Pattern Recognition for Stock Analysis

Identify patterns that precede growth spikes.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """Types of patterns."""
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    DOJI = "doji"
    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    VOLUME_SPIKE = "volume_spike"


@dataclass
class Pattern:
    """Detected pattern."""
    type: PatternType
    date: str
    symbol: str
    confidence: float
    description: str
    signal: str  # BUY, SELL, NEUTRAL


class PatternRecognizer:
    """
    Recognize patterns in stock data.
    
    Identifies:
    - Candlestick patterns
    - Moving average crossovers
    - Breakouts/breakdowns
    - Volume anomalies
    """
    
    def __init__(self):
        self._patterns: List[Pattern] = []
    
    def recognize_all(self, symbol: str, df: pd.DataFrame) -> List[Pattern]:
        """
        Recognize all patterns in data.
        
        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
        
        Returns:
            List of detected patterns
        """
        self._patterns = []
        
        # Calculate indicators first
        df = self._add_indicators(df)
        
        # Recognize patterns
        self._recognize_candlestick(symbol, df)
        self._recognize_crossovers(symbol, df)
        self._recognize_breakouts(symbol, df)
        self._recognize_volume_patterns(symbol, df)
        
        return self._patterns
    
    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators."""
        result = df.copy()
        
        # Moving averages
        result['SMA_20'] = result['Close'].rolling(window=20).mean()
        result['SMA_50'] = result['Close'].rolling(window=50).mean()
        result['SMA_200'] = result['Close'].rolling(window=252).mean()
        
        # Volume MA
        result['Volume_MA'] = result['Volume'].rolling(window=20).mean()
        
        return result
    
    def _recognize_candlestick(self, symbol: str, df: pd.DataFrame):
        """Recognize candlestick patterns."""
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Bullish Engulfing
            if (prev['Close'] < prev['Open'] and  # Previous was red
                row['Close'] > row['Open'] and      # Current is green
                row['Open'] < prev['Close'] and     # Current open below prev close
                row['Close'] > prev['Open']):       # Current close above prev open
                
                self._patterns.append(Pattern(
                    type=PatternType.BULLISH_ENGULFING,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.8,
                    description="Bullish engulfing pattern detected",
                    signal="BUY"
                ))
            
            # Hammer
            body = abs(row['Close'] - row['Open'])
            lower_shadow = min(row['Close'], row['Open']) - row['Low']
            upper_shadow = row['High'] - max(row['Close'], row['Open'])
            
            if (lower_shadow > body * 2 and  # Long lower shadow
                upper_shadow < body * 0.5 and  # Small upper shadow
                body > 0):  # Has body
                
                self._patterns.append(Pattern(
                    type=PatternType.HAMMER,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.7,
                    description="Hammer candlestick pattern",
                    signal="BUY"
                ))
    
    def _recognize_crossovers(self, symbol: str, df: pd.DataFrame):
        """Recognize moving average crossovers."""
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Golden Cross (SMA_50 crosses above SMA_200)
            if (prev['SMA_50'] <= prev['SMA_200'] and
                row['SMA_50'] > row['SMA_200']):
                
                self._patterns.append(Pattern(
                    type=PatternType.GOLDEN_CROSS,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.9,
                    description="Golden Cross - bullish long-term signal",
                    signal="BUY"
                ))
            
            # Death Cross (SMA_50 crosses below SMA_200)
            if (prev['SMA_50'] >= prev['SMA_200'] and
                row['SMA_50'] < row['SMA_200']):
                
                self._patterns.append(Pattern(
                    type=PatternType.DEATH_CROSS,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.9,
                    description="Death Cross - bearish long-term signal",
                    signal="SELL"
                ))
    
    def _recognize_breakouts(self, symbol: str, df: pd.DataFrame):
        """Recognize breakouts and breakdowns."""
        # Calculate 20-day high/low
        df['High_20'] = df['High'].rolling(window=20).max()
        df['Low_20'] = df['Low'].rolling(window=20).min()
        
        for i in range(21, len(df)):
            row = df.iloc[i]
            
            # Breakout above 20-day high
            if row['Close'] > row['High_20']:
                self._patterns.append(Pattern(
                    type=PatternType.BREAKOUT,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.75,
                    description=f"Broke above 20-day high of {row['High_20']:.2f}",
                    signal="BUY"
                ))
            
            # Breakdown below 20-day low
            if row['Close'] < row['Low_20']:
                self._patterns.append(Pattern(
                    type=PatternType.BREAKDOWN,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.75,
                    description=f"Broke below 20-day low of {row['Low_20']:.2f}",
                    signal="SELL"
                ))
    
    def _recognize_volume_patterns(self, symbol: str, df: pd.DataFrame):
        """Recognize volume anomalies."""
        for i in range(1, len(df)):
            row = df.iloc[i]
            
            # Volume spike (> 2x average)
            if row['Volume'] > row['Volume_MA'] * 2:
                # Check if price also moved significantly
                price_change = row['Close'] / df.iloc[i-1]['Close'] - 1
                
                signal = "BUY" if price_change > 0.02 else "SELL" if price_change < -0.02 else "NEUTRAL"
                
                self._patterns.append(Pattern(
                    type=PatternType.VOLUME_SPIKE,
                    date=str(row.name.date()),
                    symbol=symbol,
                    confidence=0.8,
                    description=f"Volume spike: {row['Volume']:,} ({row['Volume']/row['Volume_MA']:.1f}x avg)",
                    signal=signal
                ))
    
    def get_recent_patterns(self, days: int = 30) -> List[Pattern]:
        """Get patterns from recent days."""
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        return [
            p for p in self._patterns
            if datetime.strptime(p.date, '%Y-%m-%d') > cutoff
        ]
    
    def get_signals(self, symbol: Optional[str] = None) -> Dict[str, List[Pattern]]:
        """
        Get trading signals from patterns.
        
        Returns:
            Dictionary of signal type -> patterns
        """
        signals = {
            'BUY': [],
            'SELL': [],
            'NEUTRAL': []
        }
        
        patterns = self._patterns
        if symbol:
            patterns = [p for p in patterns if p.symbol == symbol]
        
        for pattern in patterns:
            signals[pattern.signal].append(pattern)
        
        return signals


# Example usage
def demo():
    """Demonstrate pattern recognition."""
    print("=" * 60)
    print("  StockAI Pattern Recognition - Demo")
    print("=" * 60)
    
    from data_loader import StockDataLoader
    
    # Load data
    loader = StockDataLoader()
    
    try:
        df = loader.load_yahoo("AAPL", period="2y")
    except Exception as e:
        print(f"Failed to load data: {e}")
        print("Install yfinance: pip install yfinance")
        return
    
    # Recognize patterns
    recognizer = PatternRecognizer()
    patterns = recognizer.recognize_all("AAPL", df)
    
    print(f"\nDetected {len(patterns)} patterns\n")
    
    # Show recent patterns
    recent = recognizer.get_recent_patterns(days=90)
    
    print(f"Recent patterns (last 90 days): {len(recent)}\n")
    
    for pattern in recent[:10]:  # Show first 10
        print(f"{pattern.date} | {pattern.type.value:20} | {pattern.signal:6} | {pattern.description}")
    
    # Show signals
    signals = recognizer.get_signals()
    
    print(f"\n{'='*60}")
    print("  Trading Signals")
    print(f"{'='*60}")
    print(f"  BUY signals: {len(signals['BUY'])}")
    print(f"  SELL signals: {len(signals['SELL'])}")
    print(f"  NEUTRAL: {len(signals['NEUTRAL'])}")


if __name__ == "__main__":
    demo()
