"""
StockAI Alerts Module

Desktop notifications, email, and Telegram for stock alerts.
Cross-platform: Windows, macOS, Linux.

Usage:
    from StockAI.alerts import AlertManager, load_config, create_config

    # First time: create config file
    create_config()  # creates alerts_config.json

    # Load and use
    config = load_config()
    alerts = AlertManager(config)
    alerts.send("AAPL down 3%", "Temporary dive detected", "temporary_dive", "AAPL")

    # Wire to RealTimeMonitor
    from StockAI.analysis.anomaly_detection import RealTimeMonitor
    from StockAI.alerts import wire_alerts

    monitor = RealTimeMonitor()
    monitor.watch('AAPL')
    wire_alerts(monitor)  # auto-connects alerts
    monitor.start()
"""

from .notifier import (
    AlertManager,
    DesktopNotifier,
    EmailNotifier,
    TelegramNotifier,
    load_config,
    create_config,
)


def wire_alerts(monitor, config: dict = None) -> AlertManager:
    """
    Wire an AlertManager to a RealTimeMonitor.

    Automatically sends desktop/email/telegram alerts when dives are detected.

    Usage:
        from StockAI.analysis.anomaly_detection import RealTimeMonitor
        from StockAI.alerts import wire_alerts

        monitor = RealTimeMonitor()
        monitor.watch('AAPL')
        monitor.watch('NVDA')

        alerts = wire_alerts(monitor)
        monitor.start()  # alerts fire automatically
    """
    config = config or load_config()
    manager = AlertManager(config)

    # Wrap each watched stock's callback
    for symbol in list(monitor._watched.keys()):
        old_fn = monitor._alert_fns.get(symbol)

        def make_alert_fn(sym, prev_fn):
            def alert_fn(dive):
                # Send through alert channels
                manager.send_from_dive(dive)
                # Also call original callback if one existed
                if prev_fn:
                    prev_fn(dive)

            return alert_fn

        monitor._alert_fns[symbol] = make_alert_fn(symbol, old_fn)

    print(f"[Alerts] Wired to {len(monitor._watched)} stocks")
    print(
        f"[Alerts] Channels: desktop={manager.desktop is not None}, "
        f"email={manager.email is not None}, "
        f"telegram={manager.telegram is not None}"
    )

    return manager


__all__ = [
    "AlertManager",
    "DesktopNotifier",
    "EmailNotifier",
    "TelegramNotifier",
    "load_config",
    "create_config",
    "wire_alerts",
]
