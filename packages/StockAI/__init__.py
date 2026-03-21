"""
StockAI - AI-Powered Stock Analysis

Analyze historical stock data, identify patterns, and generate recommendations.
"""

__version__ = "0.2.0"

from .data import StockDataLoader, StockDataDownloader, StockDatabaseLoader
from .analysis import StockAnalyzer, StockMetrics, PatternRecognizer
from .analysis.signals import (
    DayTradingAnalyzer,
    LongTermAnalyzer,
    InstitutionalSignals,
    MarketBreadthAnalyzer,
)
from .recommendations import StockRecommender
from .storage import PostgresRepository, VectorStore, config, get_config

__all__ = [
    "StockDataLoader",
    "StockDataDownloader",
    "StockDatabaseLoader",
    "StockAnalyzer",
    "StockMetrics",
    "PatternRecognizer",
    "DayTradingAnalyzer",
    "LongTermAnalyzer",
    "InstitutionalSignals",
    "MarketBreadthAnalyzer",
    "StockRecommender",
    "PostgresRepository",
    "VectorStore",
    "config",
    "get_config",
]
