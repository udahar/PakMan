"""
TelegramBotRunner - Long-polling Telegram bot that forwards messages to a
NeuralCanvas-compatible REST API (or any /api/chat endpoint).

Zero external dependencies — pure Python stdlib only.

Usage:
    export TELEGRAM_BOT_TOKEN=<your token>
    export NEURAL_API_URL=http://localhost:8081   # default
    python -m telegram.bot_runner

    # Or from code:
    from telegram import BotRunner
    runner = BotRunner()
    runner.run()
"""

import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
DEFAULT_NEURAL_URL = "http://localhost:8081"

HELP_TEXT = """TouchAI Bot commands:
/start  - Welcome message
/help   - Show this help
/model <name>  - Switch Ollama model (e.g. /model llama3.2)
/chat <msg>    - Chat with AI
/clear         - Clear your conversation history

Just send any text to chat.
"""


class BotRunner:
    """
    Long-polling Telegram bot.

    Config via environment variables:
        TELEGRAM_BOT_TOKEN  (required)
        NEURAL_API_URL      (default: http://localhost:8081)
        TELEGRAM_ADMIN_IDS  (optional, comma-separated user IDs — if set, only these users can chat)
        BOT_MODEL           (default: llama3.2)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        neural_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")

        self.neural_url = (neural_url or os.environ.get("NEURAL_API_URL", DEFAULT_NEURAL_URL)).rstrip("/")
        self.default_model = model or os.environ.get("BOT_MODEL", "llama3.2")

        raw_admins = os.environ.get("TELEGRAM_ADMIN_IDS", "")
        self.admin_ids: set = set()
        if raw_admins.strip():
            for part in raw_admins.split(","):
                part = part.strip()
                if part.isdigit():
                    self.admin_ids.add(int(part))

        # Per-user state: {chat_id: {"history": [...], "model": str}}
        self._sessions: dict = {}
        self._offset: int = 0

    # ------------------------------------------------------------------ #
    #  Telegram helpers                                                    #
    # ------------------------------------------------------------------ #

    def _tg(self, method: str, params: Optional[dict] = None) -> dict:
        url = TELEGRAM_API.format(token=self.token, method=method)
        data = json.dumps(params).encode() if params else None
        req = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            return {"ok": False, "error": body}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _send(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
        self._tg("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        })

    def _send_typing(self, chat_id: int) -> None:
        self._tg("sendChatAction", {"chat_id": chat_id, "action": "typing"})

    def _get_updates(self) -> list:
        result = self._tg("getUpdates", {
            "offset": self._offset,
            "limit": 50,
            "timeout": 25,  # long-poll seconds
        })
        if not result.get("ok"):
            return []
        updates = result.get("result", [])
        if updates:
            self._offset = updates[-1]["update_id"] + 1
        return updates

    # ------------------------------------------------------------------ #
    #  NeuralCanvas API helpers                                            #
    # ------------------------------------------------------------------ #

    def _neural_chat(self, chat_id: int, message: str) -> str:
        session = self._sessions.setdefault(chat_id, {"history": [], "model": self.default_model})
        payload = {
            "message": message,
            "model": session["model"],
            "history": session["history"][-12:],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.neural_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
        except Exception as e:
            return f"API error: {e}"

        response = result.get("response", "")
        if result.get("error"):
            return f"Error: {result['error']}"

        # Append to history
        session["history"].append({"role": "user", "content": message})
        session["history"].append({"role": "assistant", "content": response})

        latency = result.get("latency_ms", 0)
        model = result.get("model", session["model"])
        cached = " _(cached)_" if result.get("cached") else ""
        return f"{response}\n\n_— {model} • {latency}ms{cached}_"

    def _neural_health(self) -> dict:
        try:
            with urllib.request.urlopen(f"{self.neural_url}/api/health", timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------ #
    #  Command handlers                                                    #
    # ------------------------------------------------------------------ #

    def _handle_start(self, chat_id: int, first_name: str) -> None:
        health = self._neural_health()
        api_status = "online" if not health.get("error") else f"offline ({health['error']})"
        self._send(chat_id, (
            f"*TouchAI Bot*\n\n"
            f"Hi {first_name}! I'm connected to your NeuralCanvas API.\n\n"
            f"API status: `{api_status}`\n"
            f"Model: `{self._sessions.get(chat_id, {}).get('model', self.default_model)}`\n\n"
            f"Just send me a message to start chatting, or use /help."
        ))

    def _handle_help(self, chat_id: int) -> None:
        self._send(chat_id, f"```\n{HELP_TEXT}\n```")

    def _handle_model(self, chat_id: int, args: str) -> None:
        model = args.strip()
        if not model:
            current = self._sessions.get(chat_id, {}).get("model", self.default_model)
            self._send(chat_id, f"Current model: `{current}`\nUsage: `/model llama3.2`")
            return
        session = self._sessions.setdefault(chat_id, {"history": [], "model": self.default_model})
        session["model"] = model
        self._send(chat_id, f"Model switched to `{model}`")

    def _handle_clear(self, chat_id: int) -> None:
        if chat_id in self._sessions:
            self._sessions[chat_id]["history"] = []
        self._send(chat_id, "Conversation history cleared.")

    # ------------------------------------------------------------------ #
    #  Message dispatcher                                                  #
    # ------------------------------------------------------------------ #

    def _is_authorized(self, user_id: int) -> bool:
        if not self.admin_ids:
            return True
        return user_id in self.admin_ids

    def _handle_message(self, msg: dict) -> None:
        chat_id = msg["chat"]["id"]
        user_id = msg.get("from", {}).get("id", 0)
        first_name = msg.get("from", {}).get("first_name", "there")
        text = msg.get("text", "").strip()

        if not text:
            return  # ignore non-text (stickers, files, etc.)

        if not self._is_authorized(user_id):
            self._send(chat_id, "Not authorised.")
            return

        if text.startswith("/start"):
            self._handle_start(chat_id, first_name)
        elif text.startswith("/help"):
            self._handle_help(chat_id)
        elif text.startswith("/model"):
            self._handle_model(chat_id, text[6:])
        elif text.startswith("/clear"):
            self._handle_clear(chat_id)
        elif text.startswith("/chat"):
            query = text[5:].strip()
            if not query:
                self._send(chat_id, "Usage: `/chat <your message>`")
                return
            self._send_typing(chat_id)
            reply = self._neural_chat(chat_id, query)
            self._send(chat_id, reply)
        else:
            # Plain text → chat
            self._send_typing(chat_id)
            reply = self._neural_chat(chat_id, text)
            self._send(chat_id, reply)

    # ------------------------------------------------------------------ #
    #  Main loop                                                           #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        me = self._tg("getMe")
        name = me.get("result", {}).get("username", "bot")
        print(f"[TouchAI Bot] @{name} started — polling Telegram")
        print(f"[TouchAI Bot] Neural API: {self.neural_url}")
        print(f"[TouchAI Bot] Default model: {self.default_model}")
        if self.admin_ids:
            print(f"[TouchAI Bot] Restricted to user IDs: {self.admin_ids}")

        while True:
            try:
                updates = self._get_updates()
                for update in updates:
                    if "message" in update:
                        try:
                            self._handle_message(update["message"])
                        except Exception as e:
                            print(f"[TouchAI Bot] Handler error: {e}")
            except KeyboardInterrupt:
                print("\n[TouchAI Bot] Stopped.")
                break
            except Exception as e:
                print(f"[TouchAI Bot] Poll error: {e} — retrying in 5s")
                time.sleep(5)


def main():
    runner = BotRunner()
    runner.run()


if __name__ == "__main__":
    main()
