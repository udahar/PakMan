# Cost Optimizer - Token Budget Manager

## The Concept

Track and optimize spending across all AI model calls. Features:
- Per-session budgets
- Per-task type budgets
- Auto-routing to cheapest model that meets quality threshold
- Real-time cost dashboards
- Alerts when approaching limits

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cost Optimizer                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Budget Manager                          │   │
│  │                                                      │   │
│  │  Global Budget: $10/month                           │   │
│  │  Session Budget: $0.50                              │   │
│  │  Task Budgets:                                      │   │
│  │    - coding: $0.20                                  │   │
│  │    - summarization: $0.05                          │   │
│  │    - creative: $0.10                                │   │
│  │                                                      │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Cost Tracker                            │   │
│  │                                                      │   │
│  │  Per-request accounting:                            │   │
│  │    model: qwen2.5:7b                                │   │
│  │    prompt_tokens: 150                               │   │
│  │    completion_tokens: 45                            │   │
│  │    cost: $0.000195                                  │   │
│  │                                                      │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│         ┌───────────────┴───────────────┐                  │
│         ▼                               ▼                   │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Router          │        │  Dashboard        │         │
│  │                  │        │                  │         │
│  │  "Task: code"    │        │  - Daily spend   │         │
│  │  "Quality: 7+"   │        │  - By model      │         │
│  │  → qwen2.5:3b ✓  │        │  - By task type   │         │
│  └──────────────────┘        └──────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Work / Integration Guide

### Step 1: Define Cost Model

```python
# cost_model.py
COSTS = {
    # Ollama models (free)
    "qwen2.5:7b": {"prompt": 0, "completion": 0, "speed": 1.0},
    "qwen2.5:3b": {"prompt": 0, "completion": 0, "speed": 1.5},
    "llama3.2:3b": {"prompt": 0, "completion": 0, "speed": 1.2},
    "mistral:7b": {"prompt": 0, "completion": 0, "speed": 1.1},
    
    # OpenAI (per 1M tokens)
    "gpt-4o": {"prompt": 5.0, "completion": 15.0, "speed": 0.8},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.6, "speed": 2.0},
    "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0, "speed": 0.7},
    
    # Anthropic
    "claude-3-opus": {"prompt": 15.0, "completion": 75.0, "speed": 0.6},
    "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0, "speed": 1.0},
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    cost_per_1m = COSTS.get(model, {"prompt": 0, "completion": 0})
    return (prompt_tokens / 1_000_000 * cost_per_1m["prompt"] +
            completion_tokens / 1_000_000 * cost_per_1m["completion"])
```

### Step 2: Create Tracker

```python
# tracker.py
from datetime import datetime
import json

class CostTracker:
    def __init__(self, budget_file="costs/budgets.json"):
        self.budget_file = budget_file
        self.spending = []
        self.budgets = self.load_budgets()
        
    def track(self, model: str, prompt_tokens: int, completion_tokens: int, task_type: str = "general"):
        cost = calculate_cost(model, prompt_tokens, completion_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "task_type": task_type
        }
        
        self.spending.append(entry)
        self.update_budgets(cost, task_type)
        
        # Check alerts
        self.check_alerts()
        
        return cost
        
    def get_spending(self, period="day") -> dict:
        # Aggregate spending
        pass
        
    def check_alerts(self):
        for budget in self.budgets:
            spent = self.get_spent(budget["type"])
            if spent > budget["amount"] * 0.9:
                print(f"⚠️  Alert: {budget['type']} at {spent/budget['amount']*100:.1f}%")
```

### Step 3: Create Router

```python
# router.py
class CostRouter:
    def __init__(self, tracker: CostTracker):
        self.tracker = tracker
        
    def select_model(self, task_type: str, min_quality: int = 5, max_budget: float = None) -> str:
        """Select cheapest model that meets quality threshold"""
        
        # Get available models for this task
        candidates = MODEL_QUALITY.get(task_type, MODEL_QUALITY["general"])
        
        # Filter by quality
        candidates = [m for m in candidates if m["quality"] >= min_quality]
        
        # Sort by cost
        candidates.sort(key=lambda m: m["cost"])
        
        # Check budget
        if max_budget:
            for model in candidates:
                if model["cost"] <= max_budget:
                    return model["name"]
            return None  # No model fits budget
            
        return candidates[0]["name"]
```

### Step 4: Build Dashboard

```bash
# dashboard.py
import streamlit as st

st.title("💰 Cost Optimizer")

# Show current spending
col1, col2, col3 = st.columns(3)
col1.metric("Today", "$0.45")
col2.metric("This Week", "$2.30")
col3.metric("This Month", "$8.50")

# Show by model
st.bar_chart(spending_by_model)
```

## Quick Start

```bash
cd PromptRD/cost_optimizer
python dashboard.py
# Opens http://localhost:8501
```

## Files

- `cost_model.py` - Pricing data
- `tracker.py` - Spending tracking
- `router.py` - Model selection
- `budgets.py` - Budget management
- `dashboard.py` - Visual dashboard
- `cli.py` - CLI tools

## Integration with Frank

```python
# In frank.py
from cost_optimizer import CostTracker, CostRouter

tracker = CostTracker()
router = CostRouter(tracker)

# When making LLM call:
def call_llm(prompt, task_type="general"):
    model = router.select_model(task_type, max_budget=session_budget)
    
    response = llm.invoke(prompt, model=model)
    
    tracker.track(
        model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        task_type=task_type
    )
    
    return response
```

## Extension Ideas

- Budget alerts (Slack, email)
- Auto-pause when budget exceeded
- Historical trends
- Model performance vs cost charts
- Anomaly detection (unusual spending)
- Refund tracking (for API errors)
