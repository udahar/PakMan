"""StockAI Dashboard - Main Entry Point."""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage import get_config, PostgresRepository, VectorStore
from data import StockDataLoader
from analysis import StockAnalyzer

st.set_page_config(page_title="StockAI Dashboard", page_icon="📈", layout="wide")

st.title("📈 StockAI Dashboard")
st.markdown("AI-Powered Stock Analysis & Trading Signals")


# Initialize connections
@st.cache_resource
def get_postgres():
    """Get Postgres repository."""
    try:
        repo = PostgresRepository()
        if repo.connect():
            repo.ensure_tables()
            return repo
    except Exception as e:
        st.error(f"PostgreSQL connection failed: {e}")
    return None


@st.cache_resource
def get_vector_store():
    """Get Qdrant vector store."""
    try:
        store = VectorStore()
        if store.connect():
            return store
    except Exception as e:
        st.error(f"Qdrant connection failed: {e}")
    return None


@st.cache_data
def load_stock_data(symbols, period="2y"):
    """Load stock data."""
    try:
        loader = StockDataLoader()
        return loader.load_multiple(symbols, period=period)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return {}


# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to", ["Overview", "Winners", "Correlations", "Signals", "Settings"]
)

# Load data
pg_repo = get_postgres()
vec_store = get_vector_store()

if page == "Overview":
    st.header("Market Overview")

    # Get winners count
    winners_count = 0
    signals_count = 0
    stocks_tracked = 0

    if pg_repo:
        try:
            winners = pg_repo.get_winners(limit=100)
            winners_count = len(winners)
        except:
            pass

    # Count CSV files as "stocks tracked"
    data_dir = Path(__file__).parent.parent / "data"
    if data_dir.exists():
        stocks_tracked = len(list(data_dir.glob("*.csv")))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Winners", winners_count)
    with col2:
        st.metric("Signals Active", signals_count)
    with col3:
        st.metric("Market Health", "N/A")
    with col4:
        st.metric("Stocks Tracked", stocks_tracked)

    st.divider()

    st.subheader("Recent Stock Data")

    # Show some stock data
    data_dir = Path(__file__).parent.parent / "data"
    csv_files = list(data_dir.glob("*.csv"))[:10]

    if csv_files:
        stock_data = []
        for f in csv_files:
            symbol = f.stem.replace("_daily", "").replace("_monthly", "")
            try:
                df = pd.read_csv(f)
                if "Close" in df.columns and len(df) > 0:
                    latest = df.iloc[-1]
                    stock_data.append(
                        {
                            "Symbol": symbol,
                            "Price": f"${latest['Close']:.2f}",
                            "Volume": int(latest.get("Volume", 0))
                            if "Volume" in latest
                            else 0,
                        }
                    )
            except:
                pass

        if stock_data:
            st.dataframe(pd.DataFrame(stock_data), use_container_width=True)
    else:
        st.info("No stock data found. Use CLI to download data.")

elif page == "Winners":
    st.header("🏆 Your Winners")

    if not pg_repo:
        st.warning("PostgreSQL not connected. Winners will be shown from sample data.")
        winners = [
            {
                "symbol": "NVDA",
                "return_pct": 156.2,
                "sharpe_ratio": 2.34,
                "win_date": "2026-03-10",
            },
            {
                "symbol": "META",
                "return_pct": 89.5,
                "sharpe_ratio": 1.87,
                "win_date": "2026-03-08",
            },
            {
                "symbol": "AMZN",
                "return_pct": 67.3,
                "sharpe_ratio": 1.56,
                "win_date": "2026-03-05",
            },
        ]
    else:
        winners = pg_repo.get_winners(limit=20)
        if not winners:
            st.info("No winners yet. Add some from analysis!")

    if winners:
        df = pd.DataFrame(winners)
        st.dataframe(
            df,
            column_config={
                "symbol": "Symbol",
                "return_pct": st.column_config.NumberColumn(
                    "Return %", format="%.1f%%"
                ),
                "sharpe_ratio": "Sharpe Ratio",
                "win_date": "Date",
            },
            use_container_width=True,
        )
    else:
        st.info("No winners found. Run analysis to identify winners.")

    st.divider()

    st.subheader("Add Winner")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_symbol = st.text_input("Symbol").upper()
    with col2:
        new_return = st.number_input("Return %", value=0.0)
    with col3:
        new_sharpe = st.number_input("Sharpe Ratio", value=0.0)

    if st.button("Add to Winners"):
        if new_symbol and pg_repo:
            from datetime import datetime

            pg_repo.save_winner(new_symbol, datetime.now(), new_return, new_sharpe)
            st.success(f"Added {new_symbol}!")
            st.rerun()
        else:
            st.warning("PostgreSQL not connected or no symbol entered.")

