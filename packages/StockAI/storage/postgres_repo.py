"""PostgreSQL Repository for StockAI."""

from datetime import datetime
from typing import List, Dict, Optional

from .config import config, get_config

try:
    from sqlalchemy import create_engine, text

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class PostgresRepository:
    """PostgreSQL repository for stock data and analysis results."""

    def __init__(self, db_url: str = None, cfg=None):
        self.cfg = cfg or get_config()
        self.db_url = db_url or self.cfg.db_url
        self.engine = None
        self.conn = None

    def connect(self) -> bool:
        """Connect to PostgreSQL."""
        if not HAS_SQLALCHEMY:
            print("✗ SQLAlchemy required")
            return False

        try:
            self.engine = create_engine(self.db_url)
            self.conn = self.engine.connect()
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()

    def ensure_tables(self):
        """Ensure required tables exist."""
        if not self.conn:
            return

        self.conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS stock_vectors (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) UNIQUE NOT NULL,
                sector VARCHAR(100),
                total_return FLOAT,
                volatility FLOAT,
                sharpe_ratio FLOAT,
                beta FLOAT,
                pe_ratio FLOAT,
                peg_ratio FLOAT,
                revenue_growth FLOAT,
                institutional_ownership FLOAT,
                embedding BLOB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        self.conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS winners (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                win_date DATE NOT NULL,
                return_pct FLOAT,
                sharpe_ratio FLOAT,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, win_date)
            )
        """)
        )

        self.conn.commit()

    def save_stock_vector(self, symbol: str, sector: str, metrics: Dict):
        """Save stock vector for similarity search."""
        if not self.conn:
            return

        embedding = self._create_embedding(metrics)

        self.conn.execute(
            text("""
            INSERT INTO stock_vectors (symbol, sector, total_return, volatility, sharpe_ratio, 
                beta, pe_ratio, peg_ratio, revenue_growth, institutional_ownership, embedding, updated_at)
            VALUES (:symbol, :sector, :total_return, :volatility, :sharpe_ratio,
                :beta, :pe_ratio, :peg_ratio, :revenue_growth, :inst_ownership, :embedding, NOW())
            ON CONFLICT (symbol) DO UPDATE SET
                sector = EXCLUDED.sector,
                total_return = EXCLUDED.total_return,
                volatility = EXCLUDED.volatility,
                sharpe_ratio = EXCLUDED.sharpe_ratio,
                beta = EXCLUDED.beta,
                pe_ratio = EXCLUDED.pe_ratio,
                peg_ratio = EXCLUDED.peg_ratio,
                revenue_growth = EXCLUDED.revenue_growth,
                institutional_ownership = EXCLUDED.institutional_ownership,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """),
            {
                "symbol": symbol,
                "sector": sector,
                "total_return": metrics.get("total_return", 0),
                "volatility": metrics.get("volatility", 0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "beta": metrics.get("beta", 1.0),
                "pe_ratio": metrics.get("pe_ratio", 0),
                "peg_ratio": metrics.get("peg_ratio", 0),
                "revenue_growth": metrics.get("revenue_growth", 0),
                "inst_ownership": metrics.get("institutional_ownership", 0),
                "embedding": str(embedding),
            },
        )

        self.conn.commit()

    def _create_embedding(self, metrics: Dict) -> List[float]:
        """Create embedding vector from metrics."""
        return [
            metrics.get("total_return", 0),
            metrics.get("volatility", 0),
            metrics.get("sharpe_ratio", 0),
            metrics.get("beta", 1.0),
            (metrics.get("pe_ratio", 0) or 0) / 100,
            (metrics.get("peg_ratio", 0) or 0) / 5,
            metrics.get("revenue_growth", 0),
            metrics.get("institutional_ownership", 0),
        ]

    def get_all_vectors(self) -> List[Dict]:
        """Get all stock vectors."""
        if not self.conn:
            return []

        result = self.conn.execute(text("SELECT * FROM stock_vectors"))
        return [dict(row._mapping) for row in result]

    def get_stock_vector(self, symbol: str) -> Optional[Dict]:
        """Get vector for a specific stock."""
        if not self.conn:
            return None

        result = self.conn.execute(
            text("SELECT * FROM stock_vectors WHERE symbol = :symbol"),
            {"symbol": symbol},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def save_winner(
        self,
        symbol: str,
        win_date: datetime,
        return_pct: float,
        sharpe_ratio: float,
        reasoning: str = "",
    ):
        """Save a winning stock."""
        if not self.conn:
            return

        self.conn.execute(
            text("""
            INSERT INTO winners (symbol, win_date, return_pct, sharpe_ratio, reasoning)
            VALUES (:symbol, :win_date, :return_pct, :sharpe_ratio, :reasoning)
            ON CONFLICT (symbol, win_date) DO UPDATE SET
                return_pct = EXCLUDED.return_pct,
                sharpe_ratio = EXCLUDED.sharpe_ratio,
                reasoning = EXCLUDED.reasoning
        """),
            {
                "symbol": symbol,
                "win_date": win_date.date() if hasattr(win_date, "date") else win_date,
                "return_pct": return_pct,
                "sharpe_ratio": sharpe_ratio,
                "reasoning": reasoning,
            },
        )

        self.conn.commit()

    def get_winners(self, limit: int = 20) -> List[Dict]:
        """Get top winning stocks."""
        if not self.conn:
            return []

        result = self.conn.execute(
            text("""
            SELECT * FROM winners 
            ORDER BY return_pct DESC, sharpe_ratio DESC 
            LIMIT :limit
        """),
            {"limit": limit},
        )

        return [dict(row._mapping) for row in result]

    def find_similar_stocks(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Find stocks similar to given symbol using PostgreSQL."""
        if not self.conn:
            return []

        target = self.get_stock_vector(symbol)
        if not target:
            return []

        result = self.conn.execute(
            text("""
            SELECT *, 
                (total_return - :target_return) * (total_return - :target_return) +
                (volatility - :target_vol) * (volatility - :target_vol) +
                (sharpe_ratio - :target_sharpe) * (sharpe_ratio - :target_sharpe) +
                (COALESCE(pe_ratio, 0) - :target_pe) * (COALESCE(pe_ratio, 0) - :target_pe) +
                (COALESCE(peg_ratio, 0) - :target_peg) * (COALESCE(peg_ratio, 0) - :target_peg) as distance
            FROM stock_vectors
            WHERE symbol != :symbol
            ORDER BY distance
            LIMIT :limit
        """),
            {
                "symbol": symbol,
                "target_return": target.get("total_return", 0),
                "target_vol": target.get("volatility", 0),
                "target_sharpe": target.get("sharpe_ratio", 0),
                "target_pe": target.get("pe_ratio", 0) or 0,
                "target_peg": target.get("peg_ratio", 0) or 0,
                "limit": limit,
            },
        )

        return [dict(row._mapping) for row in result]
