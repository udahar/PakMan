# StockAI - Fourth Institutional Signal: Market Breadth

**Status:** ✅ **COMPLETE** - Market Breadth Divergence implemented

---

## 🎯 The Fourth Signal: Market Breadth Divergence

**What it measures:** How many stocks are participating in market moves

**Why hedge funds watch it:** Indexes can lie - breadth tells the truth

---

## 📊 The Problem with Indexes

Indexes like S&P 500 are **weighted** toward a few giants:

```
Example:
Apple + Microsoft + Nvidia + Amazon can push S&P up
While 400 other stocks are falling

Index says: "Market is strong" 📈
Reality: "Only 4 stocks are strong" 📉
```

**Breadth reveals the truth.**

---

## 🔍 Core Metrics

### 1. **Advance/Decline Ratio**

```python
advancing = stocks closing higher
declining = stocks closing lower

A/D Ratio = advancing / declining
```

**Example:**
```
3000 stocks up
1500 stocks down
A/D Ratio = 2.0 → Healthy market
```

### 2. **New Highs/New Lows Ratio**

```python
new_highs = stocks at 52-week highs
new_lows = stocks at 52-week lows

NH/NL Ratio = new_highs / new_lows
```

**Example:**
```
200 new highs
50 new lows
NH/NL = 4.0 → Very healthy
```

### 3. **Percent Above Moving Averages**

```python
pct_above_MA50 = stocks above 50-day MA / total stocks
pct_above_MA200 = stocks above 200-day MA / total stocks
```

**Interpretation:**
- >70% = Overbought
- 50-70% = Healthy
- 30-50% = Weak
- <30% = Oversold (potential bottom)

---

## 🚨 Breadth Divergence Signals

### **Bearish Divergence** (Crash Warning)

```
S&P 500: Rising 📈
A/D Ratio: Falling 📉
New Highs: Decreasing 📉

Interpretation:
Only large caps holding index up
Breadth weakening underneath
Crash risk increasing
```

**What it means:** The index is being propped up by a few big stocks while the broad market deteriorates.

---

### **Bullish Divergence** (Bottom Signal)

```
S&P 500: Falling 📉
A/D Ratio: Improving 📈
Advancing stocks: Increasing 📈

Interpretation:
Market internally getting stronger
Despite index decline
Often happens near bottoms
```

**What it means:** The index is falling but more stocks are participating in the rally - internal strength building.

---

## 📈 Market Health Score

**StockAI calculates a 0-100 health score:**

| Score | Interpretation | Action |
|-------|---------------|--------|
| 80-100 | **Very Healthy** | Risk-on |
| 60-79 | **Healthy** | Moderate risk |
| 40-59 | **Mixed** | Cautious |
| 20-39 | **Weak** | Defensive |
| 0-19 | **Very Weak** | High crash risk |

---

## 🏢 Sector Breadth

**Track breadth by sector:**

```
Sector Breadth Report:
┌─────────────────────────────────────────────┐
│ Sector      │ Adv/Dec │ % > MA50 │ % > MA200│
├─────────────────────────────────────────────┤
│ Energy      │  +6 / -1│   86%    │   0%     │ ← Strong
│ Technology  │  +1 / -9│   10%    │   0%     │ ← Weak
│ Financial   │  +0 / -8│    0%    │   0%     │ ← Very Weak
│ Healthcare  │  +0 / -8│   50%    │   0%     │ ← Mixed
│ Consumer    │  +1 / -7│   38%    │   0%     │ ← Weak
└─────────────────────────────────────────────┘
```

**Use:** See which sectors are leading vs lagging.

---

## 🤖 Alfred Integration

### Daily Market Reconnaissance

```python
def daily_breadth_scan():
    """Alfred's daily market breadth scan."""
    
    # Scan all stocks
    data = load_market_data()
    
    # Calculate breadth
    analyzer = MarketBreadthAnalyzer()
    breadth = analyzer.calculate_daily_breadth(data)
    health = analyzer.calculate_market_health(data, index_data)
    
    # Output
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "health_score": health.health_score,
        "advancing": breadth.advancing,
        "declining": breadth.declining,
        "divergence": health.divergence,  # BULLISH/BEARISH/NONE
        "sector_leaders": top_sectors,
        "signals": health.signals
    }
    
    return report
```

