# PromptRouter (Experimental)
<!-- Updated-On: 2026-03-08 -->
<!-- Updated-By: Codex -->
<!-- PM-Ticket: UNTRACKED -->

Purpose: rank models for a prompt using Benchmark infosheet metrics.

## Inputs used
- `quality_score` (avg score)
- `reliability_score`
- `avg_latency_ms` / `p95_latency_ms`
- `avg_cost_per_task_usd` (or estimate)
- `clutch_score`
- `weakness_count`
- `determinism_score`
- `route_readiness`
- `format/transport/logic` failure rates
- `category_fit_vector`

## Scoring idea
`utility = weighted(quality, reliability, speed, cost, clutch) - weakness_penalty`

Task profile can tilt weights for:
- speed-sensitive routes
- cost-sensitive routes
- hard/reasoning routes

## Run
```powershell
cd C:\Users\Richard\clawd\Frank\PromptRD\PromptRouter
python .\cli.py --prompt "Design a safe migration plan for Postgres schema changes" --top-k 5
```

Optional:
```powershell
python .\cli.py --prompt "Quick short answer" --models "qwen3.5:2b,aya-expanse:8b,qwen3.5:397b-cloud"
```

Default Benchmark API base:
- `http://localhost:3001/api`

Override:
- `--api-base http://localhost:3001/api`

## API Service
```powershell
cd C:\Users\Richard\clawd\Frank\PromptRD\PromptRouter
python -m uvicorn service:app --host 127.0.0.1 --port 8777
```

Route:
```powershell
curl -X POST http://127.0.0.1:8777/route `
  -H "Content-Type: application/json" `
  -d '{"prompt":"debug a flaky python service","top_k":5}'
```
