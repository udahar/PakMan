"""
Model Family Tracking for PromptOS

Groups models by vendor/family for family-specific strategy learning.
Enables transfer learning across model variants.

Usage:
    families = ModelFamilies()
    
    # Get family for a model
    family = families.get_family("qwen2.5:7b")  # Returns "ollama"
    
    # Get all models in a family
    models = families.get_models_in_family("openai")
    
    # Record family-specific performance
    families.record_performance("qwen2.5:7b", "coding", ["scratchpad"], 0.95)
    
    # Get best strategy for family (works for unseen models in same family)
    best = families.get_best_strategy_for_family("qwen2.5:32b", "coding")
"""

import json
import time
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict, field


@dataclass
class ModelFamily:
    """A model family (vendor/group)."""
    name: str
    models: Set[str] = field(default_factory=set)
    shared_strategies: Dict[str, List[str]] = field(default_factory=dict)  # task_type → strategy
    family_traits: Dict[str, float] = field(default_factory=dict)  # e.g., "reasoning_strength": 0.8


@dataclass
class FamilyPerformance:
    """Performance record for a model family."""
    family: str
    model: str
    task_type: str
    strategy: List[str]
    score: float
    success: bool
    timestamp: float


class ModelFamilies:
    """
    Model family tracking for PromptOS.
    
    Features:
    - Group models by vendor/family
    - Share strategies across family members
    - Family-specific performance tracking
    - Transfer learning to unseen models
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize model families.
        
        Args:
            storage_path: Path for persistent storage
        """
        self.storage_path = storage_path or "PromptOS/model_families.json"
        
        # Pre-defined families
        self.families: Dict[str, ModelFamily] = {
            "openai": ModelFamily(
                name="openai",
                models={"gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"},
                family_traits={
                    "reasoning_strength": 0.95,
                    "code_strength": 0.9,
                    "verbosity": 0.7,
                    "follows_format": 0.9,
                }
            ),
            "ollama": ModelFamily(
                name="ollama",
                models={
                    "qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b", "qwen2.5:72b",
                    "llama3.2:1b", "llama3.2:3b", "llama3.2:7b",
                    "mistral:7b", "mixtral:8x7b",
                },
                family_traits={
                    "reasoning_strength": 0.6,
                    "code_strength": 0.65,
                    "verbosity": 0.5,
                    "follows_format": 0.7,
                }
            ),
            "anthropic": ModelFamily(
                name="anthropic",
                models={"claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2"},
                family_traits={
                    "reasoning_strength": 0.9,
                    "code_strength": 0.85,
                    "verbosity": 0.6,
                    "follows_format": 0.85,
                }
            ),
            "cerebras": ModelFamily(
                name="cerebras",
                models={"llama3.1:8b", "llama3.1:70b"},
                family_traits={
                    "reasoning_strength": 0.7,
                    "code_strength": 0.7,
                    "verbosity": 0.5,
                    "follows_format": 0.75,
                }
            ),
        }
        
        # Performance tracking
        self.performance_records: List[FamilyPerformance] = []
        
        # Family-level strategy performance
        self.family_strategy_performance: Dict[str, Dict[str, List[Dict]]] = {}
        
        # Load existing data
        self._load()
    
    def get_family(self, model: str) -> Optional[str]:
        """
        Get family name for a model.
        
        Args:
            model: Model name
        
        Returns:
            Family name or None
        """
        for family_name, family in self.families.items():
            if model in family.models:
                return family_name
        
        # Check if model name contains family hint
        model_lower = model.lower()
        
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "llama" in model_lower or "qwen" in model_lower or "mistral" in model_lower:
            return "ollama"
        elif "cerebras" in model_lower:
            return "cerebras"
        
        return None
    
    def add_model_to_family(self, model: str, family_name: str):
        """
        Add a model to a family.
        
        Args:
            model: Model name
            family_name: Family name
        """
        if family_name not in self.families:
            self.families[family_name] = ModelFamily(name=family_name)
        
        self.families[family_name].models.add(model)
    
    def get_models_in_family(self, family_name: str) -> Set[str]:
        """
        Get all models in a family.
        
        Args:
            family_name: Family name
        
        Returns:
            Set of model names
        """
        family = self.families.get(family_name)
        return family.models if family else set()
    
    def record_performance(
        self,
        model: str,
        task_type: str,
        strategy: List[str],
        score: float,
        success: bool,
    ):
        """
        Record performance for a model.
        
        Args:
            model: Model name
            task_type: Task type
            strategy: Strategy modules
            score: Performance score
            success: Whether it succeeded
        """
        family = self.get_family(model)
        
        if not family:
            return  # Unknown family
        
        # Record performance
        record = FamilyPerformance(
            family=family,
            model=model,
            task_type=task_type,
            strategy=strategy,
            score=score,
            success=success,
            timestamp=time.time(),
        )
        
        self.performance_records.append(record)
        
        # Update family-level performance
        strategy_key = ",".join(sorted(strategy))
        
        if family not in self.family_strategy_performance:
            self.family_strategy_performance[family] = {}
        
        perf_key = f"{task_type}:{strategy_key}"
        
        if perf_key not in self.family_strategy_performance[family]:
            self.family_strategy_performance[family][perf_key] = []
        
        self.family_strategy_performance[family][perf_key].append({
            "model": model,
            "score": score,
            "success": success,
            "timestamp": time.time(),
        })
        
        # Auto-save periodically
        if len(self.performance_records) % 100 == 0:
            self._save()
    
    def get_best_strategy_for_family(
        self,
        model: str,
        task_type: str,
        min_trials: int = 3,
    ) -> List[str]:
        """
        Get best strategy for a model's family.
        
        Useful for unseen models - inherits family knowledge.
        
        Args:
            model: Model name
            task_type: Task type
            min_trials: Minimum trials required
        
        Returns:
            Best strategy modules
        """
        family = self.get_family(model)
        
        if not family:
            return self._default_strategy(task_type)
        
        # Get family performance data
        if family not in self.family_strategy_performance:
            return self._default_strategy(task_type)
        
        # Find best strategy for this task type
        candidates = []
        
        for perf_key, records in self.family_strategy_performance[family].items():
            if not perf_key.startswith(f"{task_type}:"):
                continue
            
            if len(records) < min_trials:
                continue
            
            strategy_str = perf_key.replace(f"{task_type}:", "")
            strategy = strategy_str.split(",") if strategy_str else []
            
            # Calculate average score
            avg_score = sum(r["score"] for r in records) / len(records)
            success_rate = sum(1 for r in records if r["success"]) / len(records)
            
            fitness = avg_score * 0.6 + success_rate * 0.4
            candidates.append((strategy, fitness, len(records)))
        
        if not candidates:
            return self._default_strategy(task_type)
        
        # Return best
        best = max(candidates, key=lambda x: x[1])
        return best[0]
    
    def _default_strategy(self, task_type: str) -> List[str]:
        """Return default strategy for a task type."""
        defaults = {
            "coding": ["scratchpad", "verify"],
            "debugging": ["scratchpad", "verify"],
            "reasoning": ["scratchpad"],
            "writing": [],
            "chat": [],
            "tools": ["scratchpad", "tools"],
            "planning": ["decompose"],
            "review": ["verify"],
        }
        
        return defaults.get(task_type, [])
    
    def get_family_traits(self, model: str) -> Dict[str, float]:
        """
        Get family traits for a model.
        
        Args:
            model: Model name
        
        Returns:
            Family traits dict
        """
        family = self.get_family(model)
        
        if not family:
            return {}
        
        return self.families[family].family_traits
    
    def get_stats(self) -> Dict[str, Any]:
        """Get family tracking statistics."""
        return {
            "families": len(self.families),
            "total_models": sum(len(f.models) for f in self.families.values()),
            "performance_records": len(self.performance_records),
            "family_performance_data": len(self.family_strategy_performance),
        }
    
    def _save(self):
        """Save family data to storage."""
        try:
            data = {
                "families": {
                    k: {
                        "name": v.name,
                        "models": list(v.models),
                        "shared_strategies": v.shared_strategies,
                        "family_traits": v.family_traits,
                    }
                    for k, v in self.families.items()
                },
                "performance_records": [asdict(r) for r in self.performance_records[-1000:]],
                "family_strategy_performance": self.family_strategy_performance,
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[ModelFamilies] Save failed: {e}")
    
    def _load(self):
        """Load family data from storage."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Load families
                for name, fam_data in data.get("families", {}).items():
                    if name in self.families:
                        self.families[name].models.update(fam_data.get("models", []))
                        self.families[name].family_traits.update(fam_data.get("family_traits", {}))
                
                # Load performance records
                records_data = data.get("performance_records", [])
                self.performance_records = [FamilyPerformance(**r) for r in records_data]
                
                # Load family strategy performance
                self.family_strategy_performance = data.get("family_strategy_performance", {})
                
                print(f"[ModelFamilies] Loaded {len(self.performance_records)} records")
        except Exception as e:
            print(f"[ModelFamilies] Load failed: {e}")
