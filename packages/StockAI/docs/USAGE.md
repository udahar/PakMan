# StockAI - Complete Usage Guide

**AI-Powered Stock Analysis System**

Analyze 10+ years of financial data, identify patterns, and get AI recommendations.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy yfinance
```

### 2. Analyze Stocks

```bash
cd PromptRD/StockAI

# Analyze multiple stocks
python cli.py analyze AAPL GOOGL MSFT NVDA AMZN --period 5y

# Recognize patterns
python cli.py patterns AAPL --days 90

# Get AI recommendations
python cli.py recommend AAPL GOOGL MSFT --period 2y

# Show top performers
python cli.py top AAPL GOOGL MSFT --count 10
```

---

## Python API

```python
from StockAI import StockDataLoader, StockAnalyzer, PatternRecognizer, StockRecommender

# Load data
loader = StockDataLoader()
data = loader.load_multiple(["AAPL", "GOOGL"], period="5y")

# Analyze
analyzer = StockAnalyzer()
analyzer.load_data(data)
metrics = analyzer.analyze_all()

# Get metrics for AAPL
aapl_metrics = analyzer.get_metrics("AAPL")
print(f"Sharpe: {aapl_metrics.sharpe_ratio:.2f}")
print(f"Return: {aapl_metrics.total_return:.1%}")

# Recognize patterns
recognizer = PatternRecognizer()
patterns = recognizer.recognize_all("AAPL", data["AAPL"])

# Get AI recommendation
recommender = StockRecommender()
rec = recommender.generate_recommendations(
    symbol="AAPL",
    metrics=aapl_metrics.__dict__,
    patterns=[p.__dict__ for p in patterns],
)

print(f"{rec.symbol}: {rec.action} (Confidence: {rec.confidence:.0%})")
```

---

## Commands

### `analyze` - Analyze Stocks

Calculate metrics for multiple stocks.

```bash
python cli.py analyze AAPL GOOGL MSFT --period 5y
```

**Output:**
- Total return
- Annualized return
- Sharpe ratio
- Max drawdown
- Win rate
- Current price vs 52-week range

---

### `patterns` - Recognize Patterns

Identify trading patterns.

```bash
python cli.py patterns AAPL --days 90
```

**Patterns detected:**
- Bullish/Bearish Engulfing
- Hammer
- Golden/Death Cross
- Breakouts/Breakdowns
- Volume spikes

---

### `recommend` - AI Recommendations

Generate AI-powered recommendations.

```bash
python cli.py recommend AAPL GOOGL MSFT --output recommendations.json
```

**Output:**
- BUY/HOLD/SELL recommendation
- Confidence level
- Risk assessment
- Time horizon
- Reasoning

---

### `top` - Top Performers

Show best stocks by metric.

```bash
python cli.py top AAPL GOOGL MSFT NVDA --count 10
```

**Sorted by:**
- Sharpe ratio (default)
- Total return
- Win rate

---

## Metrics Explained

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 |
| **Total Return** | Overall gain/loss | Higher is better |
| **Volatility** | Price fluctuation | Lower is safer |
| **Max Drawdown** | Worst peak-to-trough | Lower is better |
| **Win Rate** | % of profitable days | > 55% |

---

## Pattern Signals

| Pattern | Signal | Confidence |
|---------|--------|------------|
| Golden Cross | BUY | High (0.9) |
| Death Cross | SELL | High (0.9) |
| Bullish Engulfing | BUY | Medium (0.8) |
| Hammer | BUY | Medium (0.7) |
| Breakout | BUY | Medium (0.75) |
| Volume Spike | Varies | Medium (0.8) |

---

## Data Sources

### Yahoo Finance (Default)
```python
loader.load_yahoo("AAPL", period="5y")
```

### CSV Files
```python
loader.load_csv("data/AAPL.csv", "AAPL")
```

**CSV format:**
```csv
Date,Open,High,Low,Close,Volume
2024-01-01,185.00,186.50,184.00,186.00,1000000
```

---

## Example Workflow

### 1. Load Data
```python
from StockAI import StockDataLoader

loader = StockDataLoader()
symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "AMZN"]
data = loader.load_multiple(symbols, period="5y")
```

### 2. Analyze
```python
from StockAI import StockAnalyzer

analyzer = StockAnalyzer()
analyzer.load_data(data)
metrics = analyzer.analyze_all()
```

### 3. Find Patterns
```python
from StockAI import PatternRecognizer

recognizer = PatternRecognizer()
for symbol, df in data.items():
    patterns = recognizer.recognize_all(symbol, df)
```

### 4. Get Recommendations
```python
from StockAI import StockRecommender

recommender = StockRecommender()
for symbol, m in metrics.items():
    rec = recommender.generate_recommendations(
        symbol=symbol,
        metrics=m.__dict__,
        patterns=[p.__dict__ for p in recognizer._patterns if p.symbol == symbol],
    )
    print(f"{symbol}: {rec.action}")
```

### 5. Export Results
```python
recommender.export_recommendations("recommendations.json")
```

---

## Files Created

```
StockAI/
├── __init__.py          # Package exports
├── README.md            # This guide
├── data_loader.py       # Data ingestion
├── analyzer.py          # Core analysis
├── patterns.py          # Pattern recognition
├── recommender.py       # AI recommendations
├── cli.py               # Command-line interface
└── data/                # Stock data (auto-created)
```

---

## Next Steps

### 1. Backtest Strategies
```python
# Coming soon: strategies/backtester.py
```

### 2. Dashboard UI
```bash
# Coming soon: Streamlit dashboard
streamlit run ui/dashboard.py
```

### 3. Integrate with Frank/Alfred
```python
# Use with your AI system
from StockAI import StockRecommender

# Alfred can now analyze stocks!
```

---

## Risk Disclaimer

**This is for educational/research purposes only.**

- Not financial advice
- Past performance ≠ future results
- Always do your own research
- Consult a financial advisor

---

**StockAI is ready to analyze!** 📈🤖
