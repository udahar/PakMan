#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Strategy Genome - Fingerprint Tracking for Strategy Evolution

Stores and queries strategy fingerprints across all runs.
Enables Alfred to query optimal strategies per model/task.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class StrategyGenome:
    """
    Strategy fingerprint tracking system.

    Records every strategy run with full context, enabling:
    - Query optimal strategies per model/task
    - Detect patterns in successful strategies
    - Export/import strategy knowledge
    - Share learnings across Frank instances

    Usage:
        genome = StrategyGenome()

        # Record a strategy fingerprint
        genome.record(
            model="qwen2.5:7b",
            task="coding",
            strategy=["scratchpad", "verify"],
            score=0.95,
            success=True,
            tokens=450
        )

        # Query best strategies
        best = genome.query_best("qwen2.5:7b", "coding")
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize strategy genome.

        Args:
            storage_path: Path to store genome data (default: PromptOS/genome.json)
        """
        self.db_only = str(os.getenv("PROMPTOS_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.storage_path = None if self.db_only else (storage_path or "PromptOS/genome.json")
        self.genome: List[Dict] = []
        self.index: Dict[str, List[int]] = {}  # Fast lookup index

        # Load existing genome
        self._load()

    def record(
        self,
        model: str,
        task_type: str,
        strategy: List[str],
        score: float,
        success: bool,
        tokens_used: int = 0,
        ticket_id: Optional[str] = None,
        failure_mode: Optional[str] = None,
        metadata: Optional[Dict] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Record a strategy fingerprint.

        Args:
            model: Model name
            task_type: Task type
            strategy: Strategy modules used
            score: Bench score
            success: Whether it succeeded
            tokens_used: Token count
            ticket_id: Associated ticket ID
            failure_mode: Detected failure mode
            metadata: Additional metadata
            status: Explicit status - "success", "failure", or "unavailable" (connection issues)

        Returns:
            Fingerprint ID
        """
        fingerprint = {
            "id": f"fp_{len(self.genome)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "model": model,
            "task_type": task_type,
            "strategy": sorted(strategy),
            "strategy_key": ",".join(sorted(strategy)),
            "score": score,
            "success": success,
            "status": status,
            "tokens_used": tokens_used,
            "ticket_id": ticket_id,
            "failure_mode": failure_mode,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }

        # Add to genome
        idx = len(self.genome)
        self.genome.append(fingerprint)

        # Update index
        key = f"{model}:{task_type}"
        if key not in self.index:
            self.index[key] = []
        self.index[key].append(idx)

        # Auto-save periodically
        if len(self.genome) % 100 == 0:
            self._save()

        return fingerprint["id"]

    def query_best(
        self,
        model: str,
        task_type: str,
        min_trials: int = 3,
    ) -> Dict[str, Any]:
        """
        Query the best strategy for a model/task.

        Args:
            model: Model name
            task_type: Task type
            min_trials: Minimum trials required

        Returns:
            Best strategy info with stats
        """
        key = f"{model}:{task_type}"

        if key not in self.index:
            return self._default_recommendation(task_type)

        # Get all fingerprints for this model/task
        fingerprints = [self.genome[i] for i in self.index[key]]

        # Group by strategy
        strategy_stats: Dict[str, Dict] = {}

        for fp in fingerprints:
            strategy_key = fp["strategy_key"]

            if strategy_key not in strategy_stats:
                strategy_stats[strategy_key] = {
                    "strategy": fp["strategy"],
                    "trials": 0,
                    "successes": 0,
                    "total_score": 0.0,
                    "total_tokens": 0,
                    "failure_modes": {},
                }

            stats = strategy_stats[strategy_key]
            stats["trials"] += 1
            if fp["success"]:
                stats["successes"] += 1
            stats["total_score"] += fp["score"]
            stats["total_tokens"] += fp["tokens_used"]

            if fp.get("failure_mode"):
                fm = fp["failure_mode"]
                if fm not in stats["failure_modes"]:
                    stats["failure_modes"][fm] = 0
                stats["failure_modes"][fm] += 1

        # Filter by min_trials and calculate fitness
        candidates = []

        for strategy_key, stats in strategy_stats.items():
            if stats["trials"] < min_trials:
                continue

            success_rate = stats["successes"] / stats["trials"]
            avg_score = stats["total_score"] / stats["trials"]
            avg_tokens = stats["total_tokens"] / stats["trials"]

            # Fitness = success + score - token penalty
            token_penalty = min(avg_tokens / 1000, 0.2)
            fitness = (success_rate * 0.4 + avg_score * 0.6) - token_penalty

            candidates.append(
                {
                    "strategy": stats["strategy"],
                    "fitness": fitness,
                    "trials": stats["trials"],
                    "success_rate": success_rate,
                    "avg_score": avg_score,
                    "avg_tokens": avg_tokens,
                    "failure_modes": stats["failure_modes"],
                }
            )

        if not candidates:
            return self._default_recommendation(task_type)

        # Return best
        best = max(candidates, key=lambda x: x["fitness"])
        best["model"] = model
        best["task_type"] = task_type

        return best

    def _default_recommendation(self, task_type: str) -> Dict[str, Any]:
        """Return default recommendation when no data available."""
        defaults = {
            "coding": {
                "strategy": ["scratchpad", "verify"],
                "confidence": 0.5,
            },
            "debugging": {
                "strategy": ["scratchpad", "verify"],
                "confidence": 0.5,
            },
            "reasoning": {
                "strategy": ["scratchpad"],
                "confidence": 0.5,
            },
            "writing": {
                "strategy": [],
                "confidence": 0.5,
            },
            "chat": {
                "strategy": [],
                "confidence": 0.5,
            },
            "tools": {
                "strategy": ["scratchpad", "tools"],
                "confidence": 0.5,
            },
        }

        default = defaults.get(task_type, {"strategy": [], "confidence": 0.5})
        default["model"] = "unknown"
        default["task_type"] = task_type
        default["trials"] = 0

        return default

    def query_by_failure_mode(
        self,
        failure_mode: str,
        model: Optional[str] = None,
    ) -> List[Dict]:
        """
        Query fingerprints by failure mode.

        Useful for: "What strategies fail with hallucination?"

        Args:
            failure_mode: Failure mode to search
            model: Optional model filter

        Returns:
            List of matching fingerprints
        """
        results = []

        for fp in self.genome:
            if fp.get("failure_mode") == failure_mode:
                if model is None or fp["model"] == model:
                    results.append(fp)

        return results

    def get_model_profile(self, model: str) -> Dict[str, Any]:
        """
        Get complete profile for a model.

        Args:
            model: Model name

        Returns:
            Model profile with best strategies per task
        """
        profile = {
            "model": model,
            "tasks": {},
            "total_runs": 0,
            "avg_score": 0.0,
            "avg_tokens": 0,
        }

        # Get all fingerprints for this model
        model_fps = [fp for fp in self.genome if fp["model"] == model]

        if not model_fps:
            return profile

        profile["total_runs"] = len(model_fps)
        profile["avg_score"] = sum(fp["score"] for fp in model_fps) / len(model_fps)
        profile["avg_tokens"] = sum(fp["tokens_used"] for fp in model_fps) / len(
            model_fps
        )

        # Get best strategy per task type
        task_types = set(fp["task_type"] for fp in model_fps)

        for task_type in task_types:
            best = self.query_best(model, task_type)
            profile["tasks"][task_type] = best

        return profile

    def export(self, path: Optional[str] = None) -> str:
        """
        Export genome to JSON file.

        Args:
            path: Export path (default: storage_path)

        Returns:
            Export path
        """
        if self.db_only:
            return ""
        export_path = path or self.storage_path

        data = {
            "genome": self.genome[-10000:],  # Last 10k records
            "index": self.index,
            "exported_at": datetime.now().isoformat(),
        }

        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return export_path

    def import_genome(self, path: str) -> int:
        """
        Import genome from JSON file.

        Args:
            path: Import path

        Returns:
            Number of records imported
        """
        try:
            with open(path, "r") as f:
                data = json.load(f)

            imported_genome = data.get("genome", [])
            imported_index = data.get("index", {})

            # Merge
            offset = len(self.genome)
            self.genome.extend(imported_genome)

            for key, indices in imported_index.items():
                if key not in self.index:
                    self.index[key] = []
                self.index[key].extend([i + offset for i in indices])

            print(f"[Genome] Imported {len(imported_genome)} records")
            return len(imported_genome)

        except Exception as e:
            print(f"[Genome] Import failed: {e}")
            return 0

    def _save(self):
        """Save genome to storage."""
        if self.db_only:
            return
        try:
            self.export()
        except Exception as e:
            print(f"[Genome] Save failed: {e}")

    def _load(self):
        """Load genome from storage."""
        if self.db_only or not self.storage_path:
            return
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                self.genome = data.get("genome", [])
                self.index = data.get("index", {})

                print(f"[Genome] Loaded {len(self.genome)} records")
        except Exception as e:
            print(f"[Genome] Load failed: {e}")

    def stats(self) -> Dict[str, Any]:
        """Get genome statistics."""
        return {
            "total_fingerprints": len(self.genome),
            "model_task_combinations": len(self.index),
            "unique_strategies": len(set(fp["strategy_key"] for fp in self.genome)),
            "storage_path": self.storage_path,
        }