### Example Output

```
💚 Market Health Score: 10/100
  Breadth Trend:   NEUTRAL
  Participation:   WEAK
  
🏢 Sector Breadth:
  🟢 Energy      +6 / -1 | 86% > MA50
  🔴 Technology +1 / -9 | 10% > MA50
  🔴 Financial   +0 / -8 |  0% > MA50

📈 Interpretation:
  Market is WEAK - Poor participation, weak breadth
  
⚠️  WARNING: Bearish divergence detected
  Only large caps holding index up while breadth weakens
```

---

## 🎯 Why This Works

### 1. **Indexes Can Hide Reality**

```
S&P 500 is market-cap weighted:
- Top 10 stocks = ~35% of index
- Bottom 250 stocks = ~10% of index

So if Top 10 rise 5% and Bottom 250 fall 2%:
→ Index shows +2%
→ Reality: 250 stocks falling
```

### 2. **Breadth Predicts Turning Points**

```
Historical pattern:
- Market bottoms often show bullish divergence
- Market tops often show bearish divergence
- Breadth leads price by days/weeks
```

### 3. **Institutional Footprints**

```
When institutions rotate:
- They move many stocks at once
- Breadth shows the rotation
- Before indexes reflect it
```

---

## 📊 CLI Commands

### Full Breadth Analysis
```bash
python cli.py breadth --sectors
```

**Output:**
- Daily breadth (advancing/declining)
- A/D ratio
- NH/NL ratio
- Market health score
- Sector breadth
- Divergence alerts

---

## 🎯 Combined with Other Signals

**Four-signal stack:**

```python
total_score = (
    volume_shock * 0.20 +           # Individual stock
    relative_strength * 0.20 +       # Individual stock
    volatility_contraction * 0.20 +  # Individual stock
    market_breadth * 0.40            # Market-wide ← Most important!
)
```

**Why breadth gets highest weight:**
- It's market-wide (not stock-specific)
- It predicts turning points
- It reveals what indexes hide

---

## 📈 Real Example from Test

```
Market Health Score: 10/100 ← Very weak!

Daily Breadth:
  Advancing:  5
  Declining:  28
  A/D Ratio:  0.18 ← Very weak

Sector Breadth:
  Energy: +4/-1 (only strong sector)
  Tech: +0/-8 (very weak)
  Financial: +0/-7 (very weak)

Interpretation:
  Market is WEAK - Poor participation
```

**This is the kind of insight hedge funds pay millions for!**

---

## ✅ Complete Feature List

| Feature | Implemented | CLI |
|---------|-------------|-----|
| **A/D Ratio** | ✅ | ✅ |
| **NH/NL Ratio** | ✅ | ✅ |
| **% Above MA50** | ✅ | ✅ |
| **% Above MA200** | ✅ | ✅ |
| **Market Health Score** | ✅ | ✅ |
| **Breadth Divergence** | ✅ | ✅ |
| **Sector Breadth** | ✅ | ✅ |
| **Breadth History** | 📋 | - |

---

## 🚀 What Alfred Can Now Do

### Daily Market Recon
```
Every morning, Alfred outputs:
- Market Health Score (0-100)
- Breadth Trend (IMPROVING/WEAKENING)
- Divergence Alerts (BULLISH/BEARISH)
- Sector Leaders/Laggards
- % Above MA50/MA200
```

### Turning Point Detection
```
When breadth diverges from index:
🔴 BEARISH DIVERGENCE → Crash warning
🟢 BULLISH DIVERGENCE → Bottom forming
```

---

## 📊 All Four Institutional Signals

| Signal | Measures | Predicts |
|--------|----------|----------|
| **Volume Shock** | Institutional accumulation | Individual stock moves |
| **Relative Strength** | Stock vs market | Continued outperformance |
| **Volatility Contraction** | Energy build-up | Explosive breakouts |
| **Market Breadth** | Market participation | Market turning points |

---

**StockAI now has ALL FOUR hedge fund signals!** 📊🏦

**This is institutional-grade market analysis!**
