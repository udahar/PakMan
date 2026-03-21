# StockAI - Hedge Fund Institutional Signals

**Status:** ✅ **COMPLETE** - Three powerful institutional signals implemented

---

## 🎯 Three Signals Hedge Funds Love

These signals measure **behavior**, not just price. They're powerful because they reveal what institutions are doing.

---

## 1. **Volume Shock** (Institutional Footprints) 📊

**What it detects:** Big funds entering/exiting positions

**Why it works:** Big funds cannot hide volume. When they accumulate or distribute, the tape shows it.

### Signal Formula
```python
volume_ratio = today_volume / avg_volume_30_days

Look for:
- volume_ratio > 3
- AND price_change < 2%
```

### Interpretation

| Scenario | Interpretation |
|----------|---------------|
| Volume 3x+ avg, Price up <2% | **Institutional accumulation** - quietly buying |
| Volume 3x+ avg, Price down <2% | **Institutional distribution** - quietly selling |

**Why it matters:** Often precedes multi-week runs once supply dries up.

### Example Output
```
🟢 VOLUME_SHOCK
   Strength: 75/100
   Action: BUY
   Huge volume (4.2x) with price up 1.2% - Institutional accumulation
   Volume: 4.2x average
```

---

## 2. **Relative Strength vs Market** 💪

**What it detects:** Stocks outperforming the broader market

**Why it works:** Stocks that consistently outperform tend to keep outperforming because institutions rotate capital into strength.

### Signal Formula
```python
stock_return_30d = (price_today - price_30d_ago) / price_30d_ago
sp500_return_30d = (spy_today - spy_30d_ago) / spy_30d_ago

relative_strength = stock_return_30d - sp500_return_30d
```

### Example
```
Stock: +5%
S&P 500: -3%
Relative Strength: +8%
```

### Interpretation

| Relative Strength | Signal | Meaning |
|------------------|--------|---------|
| > +10% | **STRONG BUY** | Significantly outperforming |
| +5% to +10% | **BUY** | Moderately outperforming |
| -5% to +5% | **WATCH** | Neutral vs market |
| < -5% | **SELL** | Underperforming |
| < -10% | **STRONG SELL** | Significantly underperforming |

### Example Output
```
🟢 RELATIVE_STRENGTH
   Strength: 87/100
   Action: BUY
   Strong relative strength: +17.4% vs market over 30 days
   vs Market: +17.4%
```

---

## 3. **Volatility Contraction** (Energy Build-Up) 🌀

**What it detects:** The calm before the storm

**Why it works:** When a stock quiets down while volume rises, it means buyers are accumulating. When the breakout comes, it can be explosive.

### Signal Formula
```python
daily_range = high - low
range_trend = slope(daily_range over last 10 days)
volume_trend = slope(volume over last 10 days)

Look for:
- range_trend < 0 (contracting volatility)
- AND volume_trend > 0 (rising volume)
```

### Interpretation

| Pattern | Meaning |
|---------|---------|
| Range ↓, Volume ↑ | **Energy building** - explosive move coming |
| Range ↑, Volume ↓ | **Distribution** - trend weakening |
| Range ↑, Volume ↑ | **Breakout/breakdown** in progress |
| Range ↓, Volume ↓ | **Consolidation** - waiting for catalyst |

### Example Output
```
🟢 VOLATILITY_CONTRACTION
   Strength: 82/100
   Action: BUY
   Volatility contracting (0.6x) while volume rises - Energy building for breakout
   Contraction: 0.6x
```

---

## 🎯 Combined Scoring Model

**Hedge funds combine these signals:**

```python
score = (
    relative_strength * 0.35 +
    volume_shock * 0.35 +
    volatility_contraction * 0.30
)
```

### What the Combined Score Tells You

