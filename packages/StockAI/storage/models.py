"""Data models for StockAI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SignalType(Enum):
    """Types of trading signals."""

    VOLUME_SHOCK = "volume_shock"
    RELATIVE_STRENGTH = "relative_strength"
    VOLATILITY_CONTRACTION = "volatility_contraction"
    GOLDEN_CROSS = "golden_cross"
    BREAKOUT = "breakout"


@dataclass
class StockVector:
    """Vector representation of a stock for similarity search."""

    symbol: str
    sector: str
    total_return: float
    volatility: float
    sharpe_ratio: float
    beta: float
    pe_ratio: float
    peg_ratio: float
    revenue_growth: float
    institutional_ownership: float

    def to_embedding(self) -> List[float]:
        """Convert to embedding vector for similarity search."""
        return [
            self.total_return,
            self.volatility,
            self.sharpe_ratio,
            self.beta,
            self.pe_ratio / 100 if self.pe_ratio else 0,
            self.peg_ratio / 5 if self.peg_ratio else 0,
            self.revenue_growth,
            self.institutional_ownership,
        ]


@dataclass
class SimilarStock:
    """A stock similar to a given stock."""

    symbol: str
    similarity_score: float
    sector: str
    reason: str
