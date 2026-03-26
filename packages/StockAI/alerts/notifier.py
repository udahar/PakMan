"""
StockAI Alert System

Desktop notifications, email alerts, and Telegram messages.
Cross-platform: Windows, macOS, Linux.

Usage:
    from StockAI.alerts import AlertManager, load_config

    config = load_config()
    alerts = AlertManager(config)

    alerts.send(
        title="AAPL dropped 3%",
        body="Temporary dive detected. Price: $245.30",
        level="critical_dive",
        symbol="AAPL"
    )
"""

import os
import json
import platform
import subprocess
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

CONFIG_PATH = Path(__file__).parent / "alerts_config.json"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "default_config.json"


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load alert configuration.

    Looks for config in this order:
    1. Explicit path argument
    2. alerts_config.json in this directory
    3. STOCKAI_ALERTS_CONFIG env var
    4. default_config.json
    """
    paths_to_try = []

    if config_path:
        paths_to_try.append(Path(config_path))

    paths_to_try.extend(
        [
            CONFIG_PATH,
            Path(os.environ.get("STOCKAI_ALERTS_CONFIG", ""))
            if os.environ.get("STOCKAI_ALERTS_CONFIG")
            else None,
            DEFAULT_CONFIG_PATH,
        ]
    )

    for p in paths_to_try:
        if p and p.exists():
            with open(p, "r") as f:
                config = json.load(f)

            # Merge with defaults
            defaults = _load_defaults()
            merged = _deep_merge(defaults, config)
            return merged

    return _load_defaults()


def _load_defaults() -> Dict[str, Any]:
    """Load default config."""
    if DEFAULT_CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "desktop": {"enabled": True, "app_name": "StockAI"},
        "email": {"enabled": False},
        "telegram": {"enabled": False},
        "alert_levels": {
            "desktop": [
                "temporary_dive",
                "critical_dive",
                "flash_crash",
                "recovering",
                "recovered",
            ],
            "email": ["critical_dive", "flash_crash"],
            "telegram": ["critical_dive", "flash_crash"],
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def create_config(config_path: str = None):
    """
    Create a config file from defaults for editing.

    Usage:
        create_config()  # creates alerts_config.json
        # Then edit alerts_config.json with your email/telegram settings
    """
    path = Path(config_path) if config_path else CONFIG_PATH

    if path.exists():
        print(f"Config already exists: {path}")
        print("Edit it directly or delete it to regenerate.")
        return str(path)

    defaults = _load_defaults()
    with open(path, "w") as f:
        json.dump(defaults, f, indent=2)

    print(f"Created config: {path}")
    print("Edit it to add your email and Telegram credentials.")
    return str(path)


# ============================================================
# DESKTOP NOTIFIER (cross-platform)
# ============================================================


class DesktopNotifier:
    """
    Cross-platform desktop notifications.

    Works on Windows (toast), macOS (osascript), Linux (notify-send).
    No extra dependencies required.
    """

    def __init__(self, app_name: str = "StockAI"):
        self.app_name = app_name
        self.system = platform.system()

    def notify(self, title: str, body: str, urgency: str = "normal") -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title
            body: Notification body text
            urgency: 'low', 'normal', or 'critical'

        Returns:
            True if notification was sent successfully
        """
        try:
            if self.system == "Windows":
                return self._notify_windows(title, body, urgency)
            elif self.system == "Darwin":
                return self._notify_macos(title, body)
            elif self.system == "Linux":
                return self._notify_linux(title, body, urgency)
            else:
                print(f"[DesktopNotifier] Unsupported system: {self.system}")
                return False
        except Exception as e:
            print(f"[DesktopNotifier] Failed: {e}")
            return False

    def _notify_windows(self, title: str, body: str, urgency: str) -> bool:
        """Windows popup via PowerShell MessageBox (non-blocking)."""
        # Escape for PowerShell single-quoted string
        title_esc = title.replace("'", "''")
        body_esc = body.replace("'", "''")

        icon = "Warning" if urgency in ("normal", "critical") else "Information"

        # Launch non-blocking via Start-Process so monitor doesn't pause
        ps_script = (
            "Start-Process powershell -WindowStyle Hidden "
            "-ArgumentList '-NoProfile','-Command',"
            f"\"[System.Windows.Forms.MessageBox]::Show('{body_esc}','{title_esc}','OK','{icon}')\""
        )

        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_script],
            creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        return True

    def _notify_windows_fallback(self, title: str, body: str) -> bool:
        """Fallback: Balloon tip via PowerShell."""
        title_esc = title.replace("'", "''")
        body_esc = body.replace("'", "''")

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Warning
$balloon.BalloonTipTitle = '{title_esc}'
$balloon.BalloonTipText = '{body_esc}'
$balloon.BalloonTipIcon = 'Warning'
$balloon.Visible = $true
$balloon.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$balloon.Dispose()
"""

        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-Command",
                ps_script,
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW")
            else 0,
        )
        return True

    def _notify_macos(self, title: str, body: str) -> bool:
        """macOS notification via osascript."""
        title_esc = title.replace('"', '\\"')
        body_esc = body.replace('"', '\\"')

        script = f'display notification "{body_esc}" with title "{self.app_name}" subtitle "{title_esc}"'
        subprocess.run(["osascript", "-e", script], timeout=5)
        return True

    def _notify_linux(self, title: str, body: str, urgency: str) -> bool:
        """Linux notification via notify-send."""
        subprocess.run(
            [
                "notify-send",
                f"--urgency={urgency}",
                f"--app-name={self.app_name}",
                title,
                body,
            ],
            timeout=5,
        )
        return True


# ============================================================
# EMAIL NOTIFIER
# ============================================================


class EmailNotifier:
    """
    Send alerts via email (SMTP).

    Supports Gmail (with app passwords), Outlook, and custom SMTP servers.
    """

    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.use_tls = config.get("use_tls", True)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.from_addr = config.get("from_addr", self.username)
        self.to_addrs = config.get("to_addrs", [])

    def send(
        self, title: str, body: str, level: str = "normal", symbol: str = ""
    ) -> bool:
        """
        Send an email alert.

        Args:
            title: Email subject
            body: Email body (plain text or HTML)
            level: Alert level for priority
            symbol: Stock symbol (added to subject)

        Returns:
            True if sent successfully
        """
        if not self.username or not self.password:
            print("[EmailNotifier] No credentials configured")
            return False

        if not self.to_addrs:
            print("[EmailNotifier] No recipients configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[StockAI] {title}"
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            # Priority headers for critical alerts
            if level in ("critical_dive", "flash_crash"):
                msg["X-Priority"] = "1"
                msg["X-MSMail-Priority"] = "High"
                msg["Importance"] = "High"

            # Plain text version
            plain_text = f"""StockAI Alert
{"=" * 40}

