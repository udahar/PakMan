#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Strategy Farming - Positive/Negative Learning

Amplifies successful strategies and avoids failed ones.
Learns which strategies work best for which models/tasks.
"""

import json
import os
import time
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class SuccessRecord:
    """A successful strategy record."""
    model: str
    task_type: str
    strategy: List[str]
    score: float
    timestamp: float


@dataclass
class FailureRecord:
    """A failed strategy record."""
    model: str
    task_type: str
    strategy: List[str]
    failure_mode: str
    timestamp: float


class StrategyFarming:
    """
    Strategy farming with positive/negative learning.
    
    Features:
    - Amplify successful strategies
    - Avoid failed strategies
    - Family-wide learning
    - Export/import knowledge
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize strategy farming.
        
        Args:
            storage_path: Path for persistent storage
        """
        self.storage_path = storage_path or "PromptForge/strategy_farming.json"
        self.db_only = str(os.getenv("PROMPTFORGE_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        
        # Success tracking
        self.successes: List[SuccessRecord] = []
        self.success_counts: Dict[str, int] = {}  # strategy_key → count
        
        # Failure tracking (negative learning)
        self.failures: List[FailureRecord] = []
        self.avoided_strategies: Dict[str, Set[str]] = {}  # model:task → strategy_keys to avoid
        
        # Amplification weights
        self.strategy_weights: Dict[str, float] = {}
        
        # Load existing data
        self._load()
    
    def record_success(
        self,
        model: str,
        task_type: str,
        strategy: List[str],
        score: float,
    ):
        """
        Record a successful strategy.
        
        Args:
            model: Model name
            task_type: Task type
            strategy: Strategy modules
            score: Performance score
        """
        record = SuccessRecord(
            model=model,
            task_type=task_type,
            strategy=strategy,
            score=score,
            timestamp=time.time(),
        )
        
        self.successes.append(record)
        
        # Update success counts
        strategy_key = ",".join(sorted(strategy))
        count_key = f"{model}:{task_type}:{strategy_key}"
        self.success_counts[count_key] = self.success_counts.get(count_key, 0) + 1
        
        # Amplify weight
        old_weight = self.strategy_weights.get(count_key, 1.0)
        self.strategy_weights[count_key] = old_weight * 0.9 + score * 0.1
        
        # Auto-save
        if len(self.successes) % 50 == 0:
            self._save()
    
    def record_failure(
        self,
        model: str,
        task_type: str,
        strategy: List[str],
        failure_mode: str,
    ):
        """
        Record a failed strategy (negative learning).
        
        Args:
            model: Model name
            task_type: Task type
            strategy: Strategy modules
            failure_mode: Failure mode
        """
        record = FailureRecord(
            model=model,
            task_type=task_type,
            strategy=strategy,
            failure_mode=failure_mode,
            timestamp=time.time(),
        )
        
        self.failures.append(record)
        
        # Add to avoided strategies
        key = f"{model}:{task_type}"
        if key not in self.avoided_strategies:
            self.avoided_strategies[key] = set()
        
        strategy_key = ",".join(sorted(strategy))
        self.avoided_strategies[key].add(strategy_key)
        
        # Also add to family members (negative learning spreads)
        family_key = f"*:{task_type}"  # Wildcard for family
        if family_key not in self.avoided_strategies:
            self.avoided_strategies[family_key] = set()
        self.avoided_strategies[family_key].add(strategy_key)
        
        # Auto-save
        if len(self.failures) % 20 == 0:
            self._save()
    
    def get_best_strategy(
        self,
        model: str,
        task_type: str,
        min_trials: int = 3,
        exploration_rate: float = 0.1,
    ) -> List[str]:
        """
        Get best strategy for a model/task with exploration.
        
        Args:
            model: Model name
            task_type: Task type
            min_trials: Minimum trials required
            exploration_rate: Rate of random exploration (0.1 = 10%)
        
        Returns:
            Best strategy modules
        """
        import random
        
        # Epsilon exploration: 10% random strategy
        if random.random() < exploration_rate:
            # Return random strategy from successes
            candidates = [
                record.strategy for record in self.successes
                if record.task_type == task_type
            ]
            if candidates:
                return random.choice(candidates)
        
        # Get all strategies for this model/task
        candidates = []
        
        for record in self.successes:
            if record.model == model and record.task_type == task_type:
                strategy_key = ",".join(sorted(record.strategy))
                candidates.append({
                    "strategy": record.strategy,
                    "score": record.score,
                    "key": strategy_key,
                })
        
        if not candidates:
            return self._default_strategy(task_type)
        
        # Filter by min_trials
        strategy_counts = {}
        for c in candidates:
            strategy_counts[c["key"]] = strategy_counts.get(c["key"], 0) + 1
        
        filtered = [
            c for c in candidates
            if strategy_counts[c["key"]] >= min_trials
        ]
        
        if not filtered:
            return self._default_strategy(task_type)
        
        # Check if avoided
        avoided = self.get_avoided_strategies(model, task_type)
        filtered = [
            c for c in filtered
            if c["key"] not in avoided
        ]
        
        if not filtered:
            return self._default_strategy(task_type)
        
        # Return best
        best = max(filtered, key=lambda x: x["score"])
        return best["strategy"]
    
    def get_avoided_strategies(
        self,
        model: str,
        task_type: str,
    ) -> List[str]:
        """
        Get list of avoided strategies for a model/task.
        
        Args:
            model: Model name
            task_type: Task type
        
        Returns:
            List of avoided strategy keys
        """
        avoided = set()
        
        # Model-specific
        key = f"{model}:{task_type}"
        if key in self.avoided_strategies:
            avoided.update(self.avoided_strategies[key])
        
        # Family-wide
        family_key = f"*:{task_type}"
        if family_key in self.avoided_strategies:
            avoided.update(self.avoided_strategies[family_key])
        
        return list(avoided)
    
    def _default_strategy(self, task_type: str) -> List[str]:
        """Return default strategy for a task type."""
        defaults = {
            "coding": ["scratchpad", "verify"],
            "debugging": ["scratchpad", "verify"],
            "reasoning": ["scratchpad"],
            "discipline": ["format"],
            "tools": ["tools"],
            "general": ["scratchpad"],
        }
        
        return defaults.get(task_type, ["scratchpad"])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get farming statistics."""
        return {
            "total_successes": len(self.successes),
            "total_failures": len(self.failures),
            "unique_strategies_tracked": len(self.success_counts),
            "avoided_strategy_count": sum(
                len(v) for v in self.avoided_strategies.values()
            ),
        }
    
    def _save(self):
        """Save farming data to storage."""
        if self.db_only:
            return
        try:
            data = {
                "successes": [asdict(r) for r in self.successes[-500:]],
                "failures": [asdict(r) for r in self.failures[-200:]],
                "success_counts": self.success_counts,
                "avoided_strategies": {
                    k: list(v) for k, v in self.avoided_strategies.items()
                },
                "strategy_weights": self.strategy_weights,
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[StrategyFarming] Save failed: {e}")
    
    def _load(self):
        """Load farming data from storage."""
        if self.db_only:
            return
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.successes = [
                    SuccessRecord(**r) for r in data.get("successes", [])
                ]
                self.failures = [
                    FailureRecord(**r) for r in data.get("failures", [])
                ]
                self.success_counts = data.get("success_counts", {})
                self.avoided_strategies = {
                    k: set(v) for k, v in data.get("avoided_strategies", {}).items()
                }
                self.strategy_weights = data.get("strategy_weights", {})
                
                print(f"[StrategyFarming] Loaded {len(self.successes)} successes, {len(self.failures)} failures")
        except Exception as e:
            print(f"[StrategyFarming] Load failed: {e}")
