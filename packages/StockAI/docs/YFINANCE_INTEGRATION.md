# StockAI + yfinance Integration

**Status:** ✅ Integrated

---

## Integration Overview

StockAI uses the **local yfinance package** included in this directory:

```
StockAI/
├── yfinance-main/
│   └── yfinance-main/
│       └── yfinance/      # ← Local yfinance package
├── data_loader.py         # ← Uses yfinance
├── analyzer.py
└── ...
```

---

## How It Works

### 1. Automatic Path Setup

When you import StockAI, it automatically adds the local yfinance to the Python path:

```python
from StockAI.data_loader import StockDataLoader

loader = StockDataLoader()

# This will use local yfinance
df = loader.load_yahoo("AAPL", period="5y")
```

### 2. Fallback to System yfinance

If you have yfinance installed system-wide, it will use that instead:

```bash
pip install yfinance
```

### 3. No Installation Required

If you don't have yfinance installed, StockAI will use the local copy:

```bash
# No pip install needed!
python -m StockAI.cli analyze AAPL GOOGL MSFT
```

---

## Usage

### Method 1: Use Local yfinance (No Installation)

```bash
cd PromptRD/StockAI

# Just run it - uses local yfinance
python cli.py analyze AAPL GOOGL MSFT
```

### Method 2: Install yfinance System-Wide (Recommended)

```bash
# Install from local package
cd StockAI/yfinance-main/yfinance-main
pip install -e .

# Now use StockAI from anywhere
python -m StockAI.cli analyze AAPL GOOGL
```

### Method 3: Use pip (If Internet Available)

```bash
pip install yfinance

# StockAI will automatically use it
python cli.py recommend AAPL GOOGL MSFT
```

---

## yfinance Features Available

StockAI can now access all yfinance features:

### Basic Data

```python
from StockAI.data_loader import StockDataLoader

loader = StockDataLoader()

# Historical prices
df = loader.load_yahoo("AAPL", period="5y")

# Company info
ticker = loader._load_ticker("AAPL")
info = ticker.info  # Company information
```

### Advanced Features

```python
import yfinance as yf

# Multiple tickers
tickers = yf.Tickers("AAPL GOOGL MSFT")
data = tickers.download(period="5y")

# Options
ticker = yf.Ticker("AAPL")
options = ticker.options

# Financials
financials = ticker.financials
balance_sheet = ticker.balance_sheet
cashflow = ticker.cashflow
```

---

## Integration Points

### With StockAI Analyzer

```python
from StockAI import StockAnalyzer, StockDataLoader

# Load data using yfinance
loader = StockDataLoader()
data = loader.load_multiple(["AAPL", "GOOGL"], period="5y")

# Analyze
analyzer = StockAnalyzer()
analyzer.load_data(data)
metrics = analyzer.analyze_all()

# Get recommendations
for symbol, m in metrics.items():
    print(f"{symbol}: {m.sharpe_ratio:.2f} Sharpe")
```

### With StockAI Patterns

```python
from StockAI import PatternRecognizer, StockDataLoader

loader = StockDataLoader()
df = loader.load_yahoo("AAPL", period="2y")

recognizer = PatternRecognizer()
patterns = recognizer.recognize_all("AAPL", df)

for pattern in patterns:
    print(f"{pattern.date}: {pattern.type.value} - {pattern.signal}")
```

### With StockAI Recommender

```python
from StockAI import StockRecommender, StockDataLoader, StockAnalyzer

# Load and analyze
loader = StockDataLoader()
data = loader.load_multiple(["AAPL"], period="2y")

analyzer = StockAnalyzer()
analyzer.load_data(data)
metrics = analyzer.analyze_all()

# Get AI recommendation
recommender = StockRecommender()
rec = recommender.generate_recommendations(
    symbol="AAPL",
    metrics=metrics["AAPL"].__dict__,
    patterns=[]
)

print(f"{rec.symbol}: {rec.action} ({rec.confidence:.0%})")
```

---

## yfinance Data Sources

### Yahoo Finance API

yfinance uses Yahoo Finance's API to fetch:

- **Historical prices** - OHLCV data
- **Company info** - Sector, industry, employees
- **Financials** - Income statement, balance sheet, cashflow
- **Options** - Option chains
- **Dividends** - Dividend history
- **Splits** - Stock split history
- **Recommendations** - Analyst recommendations

### Data Intervals

```python
# Different intervals available
df_1d = loader.load_yahoo("AAPL", period="1mo")  # 1 day interval
df_1h = loader.load_yahoo("AAPL", period="7d")   # 1 hour interval (if available)
df_1m = loader.load_yahoo("AAPL", period="2y")   # 1 month interval
```

---

## Troubleshooting

### yfinance Not Found

```
ModuleNotFoundError: No module named 'yfinance'
```

**Solution 1:** Use local package
```bash
# StockAI will automatically find it
python cli.py analyze AAPL
```

**Solution 2:** Install system-wide
```bash
cd StockAI/yfinance-main/yfinance-main
pip install -e .
```

### Rate Limiting

If you get rate-limited by Yahoo:

```python
# Add delays between requests
import time

symbols = ["AAPL", "GOOGL", "MSFT"]
for symbol in symbols:
    df = loader.load_yahoo(symbol)
    time.sleep(1)  # Wait 1 second between requests
```

### Data Missing

Some stocks may not have complete data:

```python
# Check if data is available
df = loader.load_yahoo("SYMBOL")
if df.empty:
    print("No data available for this symbol")
```

---

## Best Practices

### 1. Cache Data

```python
# Data is automatically cached
loader = StockDataLoader()
df = loader.load_yahoo("AAPL")  # Downloads

# Second time uses cache
df2 = loader.load_yahoo("AAPL")  # Uses cached data
```

### 2. Batch Load

```python
# Load multiple at once (more efficient)
data = loader.load_multiple(["AAPL", "GOOGL", "MSFT"], period="5y")
```

### 3. Handle Errors

```python
try:
    df = loader.load_yahoo("INVALID_SYMBOL")
except Exception as e:
    print(f"Failed to load: {e}")
```

### 4. Use Appropriate Periods

```python
# Day trading: Recent data
df = loader.load_yahoo("AAPL", period="1mo")

# Swing trading: Medium-term
df = loader.load_yahoo("AAPL", period="6mo")

# Long-term investing: Long history
df = loader.load_yahoo("AAPL", period="10y")
```

---

## License & Legal

**yfinance License:** Apache 2.0

**Important:**
- yfinance is **not** affiliated with Yahoo Finance
- For **research and educational purposes** only
- Refer to Yahoo's terms of use for data usage rights
- **Personal use only**

---

## Updates

To update the local yfinance package:

```bash
cd StockAI/yfinance-main/yfinance-main
git pull origin main
```

Or install latest from PyPI:

```bash
pip install --upgrade yfinance
```

---

**StockAI + yfinance = Complete stock analysis system!** 📈🤖
