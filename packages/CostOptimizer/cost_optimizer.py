"""
Cost Optimizer - Token Budget Manager and Model Router.

A comprehensive cost management system for AI API usage that tracks spending,
manages budgets, and selects optimal models based on cost/quality tradeoffs.

Features:
- Track API usage and costs by model and task type
- Budget management with configurable limits
- Cost-based model routing
- Spending analytics and reporting

Usage:
    from cost_optimizer import CostTracker, BudgetManager, CostRouter
    
    # Track usage
    tracker = CostTracker()
    cost = tracker.track("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    
    # Check budget
    budget_mgr = BudgetManager()
    if budget_mgr.check_budget("coding", 0.01):
        budget_mgr.deduct("coding", 0.01)
    
    # Route to optimal model
    router = CostRouter()
    model = router.select_model("coding", min_quality=7, max_cost=0.01)
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CostOptimizerError(Exception):
    """Base exception for cost optimizer operations."""
    pass


class BudgetExceededError(CostOptimizerError):
    """Raised when a budget limit is exceeded."""
    pass


MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "qwen2.5:7b": {"prompt": 0.0, "completion": 0.0},
    "qwen2.5:3b": {"prompt": 0.0, "completion": 0.0},
    "llama3.2:3b": {"prompt": 0.0, "completion": 0.0},
    "mistral:7b": {"prompt": 0.0, "completion": 0.0},
    "gpt-4o": {"prompt": 5.0, "completion": 15.0},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.6},
    "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
    "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
    "claude-3-opus": {"prompt": 15.0, "completion": 75.0},
    "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0},
    "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
}


@dataclass
class CostEntry:
    """Single cost tracking entry."""
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    task_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostEntry":
        return cls(**data)


@dataclass
class Budget:
    """Budget limit for a category."""
    name: str
    amount: float
    spent: float = 0.0
    period: str = "monthly"
    
    @property
    def remaining(self) -> float:
        """Get remaining budget."""
        return max(0.0, self.amount - self.spent)
    
    @property
    def usage_percent(self) -> float:
        """Get usage as percentage."""
        if self.amount <= 0:
            return 0.0
        return min(100.0, (self.spent / self.amount) * 100)


class CostTracker:
    """
    Track API usage and costs.
    
    Usage:
        tracker = CostTracker()
        cost = tracker.track("gpt-4o", 1000, 500)
        spending = tracker.get_spending("day")
    """
    
    DEFAULT_STORAGE_FILE = "costs/tracking.jsonl"
    
    def __init__(self, storage_file: Optional[str] = None) -> None:
        self.storage_file = storage_file or os.environ.get(
            "COST_TRACKING_FILE", self.DEFAULT_STORAGE_FILE
        )
        self.current_session_cost = 0.0
        self._session_start = datetime.now()
        
        logger.info("CostTracker initialized with storage: %s", self.storage_file)
    
    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str = "general",
    ) -> float:
        """
        Track a request and return cost.
        
        Args:
            model: Model name (e.g., "gpt-4o")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            task_type: Type of task (general, coding, creative, etc.)
        
        Returns:
            Calculated cost in USD
        """
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        
        costs = MODEL_COSTS.get(model, {"prompt": 0.0, "completion": 0.0})
        
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
        
        self._save_entry(entry)
        
        self.current_session_cost += cost
        
        logger.debug(
            "Tracked %s: %d+%d tokens = $%.6f (%s)",
            model, prompt_tokens, completion_tokens, cost, task_type
        )
        
        return cost
    
    def _save_entry(self, entry: CostEntry) -> None:
        """Save entry to storage file."""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            with open(self.storage_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except IOError as e:
            logger.error("Failed to save cost entry: %s", e)
    
    def _load_entries(self) -> List[CostEntry]:
        """Load all entries from storage."""
        entries: List[CostEntry] = []
        
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(CostEntry.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning("Skipping invalid entry: %s", e)
        except FileNotFoundError:
            pass
        except IOError as e:
            logger.error("Failed to load entries: %s", e)
        
        return entries
    
    def _filter_by_period(
        self,
        entries: List[CostEntry],
        period: str
    ) -> List[CostEntry]:
        """Filter entries by time period."""
        now = datetime.now()
        
        if period == "day":
            start = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
        elif period == "month":
            start = now - timedelta(days=30)
        else:
            return entries
        
        start_iso = start.isoformat()
        return [e for e in entries if e.timestamp > start_iso]
    
    def get_spending(
        self,
        period: str = "day"
    ) -> Dict[str, Any]:
        """
        Get spending for a period.
        
        Args:
            period: Time period (day, week, month)
        
        Returns:
            Dict with total, by_model, and by_task breakdowns
        """
        entries = self._load_entries()
        filtered = self._filter_by_period(entries, period)
        
        total = sum(e.cost for e in filtered)
        
        by_model: Dict[str, float] = {}
        for e in filtered:
            by_model[e.model] = by_model.get(e.model, 0.0) + e.cost
        
        by_task: Dict[str, float] = {}
        for e in filtered:
            by_task[e.task_type] = by_task.get(e.task_type, 0.0) + e.cost
        
        return {
            "total": total,
            "by_model": by_model,
            "by_task": by_task,
            "period": period,
            "entries_count": len(filtered),
        }
    
    def get_session_cost(self) -> float:
        """Get cost for current session."""
        return self.current_session_cost
    
    def reset_session(self) -> None:
        """Reset session cost counter."""
        self.current_session_cost = 0.0
        self._session_start = datetime.now()


class BudgetManager:
    """
    Manage budget limits for different categories.
    
    Usage:
        manager = BudgetManager()
        if manager.check_budget("coding", 0.01):
            manager.deduct("coding", 0.01)
    """
    
    DEFAULT_BUDGETS = {
        "global": 10.0,
        "session": 0.50,
        "coding": 0.20,
        "creative": 0.10,
    }
    
    def __init__(self, budgets: Optional[Dict[str, float]] = None) -> None:
        self.budgets: Dict[str, Budget] = {}
        
        for name, amount in (budgets or self.DEFAULT_BUDGETS).items():
            self.budgets[name] = Budget(name=name, amount=amount)
        
        logger.info("BudgetManager initialized with %d budgets", len(self.budgets))
    
    def check_budget(self, budget_name: str, cost: float) -> bool:
        """
        Check if we have budget for this cost.
        
        Args:
            budget_name: Name of the budget
            cost: Cost to check
        
        Returns:
            True if budget is sufficient, False otherwise
        """
        budget = self.budgets.get(budget_name)
        if not budget:
            logger.debug("Budget '%s' not found, allowing", budget_name)
            return True
        
        has_budget = (budget.spent + cost) <= budget.amount
        
        if not has_budget:
            logger.warning(
                "Budget exceeded: %s (spent $%.4f of $%.4f, need $%.4f)",
                budget_name, budget.spent, budget.amount, cost
            )
        
        return has_budget
    
    def deduct(self, budget_name: str, cost: float) -> None:
        """
        Deduct from budget.
        
        Args:
            budget_name: Name of the budget
            cost: Amount to deduct
        """
        budget = self.budgets.get(budget_name)
        if budget:
            budget.spent += cost
            logger.debug("Deducted $%.4f from '%s' (now spent: $%.4f)",
                        cost, budget_name, budget.spent)
    
    def reset_if_needed(self) -> None:
        """Reset budgets based on period."""
        now = datetime.now()
        
        for budget in self.budgets.values():
            if budget.period == "session":
                budget.spent = 0.0
                logger.debug("Reset session budget: %s", budget.name)
    
    def get_budget_status(self, budget_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific budget."""
        budget = self.budgets.get(budget_name)
        if not budget:
            return None
        
        return {
            "name": budget.name,
            "amount": budget.amount,
            "spent": budget.spent,
            "remaining": budget.remaining,
            "usage_percent": budget.usage_percent,
            "period": budget.period,
        }
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all budgets."""
        return {
            name: self.get_budget_status(name)
            for name in self.budgets
        }


class CostRouter:
    """
    Select optimal model based on cost/quality tradeoff.
    
    Usage:
        router = CostRouter()
        model = router.select_model("coding", min_quality=7, max_cost=0.01)
    """
    
    MODEL_QUALITY: Dict[str, List[Dict[str, Any]]] = {
        "general": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0.0},
            {"name": "gpt-4o-mini", "quality": 7, "cost": 0.00075},
            {"name": "gpt-4o", "quality": 9, "cost": 0.02},
        ],
        "coding": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0.0},
            {"name": "gpt-4o", "quality": 9, "cost": 0.02},
        ],
        "creative": [
            {"name": "qwen2.5:7b", "quality": 7, "cost": 0.0},
            {"name": "claude-3-sonnet", "quality": 8, "cost": 0.018},
        ],
    }
    
    def __init__(
        self,
        model_quality: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> None:
        self.MODEL_QUALITY = model_quality or self.MODEL_QUALITY
        logger.info("CostRouter initialized")
    
    def select_model(
        self,
        task_type: str = "general",
        min_quality: int = 5,
        max_cost: Optional[float] = None,
    ) -> str:
        """
        Select cheapest model meeting quality threshold.
        
        Args:
            task_type: Type of task
            min_quality: Minimum quality level (1-10)
            max_cost: Maximum cost per request
        
        Returns:
            Selected model name
        """
        candidates = self.MODEL_QUALITY.get(
            task_type, self.MODEL_QUALITY["general"]
        )
        
        filtered = [c for c in candidates if c["quality"] >= min_quality]
        
        if max_cost is not None:
            filtered = [c for c in filtered if c["cost"] <= max_cost]
        
        if not filtered:
            logger.warning(
                "No model meets criteria (type=%s, min_q=%d, max_c=%s), using fallback",
                task_type, min_quality, max_cost
            )
            return candidates[0]["name"]
        
        filtered.sort(key=lambda x: x["cost"])
        
        selected = filtered[0]["name"]
        logger.debug(
            "Selected model: %s (type=%s, quality=%d, cost=$%.6f)",
            selected, task_type, filtered[0]["quality"], filtered[0]["cost"]
        )
        
        return selected
    
    def add_model(
        self,
        task_type: str,
        name: str,
        quality: int,
        cost: float
    ) -> None:
        """Add a model to the routing table."""
        if task_type not in self.MODEL_QUALITY:
            self.MODEL_QUALITY[task_type] = []
        
        self.MODEL_QUALITY[task_type].append({
            "name": name,
            "quality": quality,
            "cost": cost,
        })
        
        logger.info("Added model %s to %s (quality=%d, cost=$%.6f)",
                   name, task_type, quality, cost)


def print_dashboard() -> None:
    """Print cost optimization dashboard."""
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
    logging.basicConfig(level=logging.INFO)
    
    router = CostRouter()
    
    print("Model selection:")
    print(f"  General: {router.select_model('general')}")
    print(f"  Coding (max $0.01): {router.select_model('coding', max_cost=0.01)}")
    print(f"  Creative: {router.select_model('creative')}")
    
    print_dashboard()
