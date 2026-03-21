# Benchmark Arena - Automated Model Comparison

## The Concept

Extends your existing benchmark system with **automated model selection** and **cost optimization**. Where your current benchmark tests "how well does model X perform," Arena adds:

1. **Auto-selection** - Given a task, which model is best?
2. **Cost tracking** - $/token for each model
3. **Tradeoff analysis** - Speed vs Quality vs Cost
4. **Leaderboard** - Continuous ranking of models

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark Arena                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Task Classifier                         │   │
│  │  "What kind of task is this?"                        │   │
│  │  - coding, reasoning, creative, analysis            │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│         ┌───────────────┴───────────────┐                  │
│         ▼                               ▼                   │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Benchmark      │        │  Cost Tracker    │         │
│  │  Runner         │        │                  │         │
│  │  (your existing│        │  - API calls     │         │
│  │   system)       │        │  - tokens used   │         │
│  │                 │        │  - latency       │         │
│  └──────────────────┘        └──────────────────┘         │
│         │                               │                    │
│         └───────────────┬───────────────┘                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Arena Decision Engine                   │   │
│  │                                                       │   │
│  │  "Given task T, budget B, quality Q:"               │   │
│  │  → Pick optimal model(s)                            │   │
│  │  → Run benchmark                                    │   │
│  │  → Return results + cost analysis                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Live Leaderboard                        │   │
│  │  Model | Score | Cost/hour | Best For               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Work / Integration Guide

### Step 1: Define Model Registry

```python
# models.py
MODELS = {
    "qwen2.5:7b": {"cost_per_1k": 0.0, "speed": "fast", "quality": 7},
    "qwen2.5:3b": {"cost_per_1k": 0.0, "speed": "faster", "quality": 5},
    "llama3.2:3b": {"cost_per_1k": 0.0, "speed": "medium", "quality": 6},
    "gpt-4o": {"cost_per_1k": 0.015, "speed": "medium", "quality": 9},
    # Add OpenAI, Anthropic, etc.
}
```

### Step 2: Extend Your Benchmark

Your existing benchmark_miner.py is the runner. Add:
```python
# arena.py
from training.benchmark_miner import run_benchmark

class Arena:
    def __init__(self):
        self.models = MODELS
        self.leaderboard = Leaderboard()
        
    def auto_select(self, task: str, budget: float = None):
        # Classify task
        task_type = classify(task)
        
        # Filter models by budget
        candidates = filter_by_budget(budget)
        
        # Rank by suitability for task_type
        ranked = rank(candidates, task_type)
        
        return ranked[:3]  # Top 3 choices
    
    def run_arena(self, task, models=None):
        # Auto-select if not specified
        if not models:
            models = self.auto_select(task)
            
        # Run all models on same task
        results = {}
        for model in models:
            result = run_benchmark(task, model)
            cost = track_cost(result)
            results[model] = {"result": result, "cost": cost}
            
        return results
```

### Step 3: Add Cost Tracking

```python
# cost_tracker.py
class CostTracker:
    def __init__(self):
        self.sessions = []
        
    def track(self, model: str, prompt_tokens: int, completion_tokens: int):
        cost = (prompt_tokens + completion_tokens) / 1000 * MODELS[model]["cost_per_1k"]
        self.sessions.append({"model": cost})
        
    def report(self):
        # Generate cost breakdown
        pass
```

### Step 4: Build the Dashboard

```bash
# Reuse your dashboard.py or create arena_dashboard.py
python arena_dashboard.py
```

## Quick Start

```bash
cd PromptRD/benchmark_arena
python arena_cli.py "Write a complex algorithm" --budget 0.10
python arena_cli.py "Quick summarization" --fast
```

## Files

- `arena.py` - Main arena logic
- `models.py` - Model registry with costs
- `task_classifier.py` - Classify incoming tasks
- `cost_tracker.py` - Track spending
- `leaderboard.py` - Maintain rankings
- `arena_dashboard.py` - Visual dashboard
- `cli.py` - Command-line interface

## Integration with Frank

Add to `frank.py`:
```python
if args.arena:
    from benchmark_arena import Arena
    arena = Arena()
    result = arena.run_arena(args.prompt, models=["qwen2.5:7b", "llama3.2:3b"])
    print(result)
```

Or use in tool selection:
```
The user asks: "Optimize this code"
Frank → Arena.auto_select() → "Use qwen2.5:7b for coding tasks"
```

## Extension Ideas

- Parallel model execution (run N models at once)
- Ensemble mode (combine outputs)
- A/B testing (compare two approaches)
- Historical analysis (how do models improve over time?)
- Custom benchmarks (add your own test suites)
