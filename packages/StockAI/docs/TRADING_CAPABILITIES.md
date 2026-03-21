# StockAI - Complete Trading Analysis Capabilities

**Status:** ✅ Complete - Day Trading + Long-Term Analysis

---

## 🎯 New Capabilities Added

### 1. **Day Trading / Swing Trading Analysis** (`day_trading.py`)

**Three Trading Strategies:**

#### A. Mean Reversion (Oversold Bounce)
**Buy when:**
- Stock down >5-10% in one day
- RSI < 30 (oversold)
- Volume spike > 1.5× average
- Price far below 20-day MA

**Sell when:**
- Price rebounds 3-5%
- RSI normalizes (~50)

#### B. Momentum Trading (Breakout Continuation)
**Buy when:**
- Price breaks 20-day high
- Volume > 2× average
- Trend slope positive (>5%)
- MA20 > MA50 (bullish)

**Sell when:**
- Momentum fades

#### C. Gap Reversal
**Gap up >4%** → Short when momentum stalls  
**Gap down >4%** → Buy if reversal starts

---

### 2. **Long-Term Hold Analysis** (`long_term_hold.py`)

**Four Component Scores:**

#### Financial Strength (30% weight)
- Profit margins
- Operating margins
- Debt-to-equity
- Current ratio (liquidity)

#### Growth Score (30% weight)
- Revenue growth
- EPS growth
- 6-month price momentum

#### Valuation Score (25% weight)
- P/E ratio
- PEG ratio
- Forward P/E
- Price-to-book

#### Momentum Score (15% weight)
- Distance from 52-week high
- Above/below 200-day MA
- Institutional ownership

**Rating Scale:**
- **STRONG_BUY:** 80-100
- **BUY:** 65-79
- **HOLD:** 50-64
- **SELL:** 35-49
- **STRONG_SELL:** <35

---

## 📊 CLI Commands

### Day Trading Analysis
```bash
python cli.py day-trading AAPL GOOGL NVDA TSLA --count 10
```

**Output:**
```
📊 Day Trading Signals (5 found)

🟢 AAPL - MEAN_REVERSION
   Action: BUY
   Strength: 75%
   Entry: $255.76
   Target: $268.55 (+5.0%)
   Stop: $242.97 (-5.0%)
   Timeframe: swing_3d
   Reasoning:
     • Daily drop: -6.2%
     • RSI oversold: 28.5
     • Volume spike: 1.8x
```

### Long-Term Analysis
```bash
python cli.py long-term AAPL GOOGL MSFT NVDA JPM XOM JNJ
```

**Output:**
```
📈 Long-Term Investment Ratings (7 stocks)

🟢 GOOGL - STRONG_BUY
   Overall Score: 82/100
   Financial Strength: 100/100
   Growth Score: 100/100
   Valuation Score: 50/100
   Momentum Score: 65/100

   Key Metrics:
     P/E: 28.1 | PEG: 0.0 | D/E: 16.1
     Revenue Growth: 18.0% | EPS Growth: 31.1%
     Price: $303.55 | 52W High: $349.00

   Reasoning:
     • Strong financials (score: 100)
     • Strong growth: 18.0% revenue, 31.1% EPS
```

---

## 🛠️ All Available Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `analyze` | Basic metrics | `python cli.py analyze AAPL GOOGL` |
| `patterns` | Candlestick patterns | `python cli.py patterns AAPL --days 90` |
| `recommend` | AI recommendations | `python cli.py recommend AAPL GOOGL` |
| `top` | Top performers | `python cli.py top AAPL GOOGL MSFT` |
| `day-trading` | Day trading signals | `python cli.py day-trading AAPL NVDA` |
| `long-term` | Long-term ratings | `python cli.py long-term AAPL GOOGL JNJ` |

---

## 📈 Integration with Market Scanner

### Daily Pipeline (Alfred-style)

```python
from StockAI.day_trading import DayTradingAnalyzer
from StockAI.long_term_hold import LongTermAnalyzer
from StockAI.data_loader import StockDataLoader

# Load data
loader = StockDataLoader()
data = loader.load_multiple(symbols, period="3mo")

# Day trading scan
day_analyzer = DayTradingAnalyzer()
day_signals = day_analyzer.get_top_signals(data, top_n=10)

# Long-term analysis
long_analyzer = LongTermAnalyzer()
long_ratings = long_analyzer.analyze_multiple(data, info_dict)

# Output
print("Top 5 rebound candidates:")
for signal in day_signals[:5]:
    print(f"  {signal.symbol}: {signal.action} ({signal.strength:.0%})")

print("\nTop 5 long-term holds:")
for rating in long_ratings[:5]:
    print(f"  {rating.symbol}: {rating.rating} (Score: {rating.overall_score:.0f})")
```

