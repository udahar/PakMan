# RomAI

Token and vendor orchestrator for Alfred. Acts as the "thalamus" of the system — routing signals and managing resources before they hit the main inference layer.

## Features

- **OAuth & Secret Vault** — Centralized, encrypted store for vendor API keys and OAuth tokens
- **Spend Sentry** — Middleware that logs token counts and cost per vendor to Postgres
- **Hard Cap enforcement** — 90% threshold triggers throttle (inject "be concise" instructions); 99% kills vendor connection and reroutes to local model
- **429 Intelligence** — Detects rate limits, marks vendor as "Cooling Down", switches to secondary provider automatically
- **Cost Optimizer** — Nested module for model-cost routing decisions

## Install

```bash
pakman install RomAI
```

## Architecture

RomAI is intentionally separate from Guardian. Guardian watches system health (CPU, RAM, WSL stability). RomAI watches vendor/financial health. Neither is a God Object.

## Requirements

- PostgreSQL (for spend tracking)
- Alfred running as orchestration layer
