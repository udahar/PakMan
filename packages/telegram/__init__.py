"""telegram - Send messages via Telegram Bot API."""

__version__ = "0.1.0"

from .telegram_bot import TelegramBot, TelegramMessage, send_message, send_alert

__all__ = ["TelegramBot", "TelegramMessage", "send_message", "send_alert"]