{title}

{body}

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Level: {level}
Symbol: {symbol or "N/A"}

---
StockAI Monitoring System
"""
            msg.attach(MIMEText(plain_text, "plain"))

            # HTML version
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
  <div style="background: {"#ff4444" if "crash" in level else "#ff8800" if "dive" in level else "#4488ff"}; color: white; padding: 15px; border-radius: 5px;">
    <h2 style="margin: 0;">{title}</h2>
  </div>
  <div style="padding: 15px;">
    <p>{body.replace(chr(10), "<br>")}</p>
    <hr>
    <table style="font-size: 12px; color: #666;">
      <tr><td><b>Time:</b></td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
      <tr><td><b>Level:</b></td><td>{level}</td></tr>
      <tr><td><b>Symbol:</b></td><td>{symbol or "N/A"}</td></tr>
    </table>
  </div>
</body>
</html>
"""
            msg.attach(MIMEText(html_body, "html"))

            # Send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(self.username, self.password)
            server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            server.quit()

            print(f"[EmailNotifier] Sent to {', '.join(self.to_addrs)}")
            return True

        except Exception as e:
            print(f"[EmailNotifier] Failed: {e}")
            return False


# ============================================================
# TELEGRAM NOTIFIER
# ============================================================


class TelegramNotifier:
    """
    Send alerts via Telegram Bot API.

    Setup:
    1. Message @BotFather on Telegram to create a bot
    2. Copy the bot token
    3. Message your bot, then get your chat_id from:
       https://api.telegram.org/bot<TOKEN>/getUpdates
    """

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(
        self, title: str, body: str, level: str = "normal", symbol: str = ""
    ) -> bool:
        """
        Send a Telegram message.

        Args:
            title: Message header
            body: Message body
            level: Alert level (affects emoji)
            symbol: Stock symbol

        Returns:
            True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            print("[TelegramNotifier] No credentials configured")
            return False

        # Emoji based on level
        emoji = {
            "flash_crash": "🔴",
            "critical_dive": "🟠",
            "temporary_dive": "🟡",
            "recovering": "🟢",
            "recovered": "✅",
            "normal": "📊",
        }.get(level, "📊")

        # Format message
        text = f"""{emoji} *{title}*

{body}

