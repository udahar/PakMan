#!/usr/bin/env python3
"""
Cost Optimizer - Token Budget Manager
Starter implementation
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


MODEL_COSTS = {
    # Ollama (free)
    "qwen2.5:7b": {"prompt": 0, "completion": 0},
    "qwen2.5:3b": {"prompt": 0, "completion": 0},
    "llama3.2:3b": {"prompt": 0, "completion": 0},
    "mistral:7b": {"prompt": 0, "completion": 0},
    # OpenAI (per 1M tokens)
    "gpt-4o": {"prompt": 5.0, "completion": 15.0},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.6},
    "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
    # Anthropic (per 1M tokens)
    "claude-3-opus": {"prompt": 15.0, "completion": 75.0},
    "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0},
}


@dataclass
class CostEntry:
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    task_type: str


@dataclass
class Budget:
    name: str
    amount: float
    spent: float = 0.0
    period: str = "monthly"  # daily, weekly, monthly


class CostTracker:
    def __init__(self, storage_file: str = "costs/tracking.jsonl"):
        self.storage_file = storage_file
        self.current_session_cost = 0.0

    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str = "general",
    ) -> float:
        """Track a request and return cost"""
        costs = MODEL_COSTS.get(model, {"prompt": 0, "completion": 0})

        cost = (
            prompt_tokens / 1_000_000 * costs["prompt"]
            + completion_tokens / 1_000_000 * costs["completion"]
        )

        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            task_type=task_type,
        )

        import os

        os.makedirs("costs", exist_ok=True)

        with open(self.storage_file, "a") as f:
            f.write(json.dumps(entry.__dict__) + "\n")

        self.current_session_cost += cost
        return cost

    def get_spending(self, period: str = "day") -> dict:
        """Get spending for a period"""
        try:
            with open(self.storage_file) as f:
                entries = [json.loads(line) for line in f]
        except FileNotFoundError:
            return {"total": 0, "by_model": {}, "by_task": {}}

        # Filter by period
        now = datetime.now()
        if period == "day":
            start = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
        else:
            start = now - timedelta(days=30)

        filtered = [
            e for e in entries if datetime.fromisoformat(e["timestamp"]) > start
        ]

        total = sum(e["cost"] for e in filtered)

        by_model = {}
        for e in filtered:
            by_model[e["model"]] = by_model.get(e["model"], 0) + e["cost"]

        by_task = {}
        for e in filtered:
            by_task[e["task_type"]] = by_task.get(e["task_type"], 0) + e["cost"]

        return {"total": total, "by_model": by_model, "by_task": by_task}


class BudgetManager:
    def __init__(self):
        self.budgets = {
            "global": Budget("global", 10.0),
            "session": Budget("session", 0.50),
            "coding": Budget("coding", 0.20),
            "creative": Budget("creative", 0.10),
        }

    def check_budget(self, budget_name: str, cost: float) -> bool:
        """Check if we have budget for this cost"""
        budget = self.budgets.get(budget_name)
        if not budget:
            return True
        return (budget.spent + cost) <= budget.amount

    def deduct(self, budget_name: str, cost: float):
        """Deduct from budget"""
        if budget_name in self.budgets:
            self.budgets[budget_name].spent += cost

    def reset_if_needed(self):
        """Reset budgets based on period"""
        # Simplified - would check actual time
        for budget in self.budgets.values():
            if budget.period == "session":
                budget.spent = 0.0


class CostRouter:
    """Select optimal model based on cost/quality tradeoff"""

    MODEL_QUALITY = {
        "general": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0},
            {"name": "gpt-4o-mini", "quality": 7, "cost": 0.00075},
            {"name": "gpt-4o", "quality": 9, "cost": 0.02},
        ],
        "coding": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0},
            {"name": "gpt-4o", "quality": 9, "cost": 0.02},
        ],
        "creative": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0},
            {"name": "claude-3-sonnet", "quality": 8, "cost": 0.018},
        ],
    }

    def select_model(
        self, task_type: str = "general", min_quality: int = 5, max_cost: float = None
    ) -> Optional[str]:
        """Select cheapest model meeting quality threshold"""
        candidates = self.MODEL_QUALITY.get(task_type, self.MODEL_QUALITY["general"])

        filtered = [c for c in candidates if c["quality"] >= min_quality]

        if max_cost:
            filtered = [c for c in filtered if c["cost"] <= max_cost]

        if not filtered:
            return candidates[0]["name"]  # Fallback

        filtered.sort(key=lambda x: x["cost"])
        return filtered[0]["name"]


# Dashboard (simplified)
def print_dashboard():
    tracker = CostTracker()

    day = tracker.get_spending("day")
    week = tracker.get_spending("week")
    month = tracker.get_spending("month")

    print("\n" + "=" * 40)
    print("COST OPTIMIZER DASHBOARD")
    print("=" * 40)
    print(f"Today:    ${day['total']:.4f}")
    print(f"This week: ${week['total']:.4f}")
    print(f"This month: ${month['total']:.4f}")
    print("\nBy Model:")
    for model, cost in month.get("by_model", {}).items():
        print(f"  {model}: ${cost:.4f}")


if __name__ == "__main__":
    router = CostRouter()

    # Test routing
    print("Model selection:")
    print(f"  General: {router.select_model('general')}")
    print(f"  Coding: {router.select_model('coding', max_cost=0.01)}")
    print(f"  Creative: {router.select_model('creative')}")

    # Show dashboard
    print_dashboard()
