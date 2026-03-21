# Installing yfinance

StockAI includes the yfinance package locally, but you'll need to install its dependencies.

---

## Option 1: Install yfinance (Recommended)

```bash
# From local package
cd StockAI/yfinance-main/yfinance-main
pip install -e .

# Or from PyPI
pip install yfinance
```

This installs all dependencies automatically.

---

## Option 2: Install Dependencies Manually

If you want to use the local package without installing:

```bash
pip install pandas numpy requests curl_cffi
```

Then StockAI will use the local yfinance.

---

## Option 3: Use Without yfinance

StockAI can work with CSV files only:

```bash
# Save your data as CSV
# Format: Date,Open,High,Low,Close,Volume

python cli.py analyze AAPL GOOGL --csv
```

---

## Verify Installation

```bash
cd StockAI
python test_yfinance.py
```

Should output:
```
✓ yfinance imported successfully
✓ Successfully loaded AAPL data
```

---

## Quick Start

After installing yfinance:

```bash
# Analyze stocks
python cli.py analyze AAPL GOOGL MSFT --period 5y

# Get recommendations
python cli.py recommend AAPL GOOGL

# Show top performers
python cli.py top AAPL GOOGL MSFT NVDA
```

---

**That's it!** 📈