_Time: {datetime.now().strftime("%H:%M:%S")}_
_Level: {level}_"""

        if symbol:
            text += f"\n_Symbol: {symbol}_"

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            encoded = urllib.parse.urlencode(data).encode("utf-8")
            req = urllib.request.Request(url, data=encoded, method="POST")

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())

            if result.get("ok"):
                print(f"[TelegramNotifier] Sent to chat {self.chat_id}")
                return True
            else:
                print(f"[TelegramNotifier] API error: {result}")
                return False

        except Exception as e:
            print(f"[TelegramNotifier] Failed: {e}")
            return False


# ============================================================
# ALERT MANAGER
# ============================================================


class AlertManager:
    """
    Dispatch alerts to all configured channels.

    Routes alerts based on level and channel configuration.

    Usage:
        config = load_config()
        manager = AlertManager(config)

        manager.send(
            title="AAPL dropped 3.2%",
            body="Temporary dive detected at $245.30. Volume 2.5x normal.",
            level="temporary_dive",
            symbol="AAPL"
        )
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()

        # Initialize notifiers
        self.desktop = None
        if self.config.get("desktop", {}).get("enabled", True):
            app_name = self.config.get("desktop", {}).get("app_name", "StockAI")
            self.desktop = DesktopNotifier(app_name)

        self.email = None
        if self.config.get("email", {}).get("enabled", False):
            self.email = EmailNotifier(self.config["email"])

        self.telegram = None
        if self.config.get("telegram", {}).get("enabled", False):
            self.telegram = TelegramNotifier(
                bot_token=self.config["telegram"].get("bot_token", ""),
                chat_id=self.config["telegram"].get("chat_id", ""),
            )

        # Alert level routing
        self.alert_levels = self.config.get(
            "alert_levels",
            {
                "desktop": [
                    "temporary_dive",
                    "critical_dive",
                    "flash_crash",
                    "recovering",
                    "recovered",
                ],
                "email": ["critical_dive", "flash_crash"],
                "telegram": ["critical_dive", "flash_crash"],
            },
        )

        self._sent_count = 0

    def send(
        self, title: str, body: str, level: str = "normal", symbol: str = ""
    ) -> Dict[str, bool]:
        """
        Send alert to all configured channels that accept this level.

        Returns:
            Dict of channel -> success
        """
        results = {}

        # Desktop
        if self.desktop and level in self.alert_levels.get("desktop", []):
            results["desktop"] = self.desktop.notify(title, body)

        # Email
        if self.email and level in self.alert_levels.get("email", []):
            results["email"] = self.email.send(title, body, level, symbol)

        # Telegram
        if self.telegram and level in self.alert_levels.get("telegram", []):
            results["telegram"] = self.telegram.send(title, body, level, symbol)

        self._sent_count += 1
        return results

    def send_from_dive(self, dive) -> Dict[str, bool]:
        """
        Send alert from a TemporaryDive object.

        Auto-formats the title and body from dive data.
        """
        # Determine alert type from dive state
        if hasattr(dive, "is_recovering") and dive.is_recovering:
            if hasattr(dive, "is_complete") and dive.is_complete:
                level = "recovered"
                title = f"{dive.symbol} RECOVERED"
                body = (
                    f"Price recovered from {dive.drop_pct:.1f}% drop.\n"
                    f"Recovery: +{dive.recovery_pct:.1f}% from low.\n"
                    f"Duration: {dive.duration_minutes:.0f} minutes."
                )
            else:
                level = "recovering"
                title = f"{dive.symbol} recovering (+{dive.recovery_pct:.1f}%)"
                body = (
                    f"Price bouncing back from {dive.drop_pct:.1f}% drop.\n"
                    f"Current recovery: +{dive.recovery_pct:.1f}% from low."
                )
        else:
            if dive.drop_pct <= -5:
                level = "flash_crash"
                title = f"🔴 {dive.symbol} FLASH CRASH {dive.drop_pct:.1f}%"
            elif dive.drop_pct <= -3:
                level = "critical_dive"
                title = f"🟠 {dive.symbol} CRITICAL DIVE {dive.drop_pct:.1f}%"
            else:
                level = "temporary_dive"
                title = f"🟡 {dive.symbol} DIVE {dive.drop_pct:.1f}%"

            body = (
                f"Price dropped {dive.drop_pct:.1f}% from ${dive.start_price:.2f}\n"
                f"Low: ${dive.low_price:.2f}\n"
                f"Volume: {dive.volume_ratio:.1f}x normal\n"
                f"Z-score: {dive.z_score}"
            )

        return self.send(title, body, level, dive.symbol)

    def send_from_anomaly(self, anomaly) -> Dict[str, bool]:
        """
        Send alert from a StockAnomaly object.
        """
        level = anomaly.severity if hasattr(anomaly, "severity") else "normal"
        symbol = anomaly.symbol if hasattr(anomaly, "symbol") else ""
        desc = anomaly.description if hasattr(anomaly, "description") else str(anomaly)

        title = f"{symbol}: {anomaly.type}" if symbol else str(anomaly.type)
        body = desc

        return self.send(title, body, level, symbol)

    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return {
            "total_sent": self._sent_count,
            "channels": {
                "desktop": self.desktop is not None,
                "email": self.email is not None,
                "telegram": self.telegram is not None,
            },
        }