elif page == "Correlations":
    st.header("🔗 Find Similar Stocks")

    st.markdown("""
    Find stocks **similar to your winners** based on:
    - Return profile, Volatility, Sharpe ratio, Valuation (P/E, PEG)
    """)

    st.divider()

    # Get available symbols from data or winners
    available_symbols = []

    if pg_repo:
        try:
            winners = pg_repo.get_winners(limit=50)
            available_symbols = [w["symbol"] for w in winners]
        except:
            pass

    # Add from CSV files
    data_dir = Path(__file__).parent.parent / "data"
    csv_symbols = [
        f.stem.replace("_daily", "").replace("_monthly", "")
        for f in data_dir.glob("*.csv")
    ]
    available_symbols = list(set(available_symbols + csv_symbols))

    if not available_symbols:
        available_symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Select Winners")

        selected_winners = st.multiselect(
            "Choose winners to find similar stocks:",
            sorted(available_symbols),
            default=["NVDA", "META", "AMZN"],
        )

        num_similar = st.slider("Similar stocks per winner", 3, 10, 5)

        find_similar = st.button("🔍 Find Similar Stocks", type="primary")

    with col2:
        if find_similar and selected_winners:
            st.subheader("Similar Stocks to Your Winners")

            # Try vector store first, then fallback to basic similarity
            if vec_store:
                try:
                    for winner in selected_winners:
                        similar = vec_store.find_similar(winner, limit=num_similar)
                        if similar:
                            st.markdown(f"**{winner}** → Similar to:")
                            for s in similar:
                                st.write(
                                    f"  • **{s['symbol']}** (score: {s.get('score', 0):.2f})"
                                )
                            st.divider()
                        else:
                            st.info(
                                f"No similar stocks found for {winner} (add to vector store first)"
                            )
                except Exception as e:
                    st.error(f"Vector search failed: {e}")
            else:
                st.warning("Qdrant not connected. Showing sample correlation data.")
                # Sample data for demo
                similar_data = {
                    "NVDA": [
                        {"symbol": "AMD", "score": 0.92},
                        {"symbol": "INTC", "score": 0.78},
                    ],
                    "META": [
                        {"symbol": "GOOGL", "score": 0.95},
                        {"symbol": "NFLX", "score": 0.82},
                    ],
                    "AMZN": [
                        {"symbol": "WMT", "score": 0.74},
                        {"symbol": "COST", "score": 0.68},
                    ],
                }

                for winner in selected_winners:
                    if winner in similar_data:
                        st.markdown(f"**{winner}** → Similar to:")
                        for s in similar_data[winner][:num_similar]:
                            st.write(f"  • **{s['symbol']}** (score: {s['score']:.2f})")
                        st.divider()
        else:
            st.info("Select winners and click 'Find Similar Stocks'")

    st.divider()

    st.subheader("💡 How it works")
    st.markdown("""
    1. **Add winners** from the Winners page or run analysis
    2. **Vector store** stores stock metrics (return, volatility, P/E, etc.)
    3. **Similarity search** finds stocks with closest metrics using vector distance
    4. Use PostgreSQL for persistence, Qdrant for fast vector search
    """)

elif page == "Signals":
    st.header("📊 Trading Signals")

    st.info("Run CLI analysis to generate trading signals.")

    # Check for analysis data
    if pg_repo:
        try:
            vectors = pg_repo.get_all_vectors()
            if vectors:
                st.subheader("Stock Vectors in Database")
                df = pd.DataFrame(vectors)
                st.dataframe(
                    df[
                        [
                            "symbol",
                            "sector",
                            "total_return",
                            "sharpe_ratio",
                            "volatility",
                        ]
                    ],
                    use_container_width=True,
                )
            else:
                st.info("No stock vectors yet. Run analysis to create them.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("PostgreSQL not connected")

elif page == "Settings":
    st.header("⚙️ Settings")

    cfg = get_config()

    st.subheader("Database Connection")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("PostgreSQL Host", value=cfg.db_host, disabled=True)
        st.text_input("Database Name", value=cfg.db_name, disabled=True)
    with col2:
        st.text_input("PostgreSQL Port", value=str(cfg.db_port), disabled=True)
        st.text_input("DB User", value=cfg.db_user, disabled=True)

    st.caption("Configure via environment variables or .env file")

    st.subheader("Qdrant Connection")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Qdrant Host", value=cfg.qdrant_host, disabled=True)
    with col2:
        st.text_input("Qdrant Port", value=str(cfg.qdrant_port), disabled=True)

    st.divider()

    st.subheader("Test Connections")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Test PostgreSQL"):
            if pg_repo:
                st.success("✓ PostgreSQL connected")
            else:
                st.error("✗ PostgreSQL not connected")

    with col2:
        if st.button("Test Qdrant"):
            if vec_store:
                st.success(f"✓ Qdrant connected ({vec_store.count()} vectors)")
            else:
                st.error("✗ Qdrant not connected")

    st.divider()

    st.subheader("Configuration File")
    st.markdown("""
    Create a `.env` file in the project root:
    
    ```bash
    cp .env.example .env
    # Edit .env with your actual values
    ```
    """)

    st.code(
        """
# .env example
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zolapress
DB_USER=postgres
DB_PASSWORD=your_password_here

QDRANT_HOST=localhost
QDRANT_PORT=6333

DATA_DIR=data
DEFAULT_PERIOD=10y
    """,
        language="bash",
    )