---

## 🎯 Market Anomaly Detector

### Sector Rotation Detection

```python
# Track sector performance
sectors = {
    'Tech': ['AAPL', 'GOOGL', 'MSFT', 'NVDA'],
    'Energy': ['XOM', 'CVX', 'COP'],
    'Financial': ['JPM', 'BAC', 'GS'],
}

for sector_name, stocks in sectors.items():
    sector_return = calculate_sector_return(stocks)
    print(f"{sector_name}: {sector_return:.1%}")

# Detect relative strength
# If Tech down 6% sector-wide but one stock only down 1%
# → That's relative strength (huge signal)
```

---

## 📊 Variables Tracked

### Price & Volume
- Daily change %
- 5-day change %
- Volume ratio (vs 20-day avg)
- Distance from MA20/MA50/MA200

### Technical Indicators
- RSI (14-day)
- MACD (12,26,9)
- Bollinger Bands (20,2)
- 52-week high/low distance

### Fundamental Metrics
- Revenue growth
- EPS growth
- Free cash flow yield
- P/E, PEG ratios
- Debt-to-equity
- Institutional ownership

---

## 🔍 Backtesting Framework (Future)

```python
# Example backtest strategy
def backtest_mean_reversion(df, symbol):
    """
    If RSI < 30
    AND price < MA20 by 5%
    → BUY
    
    Sell after 3 days
    """
    signals = []
    
    for i in range(30, len(df)):
        rsi = calculate_rsi(df['Close'][:i]).iloc[-1]
        ma_20 = df['Close'][:i].rolling(20).mean().iloc[-1]
        
        if rsi < 30 and df['Close'].iloc[-1] < ma_20 * 0.95:
            # Buy signal
            entry = df['Close'].iloc[-1]
            exit_price = df['Close'].iloc[-1 + 3]  # Exit after 3 days
            
            return_pct = (exit_price - entry) / entry
            signals.append(return_pct)
    
    return signals

# Run across history
returns = backtest_mean_reversion(df, "AAPL")
print(f"Strategy win rate: {sum(1 for r in returns if r > 0) / len(returns):.1%}")
```

---

## 🤖 Alfred Integration

### Market Scanner Agent

```python
def daily_market_scan():
    """Daily market analysis for Alfred."""
    
    # Scan all watched stocks
    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "JPM", "XOM", "JNJ"]
    
    loader = StockDataLoader()
    data = loader.load_multiple(symbols, period="3mo")
    
    # Day trading opportunities
    day_analyzer = DayTradingAnalyzer()
    day_signals = day_analyzer.get_top_signals(data, top_n=5)
    
    # Long-term picks
    long_analyzer = LongTermAnalyzer()
    # ... get info from yfinance ...
    long_ratings = long_analyzer.analyze_multiple(data, info_dict)
    
    # Output for Alfred
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "day_trading": [
            {"symbol": s.symbol, "action": s.action, "strength": s.strength}
            for s in day_signals
        ],
        "long_term": [
            {"symbol": r.symbol, "rating": r.rating, "score": r.overall_score}
            for r in long_ratings[:5]
        ]
    }
    
    return report
```

---

## ✅ Complete Feature List

### Day Trading
- ✅ Mean reversion scanner
- ✅ Momentum scanner
- ✅ Gap reversal scanner
- ✅ RSI calculation
- ✅ MACD calculation
- ✅ Bollinger Bands
- ✅ Volume spike detection
- ✅ Signal strength scoring

### Long-Term
- ✅ Financial strength analysis
- ✅ Growth scoring
- ✅ Valuation analysis
- ✅ Momentum scoring
- ✅ Institutional ownership tracking
- ✅ 52-week high/low analysis
- ✅ P/E, PEG, D/E ratios
- ✅ Revenue/EPS growth tracking

### CLI
- ✅ `day-trading` command
- ✅ `long-term` command
- ✅ All existing commands working
- ✅ JSON export support

---

**StockAI now has complete trading analysis capabilities!** 📊🤖
