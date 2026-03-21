#!/usr/bin/env python3
"""
AI Stock Recommender

Use LLM to analyze patterns and generate recommendations.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class Recommendation:
    """Stock recommendation."""
    symbol: str
    action: str  # BUY, HOLD, SELL
    confidence: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH
    time_horizon: str  # SHORT, MEDIUM, LONG


class StockRecommender:
    """
    Generate AI-powered stock recommendations.
    
    Analyzes:
    - Technical patterns
    - Fundamental metrics
    - Market conditions
    - Risk factors
    """
    
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self._recommendations: List[Recommendation] = []
    
    def generate_recommendations(
        self,
        symbol: str,
        metrics: Dict,
        patterns: List[Dict],
        market_context: Optional[str] = None,
    ) -> Recommendation:
        """
        Generate recommendation for a stock.
        
        Args:
            symbol: Stock symbol
            metrics: Stock metrics (Sharpe, returns, etc.)
            patterns: Detected patterns
            market_context: Optional market context
        
        Returns:
            Recommendation object
        """
        # Build prompt for LLM
        prompt = self._build_prompt(symbol, metrics, patterns, market_context)
        
        # Call LLM (placeholder - would integrate with your AI system)
        analysis = self._analyze_with_llm(prompt)
        
        # Parse recommendation
        recommendation = self._parse_analysis(symbol, analysis)
        
        self._recommendations.append(recommendation)
        
        return recommendation
    
    def _build_prompt(
        self,
        symbol: str,
        metrics: Dict,
        patterns: List[Dict],
        market_context: Optional[str],
    ) -> str:
        """Build analysis prompt."""
        prompt = f"""Analyze this stock and provide investment recommendation:

SYMBOL: {symbol}

METRICS:
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
- Total Return: {metrics.get('total_return', 0):.1%}
- Volatility: {metrics.get('volatility', 0):.1%}
- Max Drawdown: {metrics.get('max_drawdown', 0):.1%}
- Win Rate: {metrics.get('win_rate', 0):.1%}
- Current Price: ${metrics.get('current_price', 0):.2f}

PATTERNS DETECTED:
"""
        
        for pattern in patterns[:5]:  # Top 5 patterns
            prompt += f"- {pattern.get('type', 'Unknown')}: {pattern.get('signal', 'NEUTRAL')} ({pattern.get('date', 'N/A')})\n"
        
        if market_context:
            prompt += f"\nMARKET CONTEXT:\n{market_context}\n"
        
        prompt += """
Provide recommendation in this format:
ACTION: [BUY|HOLD|SELL]
CONFIDENCE: [0.0-1.0]
TARGET_PRICE: [price or N/A]
STOP_LOSS: [price or N/A]
RISK_LEVEL: [LOW|MEDIUM|HIGH]
TIME_HORIZON: [SHORT|MEDIUM|LONG]
REASONING: [2-3 sentences]
"""
        
        return prompt
    
    def _analyze_with_llm(self, prompt: str) -> str:
        """Analyze with LLM."""
        # Placeholder - integrate with your AI system
        # For now, return mock analysis
        
        return """ACTION: BUY
CONFIDENCE: 0.75
TARGET_PRICE: N/A
STOP_LOSS: N/A
RISK_LEVEL: MEDIUM
TIME_HORIZON: LONG
REASONING: Strong technical indicators with positive patterns. Sharpe ratio indicates good risk-adjusted returns. Recent bullish patterns suggest upward momentum.
"""
    
    def _parse_analysis(self, symbol: str, analysis: str) -> Recommendation:
        """Parse LLM analysis into Recommendation."""
        lines = analysis.strip().split('\n')
        
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        return Recommendation(
            symbol=symbol,
            action=data.get('ACTION', 'HOLD'),
            confidence=float(data.get('CONFIDENCE', 0.5)),
            target_price=self._parse_price(data.get('TARGET_PRICE')),
            stop_loss=self._parse_price(data.get('STOP_LOSS')),
            reasoning=data.get('REASONING', ''),
            risk_level=data.get('RISK_LEVEL', 'MEDIUM'),
            time_horizon=data.get('TIME_HORIZON', 'MEDIUM'),
        )
    
    def _parse_price(self, value: str) -> Optional[float]:
        """Parse price from string."""
        if not value or value.upper() == 'N/A':
            return None
        
        try:
            return float(value.replace('$', '').replace(',', ''))
        except:
            return None
    
    def get_top_recommendations(self, min_confidence: float = 0.7) -> List[Recommendation]:
        """Get recommendations above confidence threshold."""
        return [
            r for r in self._recommendations
            if r.confidence >= min_confidence and r.action == 'BUY'
        ]
    
    def export_recommendations(self, filepath: str):
        """Export recommendations to JSON."""
        data = [
            {
                'symbol': r.symbol,
                'action': r.action,
                'confidence': r.confidence,
                'target_price': r.target_price,
                'stop_loss': r.stop_loss,
                'reasoning': r.reasoning,
                'risk_level': r.risk_level,
                'time_horizon': r.time_horizon,
            }
            for r in self._recommendations
        ]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Exported {len(data)} recommendations to {filepath}")


# Example usage
def demo():
    """Demonstrate AI recommendations."""
    print("=" * 60)
    print("  StockAI AI Recommender - Demo")
    print("=" * 60)
    
    from analyzer import StockAnalyzer
    from patterns import PatternRecognizer
    from data_loader import StockDataLoader
    
    # Load data
    loader = StockDataLoader()
    
    try:
        data = loader.load_multiple(["AAPL", "GOOGL", "MSFT"], period="2y")
    except Exception as e:
        print(f"Failed to load data: {e}")
        return
    
    # Analyze
    analyzer = StockAnalyzer()
    analyzer.load_data(data)
    metrics = analyzer.analyze_all()
    
    # Recognize patterns
    recognizer = PatternRecognizer()
    
    for symbol, df in data.items():
        recognizer.recognize_all(symbol, df)
    
    # Generate recommendations
    recommender = StockRecommender()
    
    print("\nGenerating AI recommendations...\n")
    
    for symbol, m in metrics.items():
        patterns = [p.__dict__ for p in recognizer._patterns if p.symbol == symbol]
        
        rec = recommender.generate_recommendations(
            symbol=symbol,
            metrics=m.__dict__,
            patterns=patterns,
        )
        
        print(f"{symbol}: {rec.action} (Confidence: {rec.confidence:.0%})")
        print(f"  Risk: {rec.risk_level} | Horizon: {rec.time_horizon}")
        print(f"  {rec.reasoning[:80]}...")
        print()
    
    # Show top recommendations
    top = recommender.get_top_recommendations(min_confidence=0.6)
    
    print("=" * 60)
    print("  Top BUY Recommendations")
    print("=" * 60)
    
    for rec in top:
        print(f"  {rec.symbol}: {rec.action} ({rec.confidence:.0%})")


if __name__ == "__main__":
    demo()
