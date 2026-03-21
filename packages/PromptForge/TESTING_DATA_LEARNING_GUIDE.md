<!-- Updated-On: 2026-03-07 -->
<!-- Updated-By: Codex -->
<!-- PM-Ticket: UNTRACKED -->

# PromptForge Testing, Data, and Production Guide

## What We Are Testing

PromptForge runs randomized experiments across multiple dimensions so repeated identical tests are rare by design:

- Model dimension: local/cloud/provider-specific models
- Task dimension: `coding`, `debugging`, `reasoning`, `planning`
- Prompt dimension: rotating prompt sets per task type
- Strategy dimension: reasoning-module combinations (for example `scratchpad`, `verify`, `planner`)

Primary goal:
- Discover model+strategy combinations that maximize quality per token across diverse tasks.

Secondary goal:
- Detect provider reliability behavior (timeouts, `429` rate limits, fallback frequency).

## How Data Is Collected

PromptForge stores structured run data in Postgres and experiment traces in Qdrant:

- Per-iteration outcome: model, task, strategy, score, success/failure
- Evolution history: strategy mutations and winner tracking
- Adversarial outcomes: side-by-side model competition results
- Provider resilience telemetry:
  - requested provider
  - fallback provider used (if any)
  - attempt trail per provider
  - `429` and breaker-open events

Persistence mode:
- Runtime is DB-first (`PROMPTOS_DB_ONLY=1`, `PROMPTFORGE_DB_ONLY=1`)
- JSON sidecars are not the active persistence path.

## What We Can Learn

From this dataset you can derive:

- Best strategy per model/task pair
- Transferable strategy patterns across model families/vendors
- Reliability-adjusted ranking (quality score weighted by failure/rate-limit behavior)
- Cost/latency/quality trade-offs by vendor lane
- When provider fallback improves throughput versus when it degrades quality

## How To Use This in Production

Use the learned data as a policy layer, not just a report:

1. Route by intent:
   - Pick model/provider from learned winners by task type.
2. Apply strategy presets:
   - Auto-attach proven strategy modules before inference.
3. Use vendor-lane resilience:
   - On `429`, open provider breaker for 300s and fail over by vendor chain.
4. Score outcomes continuously:
   - Keep online updates so routing adapts to drift.
5. Gate risky rollouts:
   - Require minimum sample count and confidence before promoting a new strategy/provider pair.

## Current Resilience Contract

- Circuit breaker scope: provider-level (`cerebras`, `ollama`, `openai`, `qwen-cli`)
- Open condition: HTTP/CLI rate-limit (`429`)
- Breaker duration: `300` seconds (default)
- Fallback order:
  - `cerebras -> ollama -> openai -> qwen-cli`
  - `ollama -> openai -> qwen-cli`
  - `openai -> ollama -> qwen-cli`
  - `qwen-cli -> ollama -> openai`

## Operational Notes

- If a vendor key/CLI is not configured, that provider is skipped in-chain.
- Timeout errors remain hard failures for scoring visibility.
- Non-timeout infrastructure/model-shape errors are skipped from scoring to avoid polluting model-quality metrics.
