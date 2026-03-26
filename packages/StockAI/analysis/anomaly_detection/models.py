from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

class AnomalyType(Enum):
    PRICE_SPIKE = "price_spike"
    PRICE_CRASH = "price_crash"
    VOLUME_SURGE = "volume_surge"
    VOLUME_DRY_UP = "volume_dry_up"
    VOLATILITY_SPIKE = "volatility_spike"
    VOLATILITY_REGIME_CHANGE = "volatility_regime_change"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"
    TREND_BREAK = "trend_break"
    STRUCTURAL_BREAK = "structural_break"
    CORRELATION_BREAK = "correlation_break"


@dataclass
class StockAnomaly:
    """A detected anomaly in stock data."""

    type: str
    date: Any
    symbol: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    z_score: float
    description: str
    value: float
    expected_value: float
    details: Dict[str, Any] = field(default_factory=dict)


class TemporaryDive:
    """A detected temporary price dive."""

    symbol: str
    start_time: Any
    start_price: float
    low_price: float
    low_time: Any
    drop_pct: float
    duration_minutes: float
    recovery_pct: float  # how much it recovered from low
    is_recovering: bool  # currently bouncing back
    is_complete: bool  # fully recovered or still diving
    z_score: float
    volume_ratio: float  # volume during dive vs normal
    description: str
    alerts_sent: int = 0


@dataclass
class WatchState:
    """Internal state for a watched stock."""

    symbol: str
    baseline_price: float = 0.0
    baseline_volatility: float = 0.0
    baseline_volume: float = 0.0
    price_history: list = field(default_factory=list)
    volume_history: list = field(default_factory=list)
    time_history: list = field(default_factory=list)
    active_dive: Optional[TemporaryDive] = None
    completed_dives: list = field(default_factory=list)
    last_alert_time: float = 0.0
    alert_cooldown: float = 300.0  # 5 minutes between alerts

