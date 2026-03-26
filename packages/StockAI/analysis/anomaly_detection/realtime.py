import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from .models import TemporaryDive, WatchState

class RealTimeMonitor:
    """
    Real-time stock monitoring for temporary dives and anomalies.

    Polls price data periodically and detects:
    - Temporary dives: sudden drops with partial/full recovery
    - Flash crashes: extreme drops (>5% in minutes)
    - Volume spikes during price moves
    - Recovery signals: when a dive starts bouncing back

    Usage:
        monitor = RealTimeMonitor(
            poll_interval=30,      # check every 30 seconds
            dive_threshold=-2.0,   # -2% is a dive
            recovery_threshold=1.0 # +1% from low = recovering
        )

        # Add callback for alerts
        def on_dive(dive):
            print(f"ALERT: {dive.symbol} dropped {dive.drop_pct:.1f}%")

        monitor.watch('AAPL', alert_fn=on_dive)
        monitor.watch('NVDA', alert_fn=on_dive)

        # Start polling (blocking)
        monitor.start()

        # Or check once
        alerts = monitor.check_now()
    """

    def __init__(
        self,
        poll_interval: int = 30,
        dive_threshold: float = -2.0,
        flash_crash_threshold: float = -5.0,
        recovery_threshold: float = 1.0,
        lookback_minutes: int = 30,
        baseline_days: int = 20,
        alert_cooldown: float = 300,
    ):
        """
        Args:
            poll_interval: Seconds between price checks
            dive_threshold: % drop to consider a dive (negative)
            flash_crash_threshold: % drop for flash crash alert
            recovery_threshold: % bounce from low to signal recovery
            lookback_minutes: Minutes of history for dive detection
            baseline_days: Days of history for baseline volatility
            alert_cooldown: Min seconds between alerts per stock
        """
        self.poll_interval = poll_interval
        self.dive_threshold = dive_threshold
        self.flash_crash_threshold = flash_crash_threshold
        self.recovery_threshold = recovery_threshold
        self.lookback_minutes = lookback_minutes
        self.baseline_days = baseline_days
        self.alert_cooldown = alert_cooldown

        self._watched: Dict[str, WatchState] = {}
        self._alert_fns: Dict[str, callable] = {}
        self._running = False
        self._all_alerts: List[Dict] = []

    def watch(
        self, symbol: str, alert_fn: callable = None, dive_threshold: float = None
    ):
        """
        Add a stock to the watchlist.

        Args:
            symbol: Stock symbol
            alert_fn: Callback function(dive: TemporaryDive) called on dive
            dive_threshold: Override global dive threshold for this stock
        """
        state = WatchState(symbol=symbol)
        state.alert_cooldown = (
            self.alert_cooldown if dive_threshold is None else self.alert_cooldown
        )

        # Load baseline from historical data
        self._load_baseline(state)

        self._watched[symbol] = state
        if alert_fn:
            self._alert_fns[symbol] = alert_fn

    def _load_baseline(self, state: WatchState):
        """Load baseline price/volatility from recent history."""
        try:
            import sys
            from pathlib import Path

            yf_path = Path(__file__).parent.parent / "yfinance-main" / "yfinance-main"
            if yf_path.exists() and str(yf_path) not in sys.path:
                sys.path.insert(0, str(yf_path))
            import yfinance as yf

            ticker = yf.Ticker(state.symbol)
            hist = ticker.history(period=f"{self.baseline_days}d", interval="1d")

            if not hist.empty:
                state.baseline_price = hist["Close"].iloc[-1]
                returns = hist["Close"].pct_change().dropna()
                state.baseline_volatility = returns.std() * np.sqrt(252)
                state.baseline_volume = hist["Volume"].mean()

                # Seed price history with last known price
                import datetime

                state.price_history = [state.baseline_price]
                state.volume_history = [state.baseline_volume]
                state.time_history = [datetime.datetime.now()]

                print(
                    f"[Monitor] {state.symbol}: ${state.baseline_price:.2f}, "
                    f"vol={state.baseline_volatility:.1%}, "
                    f"avg_vol={state.baseline_volume:,.0f}"
                )
            else:
                print(
                    f"[Monitor] {state.symbol}: no historical data, will learn baseline live"
                )
        except Exception as e:
            print(
                f"[Monitor] {state.symbol}: baseline load failed ({e}), will learn live"
            )

    def check_now(self) -> List[Dict]:
        """
        Check all watched stocks RIGHT NOW (single poll).

        Returns list of alert dicts for any new detections.
        """
        alerts = []

        for symbol, state in self._watched.items():
            try:
                alert = self._check_stock(state)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                print(f"[Monitor] {symbol} check failed: {e}")

        return alerts

    def _check_stock(self, state: WatchState) -> Optional[Dict]:
        """Check a single stock for dives."""
        import datetime

        now = datetime.datetime.now()

        # Fetch current price
        price, volume = self._fetch_current_price(state.symbol)

        if price is None:
            return None

        # Initialize baseline if this is first data point
        if state.baseline_price == 0:
            state.baseline_price = price
            state.price_history = [price]
            state.volume_history = [volume or 0]
            state.time_history = [now]
            return None

        # Add to history
        state.price_history.append(price)
        state.volume_history.append(volume or 0)
        state.time_history.append(now)

        # Trim old history
        cutoff = now - datetime.timedelta(minutes=self.lookback_minutes * 3)
        while state.time_history and state.time_history[0] < cutoff:
            state.time_history.pop(0)
            state.price_history.pop(0)
            state.volume_history.pop(0)

        # Calculate change from baseline
        pct_change = (price / state.baseline_price - 1) * 100

        # Check if we're in an active dive
        if state.active_dive:
            return self._update_active_dive(state, price, volume, now, pct_change)

        # Check for new dive
        if pct_change <= self.dive_threshold:
            return self._start_new_dive(state, price, volume, now, pct_change)

        return None

    def _start_new_dive(
        self, state: WatchState, price: float, volume: float, now, pct_change: float
    ) -> Optional[Dict]:
        """A new dive has started."""
        # Check alert cooldown
        elapsed = (
            (now - state.last_alert_time).total_seconds()
            if hasattr(state.last_alert_time, "total_seconds")
            else 999
        )
        if elapsed < state.alert_cooldown:
            return None

        # Volume ratio
        avg_vol = state.baseline_volume if state.baseline_volume > 0 else 1
        vol_ratio = (volume / avg_vol) if volume else 1.0

        # Z-score of the drop
        if len(state.price_history) >= 5:
            recent_returns = (
                np.diff(state.price_history[-20:]) / state.price_history[-21:-1]
            )
            std = np.std(recent_returns) if len(recent_returns) > 1 else 0.01
            current_return = (
                (price - state.price_history[-2]) / state.price_history[-2]
                if state.price_history[-2] > 0
                else 0
            )
            z = current_return / std if std > 0 else 0
        else:
            z = pct_change / 2  # rough estimate

        # Classify severity
        if pct_change <= self.flash_crash_threshold:
            severity = "flash_crash"
            desc = f"FLASH CRASH: {state.symbol} down {pct_change:.1f}% in minutes"
        elif pct_change <= -3.0:
            severity = "critical_dive"
            desc = f"CRITICAL DIVE: {state.symbol} down {pct_change:.1f}%"
        else:
            severity = "temporary_dive"
            desc = f"TEMPORARY DIVE: {state.symbol} down {pct_change:.1f}%"

        dive = TemporaryDive(
            symbol=state.symbol,
            start_time=now,
            start_price=state.baseline_price,
            low_price=price,
            low_time=now,
            drop_pct=pct_change,
            duration_minutes=0,
            recovery_pct=0,
            is_recovering=False,
            is_complete=False,
            z_score=round(z, 3),
            volume_ratio=round(vol_ratio, 2),
            description=desc,
        )

        state.active_dive = dive
        state.last_alert_time = now

        # Fire alert
        alert = self._fire_alert(state, dive, severity)
        return alert

    def _update_active_dive(
        self, state: WatchState, price: float, volume: float, now, pct_change: float
    ) -> Optional[Dict]:
        """Update an active dive with new price data."""
        dive = state.active_dive

        # Update duration
        if hasattr(now, "total_seconds"):
            dive.duration_minutes = (now - dive.start_time).total_seconds() / 60

        # New low?
        if price < dive.low_price:
            dive.low_price = price
            dive.low_time = now
            dive.drop_pct = (price / dive.start_price - 1) * 100

        # Recovery check: how far from the low?
        recovery = (price / dive.low_price - 1) * 100
        dive.recovery_pct = recovery

        # Signal recovery?
        if recovery >= self.recovery_threshold and not dive.is_recovering:
            dive.is_recovering = True
            alert = self._fire_alert(state, dive, "recovering")
            return alert

        # Fully recovered?
        if recovery >= abs(dive.drop_pct) * 0.8:
            dive.is_complete = True
            dive.is_recovering = True
            state.completed_dives.append(dive)
            state.active_dive = None

            alert = self._fire_alert(state, dive, "recovered")
            return alert

        # Still diving deeper?
        if pct_change < dive.drop_pct - 1.0:
            alert = self._fire_alert(state, dive, "deepening")
            return alert

        return None

    def _fire_alert(
        self, state: WatchState, dive: TemporaryDive, alert_type: str
    ) -> Dict:
        """Fire an alert for a dive event."""
        dive.alerts_sent += 1

        alert = {
            "type": alert_type,
            "symbol": dive.symbol,
            "drop_pct": round(dive.drop_pct, 2),
            "recovery_pct": round(dive.recovery_pct, 2),
            "duration_min": round(dive.duration_minutes, 1),
            "current_price": dive.low_price,
            "volume_ratio": dive.volume_ratio,
            "description": dive.description,
            "is_recovering": dive.is_recovering,
            "is_complete": dive.is_complete,
        }

        self._all_alerts.append(alert)

        # Call user callback
        if dive.symbol in self._alert_fns:
            try:
                self._alert_fns[dive.symbol](dive)
            except Exception as e:
                print(f"[Monitor] Alert callback error: {e}")

        return alert

    def _fetch_current_price(
        self, symbol: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """Fetch current price for a symbol."""
        try:
            import sys
            from pathlib import Path

            yf_path = Path(__file__).parent.parent / "yfinance-main" / "yfinance-main"
            if yf_path.exists() and str(yf_path) not in sys.path:
                sys.path.insert(0, str(yf_path))
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.fast_info

            price = (
                info.get("lastPrice")
                or info.get("last_price")
                or info.get("regularMarketPrice")
            )
            volume = info.get("lastVolume") or info.get("regularMarketVolume")

            if price is None:
                # Fall back to recent history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                    volume = hist["Volume"].iloc[-1]

            return float(price) if price else None, float(volume) if volume else None
        except Exception as e:
            return None, None

    def start(self, max_checks: int = None):
        """
        Start polling loop. Blocks until stopped with Ctrl+C.

        Args:
            max_checks: Stop after N checks (None = run forever)
        """
        import time

        if not self._watched:
            print("[Monitor] No stocks watched. Call watch() first.")
            return

        symbols = ", ".join(self._watched.keys())
        print(f"[Monitor] Watching {symbols}")
        print(f"[Monitor] Poll interval: {self.poll_interval}s")
        print(f"[Monitor] Dive threshold: {self.dive_threshold}%")
        print(f"[Monitor] Flash crash threshold: {self.flash_crash_threshold}%")
        print(f"[Monitor] Press Ctrl+C to stop\n")

        self._running = True
        checks = 0

        try:
            while self._running:
                alerts = self.check_now()

                for alert in alerts:
                    self._print_alert(alert)

                checks += 1
                if max_checks and checks >= max_checks:
                    break

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[Monitor] Stopped.")

        self._running = False

    def stop(self):
        """Stop the polling loop."""
        self._running = False

    def _print_alert(self, alert: Dict):
        """Print a formatted alert."""
        import datetime

        ts = datetime.datetime.now().strftime("%H:%M:%S")

        icons = {
            "temporary_dive": "V",
            "critical_dive": "!!!",
            "flash_crash": "!!!CRASH!!!",
            "recovering": "^",
            "recovered": "OK",
            "deepening": "v",
        }
        icon = icons.get(alert["type"], "?")

        recov = (
            f" (recovery: +{alert['recovery_pct']:.1f}%)"
            if alert["is_recovering"]
            else ""
        )
        print(f"[{ts}] {icon} {alert['description']}{recov}")

    def get_active_dives(self) -> List[TemporaryDive]:
        """Get all currently active (unresolved) dives."""
        return [s.active_dive for s in self._watched.values() if s.active_dive]

    def get_completed_dives(self) -> Dict[str, List[TemporaryDive]]:
        """Get all completed dives per symbol."""
        return {s.symbol: s.completed_dives for s in self._watched.values()}

    def get_history(self, symbol: str) -> Optional[Dict]:
        """Get price history for a watched stock."""
        state = self._watched.get(symbol)
        if not state:
            return None
        return {
            "symbol": symbol,
            "prices": list(state.price_history),
            "volumes": list(state.volume_history),
            "times": [str(t) for t in state.time_history],
            "baseline_price": state.baseline_price,
            "active_dive": state.active_dive,
            "completed_dives": len(state.completed_dives),
        }

    def summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        return {
            "watched_symbols": list(self._watched.keys()),
            "active_dives": len(self.get_active_dives()),
            "total_alerts": len(self._all_alerts),
            "completed_dives": {
                s: len(st.completed_dives) for s, st in self._watched.items()
            },
        }


# Convenience function
def watch_for_dives(
    symbols: List[str], poll_interval: int = 30, dive_threshold: float = -2.0
):
    """
    Quick setup: watch stocks for temporary dives.

    Usage:
        monitor = watch_for_dives(['AAPL', 'NVDA', 'TSLA'])
        monitor.start()
    """
    monitor = RealTimeMonitor(
        poll_interval=poll_interval,
        dive_threshold=dive_threshold,
    )

    def alert_printer(dive):
        print(f"DIVE ALERT: {dive.symbol} dropped {dive.drop_pct:.1f}%")

    for symbol in symbols:
        monitor.watch(symbol, alert_fn=alert_printer)

    return monitor
