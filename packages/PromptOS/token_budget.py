"""
Token Budget Enforcement for PromptOS

Enforces token limits per ticket type, model, or strategy.
Prevents runaway token usage and controls costs.

Usage:
    budget = TokenBudget(
        default_limit=1000,
        limits_by_model={"qwen2.5:3b": 500, "gpt-4o": 2000},
        limits_by_task={"chat": 300, "coding": 1500}
    )
    
    # Check before running
    if budget.would_exceed(prompt, model, strategy):
        strategy = budget.get_cheaper_strategy(model, strategy)
    
    # Record usage
    budget.record(prompt, response, model, strategy)
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class TokenRecord:
    """A token usage record."""
    prompt: str
    response: str
    model: str
    strategy: List[str]
    prompt_tokens: int
    response_tokens: int
    total_tokens: int
    timestamp: float
    ticket_id: Optional[str] = None


class TokenBudget:
    """
    Token budget enforcement for PromptOS.
    
    Features:
    - Global token limits
    - Per-model limits
    - Per-task-type limits
    - Per-ticket limits
    - Strategy cost estimation
    - Auto-downgrade to cheaper strategies
    """
    
    def __init__(
        self,
        default_limit: int = 1000,
        limits_by_model: Optional[Dict[str, int]] = None,
        limits_by_task: Optional[Dict[str, int]] = None,
        limits_by_ticket: Optional[Dict[str, int]] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize token budget.
        
        Args:
            default_limit: Default token limit (1000)
            limits_by_model: Per-model limits
            limits_by_task: Per-task-type limits
            limits_by_ticket: Per-ticket-type limits
            storage_path: Path for persistent storage
        """
        self.default_limit = default_limit
        self.limits_by_model = limits_by_model or {}
        self.limits_by_task = limits_by_task or {}
        self.limits_by_ticket = limits_by_ticket or {}
        self.storage_path = storage_path or "PromptOS/token_budget.json"
        
        # Usage tracking
        self.records: List[TokenRecord] = []
        self.usage_by_model: Dict[str, int] = {}
        self.usage_by_task: Dict[str, int] = {}
        self.usage_by_ticket: Dict[str, int] = {}
        
        # Strategy cost tracking (avg tokens per strategy module)
        self.strategy_costs: Dict[str, float] = {
            "role": 50,
            "decompose": 80,
            "scratchpad": 150,
            "tools": 100,
            "verify": 120,
            "format": 40,
            "planner": 100,
            "few_shot": 200,
            "constraints": 80,
        }
        
        # Load existing data
        self._load()
    
    def get_limit(
        self,
        model: str,
        task_type: str,
        ticket_type: Optional[str] = None,
    ) -> int:
        """
        Get token limit for a model/task/ticket combination.
        
        Args:
            model: Model name
            task_type: Task type
            ticket_type: Optional ticket type
        
        Returns:
            Token limit
        """
        # Most specific limit wins
        if ticket_type and ticket_type in self.limits_by_ticket:
            return self.limits_by_ticket[ticket_type]
        
        if model in self.limits_by_model:
            return self.limits_by_model[model]
        
        if task_type in self.limits_by_task:
            return self.limits_by_task[task_type]
        
        return self.default_limit
    
    def estimate_tokens(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
    ) -> Tuple[int, int]:
        """
        Estimate token usage for a prompt + strategy.
        
        Args:
            prompt: Input prompt
            model: Model name
            strategy: Strategy modules
        
        Returns:
            (prompt_tokens, total_tokens) estimate
        """
        # Prompt tokens (~4 chars per token)
        prompt_tokens = len(prompt) // 4
        
        # Strategy overhead
        strategy_tokens = sum(
            self.strategy_costs.get(module, 50)
            for module in strategy
        )
        
        # Model multiplier (some models use more tokens)
        model_multiplier = self._get_model_multiplier(model)
        
        # Estimated response (varies by task type)
        estimated_response = prompt_tokens * model_multiplier
        
        total_tokens = prompt_tokens + strategy_tokens + estimated_response
        
        return prompt_tokens, total_tokens
    
    def would_exceed(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
        task_type: str,
        ticket_type: Optional[str] = None,
    ) -> bool:
        """
        Check if a request would exceed budget.
        
        Args:
            prompt: Input prompt
            model: Model name
            strategy: Strategy modules
            task_type: Task type
            ticket_type: Optional ticket type
        
        Returns:
            True if would exceed limit
        """
        limit = self.get_limit(model, task_type, ticket_type)
        _, estimated_total = self.estimate_tokens(prompt, model, strategy)
        
        return estimated_total > limit
    
    def get_cheaper_strategy(
        self,
        model: str,
        current_strategy: List[str],
        task_type: str,
        ticket_type: Optional[str] = None,
    ) -> List[str]:
        """
        Get a cheaper strategy that fits budget.
        
        Args:
            model: Model name
            current_strategy: Current strategy modules
            task_type: Task type
            ticket_type: Optional ticket type
        
        Returns:
            Cheaper strategy modules
        """
        limit = self.get_limit(model, task_type, ticket_type)
        
        # Try removing modules one by one (most expensive first)
        sorted_modules = sorted(
            current_strategy,
            key=lambda m: self.strategy_costs.get(m, 50),
            reverse=True,
        )
        
        for module in sorted_modules:
            test_strategy = [m for m in current_strategy if m != module]
            _, estimated = self.estimate_tokens("", model, test_strategy)
            
            if estimated <= limit:
                return test_strategy
        
        # If still over limit, return empty strategy
        return []
    
    def _get_model_multiplier(self, model: str) -> float:
        """Get token multiplier for a model."""
        # Larger models tend to be more verbose
        multipliers = {
            "gpt-4o": 1.5,
            "gpt-4": 1.5,
            "claude": 1.3,
            "qwen2.5:72b": 1.2,
            "qwen2.5:32b": 1.1,
            "qwen2.5:7b": 1.0,
            "qwen2.5:3b": 0.9,
            "llama3.2:3b": 0.9,
        }
        
        for model_name, mult in multipliers.items():
            if model_name in model.lower():
                return mult
        
        return 1.0  # Default
    
    def record(
        self,
        prompt: str,
        response: str,
        model: str,
        strategy: List[str],
        prompt_tokens: int,
        response_tokens: int,
        ticket_id: Optional[str] = None,
    ):
        """
        Record actual token usage.
        
        Args:
            prompt: Input prompt
            response: LLM response
            model: Model name
            strategy: Strategy modules
            prompt_tokens: Actual prompt tokens
            response_tokens: Actual response tokens
            ticket_id: Optional ticket ID
        """
        total_tokens = prompt_tokens + response_tokens
        
        record = TokenRecord(
            prompt=prompt,
            response=response,
            model=model,
            strategy=strategy,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            total_tokens=total_tokens,
            timestamp=time.time(),
            ticket_id=ticket_id,
        )
        
        self.records.append(record)
        
        # Update usage tracking
        self.usage_by_model[model] = self.usage_by_model.get(model, 0) + total_tokens
        
        task_type = self._classify_task(prompt)
        self.usage_by_task[task_type] = self.usage_by_task.get(task_type, 0) + total_tokens
        
        if ticket_id:
            self.usage_by_ticket[ticket_id] = self.usage_by_ticket.get(ticket_id, 0) + total_tokens
        
        # Update strategy cost estimates
        for module in strategy:
            old_avg = self.strategy_costs.get(module, 50)
            # Running average
            self.strategy_costs[module] = old_avg * 0.9 + (total_tokens / len(strategy)) * 0.1
        
        # Auto-save periodically
        if len(self.records) % 100 == 0:
            self._save()
    
    def _classify_task(self, prompt: str) -> str:
        """Classify prompt into task type."""
        prompt_lower = prompt.lower()
        
        task_keywords = {
            "coding": ["write", "create", "build", "implement", "code"],
            "debugging": ["fix", "debug", "error", "bug"],
            "reasoning": ["explain", "analyze", "why", "how"],
            "chat": ["hello", "hi", "how are"],
        }
        
        for task, keywords in task_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return task
        
        return "general"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_tokens = sum(r.total_tokens for r in self.records)
        
        return {
            "total_requests": len(self.records),
            "total_tokens": total_tokens,
            "avg_tokens_per_request": total_tokens / len(self.records) if self.records else 0,
            "usage_by_model": self.usage_by_model,
            "usage_by_task": self.usage_by_task,
            "strategy_costs": self.strategy_costs,
        }
    
    def _save(self):
        """Save budget data to storage."""
        try:
            data = {
                "records": [asdict(r) for r in self.records[-1000:]],  # Last 1000
                "usage_by_model": self.usage_by_model,
                "usage_by_task": self.usage_by_task,
                "usage_by_ticket": self.usage_by_ticket,
                "strategy_costs": self.strategy_costs,
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[TokenBudget] Save failed: {e}")
    
    def _load(self):
        """Load budget data from storage."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.usage_by_model = data.get("usage_by_model", {})
                self.usage_by_task = data.get("usage_by_task", {})
                self.usage_by_ticket = data.get("usage_by_ticket", {})
                self.strategy_costs = data.get("strategy_costs", self.strategy_costs)
                
                # Load records
                records_data = data.get("records", [])
                self.records = [TokenRecord(**r) for r in records_data]
                
                print(f"[TokenBudget] Loaded {len(self.records)} records")
        except Exception as e:
            print(f"[TokenBudget] Load failed: {e}")
