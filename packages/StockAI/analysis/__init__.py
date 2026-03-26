"""StockAI Analysis Module - Core analysis and signal detection."""

from .analyzer import StockAnalyzer, StockMetrics
from .patterns import PatternRecognizer, Pattern, PatternType
from .scanner import MarketScanner, AlfredMarketScanner, MarketAnomaly, SectorRotation
from .regression import RegressionAnalyzer, RegressionResult, FactorAnalysis
from .anomaly_detection import (
    StockAnomalyDetector,
    StockAnomaly,
    AnomalyType,
    RealTimeMonitor,
    TemporaryDive,
)

__all__ = [
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
]
