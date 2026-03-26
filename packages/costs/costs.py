"""
Costs - Cost tracking and management for AI operations.

Usage:
    from costs import CostTracker, BudgetManager
    
    tracker = CostTracker()
    tracker.track_cost("gpt-4", tokens=1000, cost=0.03)
    
    budget = BudgetManager(monthly_limit=100.0)
    budget.check_budget()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


MODEL_COSTS = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
    "llama3.2": {"prompt": 0.0, "completion": 0.0},
    "qwen2.5": {"prompt": 0.0, "completion": 0.0},
}


@dataclass
class CostEntry:
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    metadata: Dict = field(default_factory=dict)


class CostTracker:
    def __init__(self, storage_path: str = "~/.pakman/costs.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.entries: List[CostEntry] = []
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.entries = [CostEntry(**e) for e in data.get("entries", [])]
            except Exception:
                pass
    
    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [vars(e) for e in self.entries]}
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def track_cost(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        metadata: Optional[Dict] = None
    ) -> float:
        costs = MODEL_COSTS.get(model, {"prompt": 0, "completion": 0})
        total = (prompt_tokens / 1_000_000 * costs.get("prompt", 0) +
                 completion_tokens / 1_000_000 * costs.get("completion", 0))
        
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=total,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        self._save()
        return total
    
    def get_total_cost(self, since: Optional[str] = None) -> float:
        if not since:
            return sum(e.total_cost for e in self.entries)
        
        since_dt = datetime.fromisoformat(since)
        return sum(
            e.total_cost for e in self.entries
            if datetime.fromisoformat(e.timestamp) >= since_dt
        )
    
    def get_by_model(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for e in self.entries:
            result[e.model] = result.get(e.model, 0.0) + e.total_cost
        return result


class BudgetManager:
    def __init__(self, monthly_limit: float = 100.0):
        self.monthly_limit = monthly_limit
        self.tracker = CostTracker()
    
    def check_budget(self) -> Dict:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        spent = self.tracker.get_total_cost(since=month_start.isoformat())
        remaining = self.monthly_limit - spent
        percent = (spent / self.monthly_limit * 100) if self.monthly_limit > 0 else 0
        
        return {
            "spent": round(spent, 4),
            "remaining": round(remaining, 4),
            "limit": self.monthly_limit,
            "percent_used": round(percent, 1),
            "over_budget": remaining < 0
        }


__all__ = ["CostTracker", "BudgetManager", "CostEntry", "MODEL_COSTS"]