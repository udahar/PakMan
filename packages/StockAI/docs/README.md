# StockAI - AI-Powered Stock Analysis

Analyze stocks, identify patterns, generate recommendations, and find similar stocks using vector similarity.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
pip install streamlit plotly pandas numpy sqlalchemy psycopg2-binary qdrant-client

# Run dashboard
streamlit run dashboard/app.py

# Or use CLI
python -m cli.cli analyze AAPL GOOGL NVDA
```

## Structure

```
StockAI/
├── cli/              # Command-line interface
│   └── cli.py
├── data/             # Data loading & storage
│   ├── loader.py     # StockDataLoader
│   ├── downloader.py
│   └── db_loader.py # PostgreSQL loader
├── analysis/         # Analysis engines
│   ├── analyzer.py  # Core StockAnalyzer
│   ├── patterns.py  # Pattern recognition
│   ├── signals/     # Trading signals
│   │   ├── day_trading.py
│   │   ├── long_term.py
│   │   ├── institutional.py
│   │   └── breadth.py
│   └── scanner/
│       └── market_scanner.py
├── recommendations/  # AI recommender
│   └── recommender.py
├── storage/         # PostgreSQL + Qdrant
│   ├── postgres_repo.py
│   └── vector_store.py
├── dashboard/       # Streamlit dashboard
│   └── app.py
├── docs/            # Documentation
├── data/            # CSV data files
└── yfinance-main/   # Bundled yfinance
```

## Features

- **Data Loading**: CSV, Yahoo Finance, PostgreSQL
- **Technical Analysis**: RSI, MACD, Bollinger Bands, moving averages
- **Pattern Recognition**: Candlesticks, breakouts, crossovers
- **Trading Signals**: Day trading, long-term, institutional, market breadth
- **Similarity Search**: Find stocks "close to winners" via Qdrant vectors
- **Dashboard**: Streamlit UI with correlation graphs

## Configuration

Set environment variables:
- `STOCKAI_DB_URL`: PostgreSQL connection (default: postgresql://postgres:zolapress2025@localhost:5432/zolapress)
- Qdrant runs at localhost:6333

## Requirements

See `requirements.txt`
