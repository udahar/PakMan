"""
Telegram - Send messages via Telegram Bot API.

Usage:
    from telegram import TelegramBot, send_message
    
    bot = TelegramBot(token="YOUR_BOT_TOKEN")
    bot.send_message(chat_id="123456", text="Hello!")
    
    # Quick send
    send_message("123456", "Hello!", token="YOUR_BOT_TOKEN")
"""

import os
from typing import Optional, Dict, List
from dataclasses import dataclass
import json


TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


@dataclass
class TelegramMessage:
    chat_id: str
    text: str
    parse_mode: str = "Markdown"
    disable_web_page_preview: bool = False
    reply_to_message_id: Optional[int] = None


class TelegramBot:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            raise ValueError("Telegram bot token required")
    
    def _request(self, method: str, params: Optional[Dict] = None) -> Dict:
        import urllib.request
        import urllib.parse
        
        url = TELEGRAM_API_URL.format(token=self.token, method=method)
        data = json.dumps(params).encode() if params else None
        
        req = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = False
    ) -> Dict:
        return self._request("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        })
    
    def get_me(self) -> Dict:
        return self._request("getMe")
    
    def get_updates(self, limit: int = 100) -> Dict:
        return self._request("getUpdates", {"limit": limit})


def send_message(
    chat_id: str,
    text: str,
    token: Optional[str] = None,
    parse_mode: str = "Markdown"
) -> Dict:
    """Quick send message function."""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    bot = TelegramBot(token)
    return bot.send_message(chat_id, text, parse_mode)


def send_alert(
    message: str,
    chat_id: str,
    token: Optional[str] = None,
    severity: str = "info"
) -> Dict:
    """Send formatted alert message."""
    emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }.get(severity, "ℹ️")
    
    formatted = f"{emoji} *Alert*\n\n{message}"
    return send_message(chat_id, formatted, token)


__all__ = ["TelegramBot", "TelegramMessage", "send_message", "send_alert"]