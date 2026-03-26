"""
StockAI - AI-Powered Stock Analysis

Analyze historical stock data, identify patterns, and generate recommendations.
"""

__version__ = "0.2.0"

from .data import StockDataLoader, StockDataDownloader, StockDatabaseLoader
from .analysis import (
    StockAnalyzer,
    StockMetrics,
    PatternRecognizer,
    Pattern,
    PatternType,
    MarketScanner,
    AlfredMarketScanner,
    MarketAnomaly,
    SectorRotation,
    RegressionAnalyzer,
    RegressionResult,
    FactorAnalysis,
    StockAnomalyDetector,
    StockAnomaly,
    AnomalyType,
    RealTimeMonitor,
    TemporaryDive,
)
from .analysis.signals import (
    DayTradingAnalyzer,
    LongTermAnalyzer,
    InstitutionalSignals,
    MarketBreadthAnalyzer,
)
from .recommendations import StockRecommender
from .storage import (
    PostgresRepository,
    VectorStore,
    Config,
    config,
    get_config,
    reload_config,
    StockVector,
    SimilarStock,
    SignalType,
    get_similar_to_winners,
)

__all__ = [
    # Data
    "StockDataLoader",
    "StockDataDownloader",
    "StockDatabaseLoader",
    # Analysis
    "StockAnalyzer",
    "StockMetrics",
    "PatternRecognizer",
    "Pattern",
    "PatternType",
    "MarketScanner",
    "AlfredMarketScanner",
    "MarketAnomaly",
    "SectorRotation",
    "RegressionAnalyzer",
    "RegressionResult",
    "FactorAnalysis",
    "StockAnomalyDetector",
    "StockAnomaly",
    "AnomalyType",
    "RealTimeMonitor",
    "TemporaryDive",
    # Signals
    "DayTradingAnalyzer",
    "LongTermAnalyzer",
    "InstitutionalSignals",
    "MarketBreadthAnalyzer",
    # Recommendations
    "StockRecommender",
    # Storage
    "PostgresRepository",
    "VectorStore",
    "Config",
    "config",
    "get_config",
    "reload_config",
    "StockVector",
    "SimilarStock",
    "SignalType",
    "get_similar_to_winners",
]
