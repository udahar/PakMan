# AutoDistiller
> **Status:** 🔬 IN PROGRESS

## What It Is
Mines high-quality AI executions from expensive models (GPT-4o, Claude 3.5) and auto-formats them into JSONL fine-tuning datasets to train cheaper, local models (Llama-3, Qwen).

## Why It Matters
You're already generating high-quality AI completions through PromptForge. AutoDistiller captures the best ones for free, saving thousands in API costs by teaching local models to replicate the behavior.

## How It Works

```
PromptForge session produces:
 score=0.92 ★★★★★ | model=gpt-4o | task=coding
         │
         ▼
  AutoDistiller scans history
         │
  quality_filter(score ≥ 0.8) → ✅ keep
         │
  format_to_jsonl({
    "instruction": "<original prompt>",
    "output": "<gpt-4o response>",
    "task_type": "coding"
  })
         │
         ▼
  auto_dedup() → writes to dataset.jsonl
         │
         ▼
  Triggers: ollama create my-model -f Modelfile
```

### Output Formats Supported
- `ChatML` (Mistral, LLaMA-3)
- `Alpaca` (generic instruction fine-tuning)
- `ShareGPT` (multi-turn)
- `Ollama Modelfile` (Ollama-native)

## Integration Points
- `PromptForge` → primary data source (scored experiment history)
- `PromptOS` → genome records tagged as "elite" trigger auto-distill

## Roadmap
- [ ] Build quality-score filter (threshold from env var)
- [ ] Add deduplication by semantic similarity
- [ ] Support ChatML, Alpaca, ShareGPT output formats
- [ ] Auto-trigger Ollama `create` command on dataset completion
