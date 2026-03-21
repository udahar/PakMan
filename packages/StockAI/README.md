# StockAI

AI-powered stock analysis package. Loads historical price data, identifies patterns, and generates investment recommendations using local LLM inference.

## Install

```bash
pakman install StockAI
```

## Features

- **Data loading** — yfinance integration, local DB caching (`StockDataLoader`, `StockDatabaseLoader`)
- **Analysis** — Pattern recognition, technical metrics (`StockAnalyzer`, `PatternRecognizer`)
- **Recommendations** — LLM-assisted recommendation generation
- **Dashboard** — Terminal and web dashboard views
- **CLI** — Command-line interface for quick queries

## Usage

```python
from StockAI import StockDataLoader, StockAnalyzer

loader = StockDataLoader()
data = loader.load("AAPL", period="1y")

analyzer = StockAnalyzer()
report = analyzer.analyze(data)
print(report.summary)
```

## Requirements

- Python 3.8+
- yfinance
- See `requirements.txt` for full list
