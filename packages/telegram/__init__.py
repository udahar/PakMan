"""telegram - Telegram Bot API: send messages and run a polling bot."""

__version__ = "0.2.0"

from .telegram_bot import TelegramBot, TelegramMessage, send_message, send_alert
from .bot_runner import BotRunner

__all__ = ["TelegramBot", "TelegramMessage", "send_message", "send_alert", "BotRunner"]