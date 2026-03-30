# telegram

> **Status:** STABLE | **Tags:** utility, telegram, bot

## Overview

Pure-Python Telegram integration with two modes:
- **Send-only** (`TelegramBot`) — send messages and alerts from any script
- **Bot runner** (`BotRunner`) — long-polling bot that forwards chats to a NeuralCanvas REST API

Zero external dependencies — stdlib only.

## Installation

```bash
pakman install telegram
```

## Bot Runner (TouchAI)

Set environment variables and run:

```bash
export TELEGRAM_BOT_TOKEN=<your token>
export NEURAL_API_URL=http://localhost:8081   # default
export BOT_MODEL=llama3.2                     # default
export TELEGRAM_ADMIN_IDS=123456,789012       # optional, restrict access

python -m telegram.bot_runner
```

### Bot commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome + API status |
| `/help` | Show command list |
| `/model <name>` | Switch Ollama model |
| `/chat <msg>` | Explicit chat |
| `/clear` | Clear conversation history |
| _(any text)_ | Chat with AI |

## Send-Only Usage

```python
from telegram import send_message, send_alert, TelegramBot

# Quick send
send_message("CHAT_ID", "Hello!", token="TOKEN")

# Alerts
send_alert("Deploy succeeded", chat_id="CHAT_ID", severity="success")

# Full bot object
bot = TelegramBot(token="TOKEN")
bot.send_message("CHAT_ID", "*Bold* message")
```

## Architecture

- Standalone — no cross-package dependencies
- Secrets via environment variables only, never hard-coded
- `BotRunner` connects to any HTTP API with `/api/chat` and `/api/health` endpoints