| Score | Interpretation | Action |
|-------|---------------|--------|
| 80-100 | **All signals aligned** | Strong conviction |
| 60-79 | **Multiple signals positive** | Moderate conviction |
| 40-59 | **Mixed signals** | Watch/Wait |
| <40 | **Negative signals** | Avoid/Sell |

---

## 📊 How to Use

### CLI Command
```bash
# Scan for institutional signals
python cli.py institutional AAPL GOOGL MSFT NVDA TSLA

# Output shows:
# - All detected signals
# - Ranked stocks by combined score
```

### Python API
```python
from institutional_signals import InstitutionalSignals

analyzer = InstitutionalSignals()

# Scan multiple stocks
all_signals = analyzer.scan_multiple_stocks(data, benchmark)

# Get ranked list
ranked = analyzer.rank_stocks_by_score(all_signals)

# Top candidate
top_stock, top_score, top_signals = ranked[0]
```

---

## 🔍 Real Example from Test Run

```
Rank  Symbol  Score  Signals
----------------------------
   1  NFLX    87     relative_strength
   2  AAPL    50     relative_strength
   3  GOOGL   50     relative_strength
```

**NFLX detected with +17.4% relative strength** → Strong institutional favorite

---

## 🤖 Alfred Integration

### Daily Market Reconnaissance

```python
def daily_institutional_scan():
    """Alfred's daily institutional signal scan."""
    
    # Load data
    data = load_stock_data()
    benchmark = load_benchmark("SPY")
    
    # Scan
    analyzer = InstitutionalSignals()
    all_signals = analyzer.scan_multiple_stocks(data, benchmark)
    
    # Rank
    ranked = analyzer.rank_stocks_by_score(all_signals)
    
    # Output top candidates
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "top_breakout_candidates": ranked[:5],
        "volume_shocks": [s for s in all_signals if s.signal_type == 'volume_shock'],
        "relative_strength_leaders": [s for s in all_signals if s.signal_type == 'relative_strength' and s.score > 0.10],
        "volatility_squeezes": [s for s in all_signals if s.signal_type == 'volatility_contraction']
    }
    
    return report
```

---

## 📈 Variables Tracked

### Volume Shock
- ✅ Volume today
- ✅ Volume 30-day average
- ✅ Volume ratio
- ✅ Price change %

### Relative Strength
- ✅ Stock return (30-day)
- ✅ Benchmark return (30-day)
- ✅ Relative strength differential

### Volatility Contraction
- ✅ Daily range (high - low)
- ✅ Range percentage (range/close)
- ✅ Range trend (10-day slope)
- ✅ Volume trend (10-day slope)
- ✅ Contraction ratio

---

## 🎯 Why These Signals Work

### 1. **Volume Shock** - Follow the Smart Money
- Institutions move markets
- They can't hide their volume
- Detect accumulation before price moves

### 2. **Relative Strength** - Momentum is Real
- Institutions rotate into strength
- Outperformance tends to persist
- Measures stock vs entire market

### 3. **Volatility Contraction** - Energy Physics
- Compression → Expansion
- Quiet accumulation → Explosive move
- Measures supply/demand imbalance

---

## ✅ Complete Feature List

| Signal | Implemented | CLI | Scoring |
|--------|-------------|-----|---------|
| **Volume Shock** | ✅ | ✅ | ✅ |
| **Relative Strength** | ✅ | ✅ | ✅ |
| **Volatility Contraction** | ✅ | ✅ | ✅ |
| **Combined Scoring** | ✅ | ✅ | ✅ |
| **Stock Ranking** | ✅ | ✅ | ✅ |

---

## 🚀 Next Level: The Fourth Signal

ChatGPT mentioned a **fourth signal** that "predicts market turning points days in advance."

This would require:
- Tracking the **entire market** daily
- Computing breadth indicators
- Advance/decline ratios
- New highs vs new lows

**Want me to build this?** It's the final piece for complete market reconnaissance.

---

**StockAI now has institutional-grade signals!** 📊🏦
