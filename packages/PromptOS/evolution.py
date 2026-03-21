#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Strategy Evolution - Self-Optimization Based on Bench Results

Automatically evolves strategy stacks based on ticket success/failure.
Implements real genetic algorithm with population, selection, mutation, and crossover.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import random
import json
import os
from pathlib import Path


@dataclass
class EvolvedStrategy:
    """An evolved strategy candidate."""

    strategy: List[str]
    fitness: float
    generation: int
    parent_fitness: float
    mutation_type: str  # "none", "add", "remove", "crossover"
    created_at: str


class StrategyEvolution:
    """
    Self-optimizing strategy evolution system.

    Learns which strategy combinations work best for which models/tasks
    based on Bench scoring and ticket outcomes.

    Features:
    - Real genetic algorithm with population management
    - Tournament selection
    - Mutation and crossover operators
    - Offspring tracking and evaluation
    - Elitism (keep best strategies)

    Usage:
        evolution = StrategyEvolution()

        # Record results
        evolution.record_result(
            model="qwen2.5:7b",
            task="coding",
            strategy=["scratchpad", "verify"],
            success=True,
            score=0.95
        )

        # Get evolved best strategy
        best = evolution.get_best_strategy("qwen2.5:7b", "coding")

        # Get suggested offspring (new strategies to try)
        offspring = evolution.get_offspring_suggestions("qwen2.5:7b", "coding")
    """

    def __init__(self, storage_path: Optional[str] = None):
        # Strategy performance tracking
        self.strategy_performance: Dict[str, Dict[str, List[Dict]]] = {}

        # Evolution history
        self.evolution_history: List[Dict] = []

        # Population management - stores evolved strategies
        self.population: Dict[str, List[EvolvedStrategy]] = {}

        # Offspring tracking - strategies to try next
        self.pending_offspring: Dict[str, List[EvolvedStrategy]] = {}

        # Mutation rates (for exploration)
        self.mutation_rate = 0.2
        self.crossover_rate = 0.3
        self.population_size = 10
        self.elite_count = 3

        # Available modules
        self.available_modules = [
            "role",
            "decompose",
            "scratchpad",
            "tools",
            "verify",
            "format",
            "planner",
            "few_shot",
            "constraints",
        ]

        # Storage
        self.db_only = str(os.getenv("PROMPTOS_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.storage_path = None if self.db_only else (storage_path or "PromptOS/evolution_data.json")
        self._load()

    def record_result(
        self,
        model: str,
        task_type: str,
        strategy: List[str],
        success: bool,
        score: float,
        tokens_used: int = 0,
        status: Optional[str] = None,
    ):
        """
        Record a strategy result for evolution.

        Args:
            model: Model name
            task_type: Task type
            strategy: Strategy modules used
            success: Whether it succeeded
            score: Bench score
            tokens_used: Token count
            status: Explicit status - "success", "failure", or "unavailable"
        """
        key = f"{model}:{task_type}"

        if key not in self.strategy_performance:
            self.strategy_performance[key] = {}
            self.population[key] = []
            self.pending_offspring[key] = []

        strategy_key = ",".join(sorted(strategy))

        if strategy_key not in self.strategy_performance[key]:
            self.strategy_performance[key][strategy_key] = []

        self.strategy_performance[key][strategy_key].append(
            {
                "success": success,
                "score": score,
                "status": status,
                "tokens_used": tokens_used,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Update population fitness if this strategy is in population
        self._update_population_fitness(key, strategy_key, score)

        # Trigger evolution if enough data
        total_trials = sum(len(v) for v in self.strategy_performance[key].values())
        if total_trials >= 5:
            self._evolve(key)

        # Auto-save
        self._save()

    def _update_population_fitness(self, key: str, strategy_key: str, new_score: float):
        """Update fitness for a strategy in the population."""
        if key not in self.population:
            return

        strategy_list = strategy_key.split(",") if strategy_key else []

        for evo in self.population[key]:
            if (
                evo.strategy == strategy_list
                or ",".join(sorted(evo.strategy)) == strategy_key
            ):
                # Update with running average
                evo.fitness = (evo.fitness + new_score) / 2
                break

    def _evolve(self, key: str):
        """Run evolution step for a model/task combination."""
        # Get all strategies and their fitness
        population_data = self._get_sorted_strategies(key)

        if len(population_data) < 2:
            return

        # Extract top strategies as parents
        parents = [s[0] for s in population_data[: self.elite_count]]

        # Create offspring
        new_offspring = []

        # Generate offspring through mutation and crossover
        for _ in range(self.population_size):
            parent = random.choice(parents)
            parent_fitness = parent[1]
            parent_strategy = parent[0].split(",") if parent[0] else []

            # Decide: mutate or crossover
            if random.random() < self.crossover_rate and len(parents) > 1:
                # Crossover
                parent2 = random.choice(parents)
                parent2_strategy = parent2[0].split(",") if parent2[0] else []
                child1, child2 = self.crossover(parent_strategy, parent2_strategy)
                offspring_strategy = child1
                mutation_type = "crossover"
            else:
                # Mutation
                offspring_strategy = self.mutate_strategy(
                    parent_strategy, self.available_modules
                )
                mutation_type = "mutated"

            # Ensure valid
            if not offspring_strategy:
                offspring_strategy = self._default_strategy(key.split(":")[-1])

            # Check if it's new
            offspring_key = ",".join(sorted(offspring_strategy))
            existing = [s[0] for s in population_data]

            if offspring_key not in existing:
                # Create new evolved strategy
                evo = EvolvedStrategy(
                    strategy=offspring_strategy,
                    fitness=parent_fitness,  # Start with parent fitness
                    generation=len(self.evolution_history) + 1,
                    parent_fitness=parent_fitness,
                    mutation_type=mutation_type,
                    created_at=datetime.now().isoformat(),
                )
                new_offspring.append(evo)

        # Add offspring to pending
        self.pending_offspring[key].extend(new_offspring)

        # Record evolution event
        self.evolution_history.append(
            {
                "key": key,
                "parents": parents[:3],
                "offspring_generated": len(new_offspring),
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _get_sorted_strategies(self, key: str) -> List[Tuple[str, float]]:
        """Get all strategies sorted by fitness."""
        if key not in self.strategy_performance:
            return []

        performances = []

        for strategy_key, results in self.strategy_performance[key].items():
            if not results:
                continue

            success_rate = sum(1 for r in results if r["success"]) / len(results)
            avg_score = sum(r["score"] for r in results) / len(results)
            avg_tokens = sum(r["tokens_used"] for r in results) / len(results)
            token_penalty = min(avg_tokens / 1000, 0.2)

            fitness = (success_rate * 0.5 + avg_score * 0.5) - token_penalty
            performances.append((strategy_key, fitness))

        return sorted(performances, key=lambda x: x[1], reverse=True)

    def get_offspring_suggestions(
        self,
        model: str,
        task_type: str,
        n: int = 3,
    ) -> List[List[str]]:
        """
        Get suggested new strategies to try (offspring).

        Args:
            model: Model name
            task_type: Task type
            n: Number of suggestions

        Returns:
            List of strategy modules to try
        """
        key = f"{model}:{task_type}"

        if key not in self.pending_offspring:
            return []

        pending = self.pending_offspring[key]

        if not pending:
            return []

        # Return top n suggestions
        suggestions = [evo.strategy for evo in pending[:n]]

        # Mark as suggested (they'll be removed after trials)
        for evo in pending[:n]:
            evo.fitness = -1  # Mark as pending trial

        return suggestions

    def _maybe_evolve(self, key: str):
        """Legacy method - now handled by _evolve."""
        self._evolve(key)

    def _get_best_performing_strategy(self, key: str) -> Optional[List[str]]:
        """Get the best performing strategy for a model/task."""
        if key not in self.strategy_performance:
            return None

        performances = {}

        for strategy_key, results in self.strategy_performance[key].items():
            if not results:
                continue

            # Calculate fitness (weighted combination of success rate and score)
            success_rate = sum(1 for r in results if r["success"]) / len(results)
            avg_score = sum(r["score"] for r in results) / len(results)

            # Token efficiency penalty
            avg_tokens = sum(r["tokens_used"] for r in results) / len(results)
            token_penalty = min(avg_tokens / 1000, 0.2)  # Max 20% penalty

            fitness = (success_rate * 0.5 + avg_score * 0.5) - token_penalty
            performances[strategy_key] = fitness

        if not performances:
            return None

        best_key = max(performances, key=performances.get)
        return best_key.split(",") if best_key else None

    def get_best_strategy(
        self,
        model: str,
        task_type: str,
        min_trials: int = 3,
    ) -> List[str]:
        """
        Get the best evolved strategy for a model/task.

        Args:
            model: Model name
            task_type: Task type
            min_trials: Minimum trials before considering a strategy

        Returns:
            Best strategy modules
        """
        key = f"{model}:{task_type}"

        if key not in self.strategy_performance:
            return self._default_strategy(task_type)

        # Find strategies with enough trials
        candidates = []

        for strategy_key, results in self.strategy_performance[key].items():
            if len(results) >= min_trials:
                # Calculate fitness
                success_rate = sum(1 for r in results if r["success"]) / len(results)
                avg_score = sum(r["score"] for r in results) / len(results)
                fitness = success_rate * 0.4 + avg_score * 0.6

                candidates.append((strategy_key, fitness))

        if not candidates:
            return self._default_strategy(task_type)

        # Return best
        best_key = max(candidates, key=lambda x: x[1])[0]
        return best_key.split(",") if best_key else self._default_strategy(task_type)

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

    def mutate_strategy(
        self, strategy: List[str], available_modules: List[str]
    ) -> List[str]:
        """
        Mutate a strategy (for exploration).

        Args:
            strategy: Current strategy
            available_modules: Available modules to add

        Returns:
            Mutated strategy
        """
        mutated = strategy.copy()

        # Random mutation
        if random.random() < self.mutation_rate:
            # Add a random module
            if available_modules and random.random() < 0.5:
                new_module = random.choice(available_modules)
                if new_module not in mutated:
                    mutated.append(new_module)

            # Remove a random module
            elif mutated and random.random() < 0.5:
                mutated.pop(random.randint(0, len(mutated) - 1))

        return mutated

    def crossover(
        self,
        strategy1: List[str],
        strategy2: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        Crossover two strategies (for exploration).

        Args:
            strategy1: First parent strategy
            strategy2: Second parent strategy

        Returns:
            Two child strategies
        """
        if random.random() > self.crossover_rate:
            return strategy1.copy(), strategy2.copy()

        # Single-point crossover
        if not strategy1 or not strategy2:
            return strategy1.copy(), strategy2.copy()

        point = random.randint(1, min(len(strategy1), len(strategy2)) - 1)

        child1 = strategy1[:point] + strategy2[point:]
        child2 = strategy2[:point] + strategy1[point:]

        return child1, child2

    def get_evolution_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        total_records = sum(
            len(results)
            for model_task in self.strategy_performance.values()
            for results in model_task.values()
        )

        return {
            "model_task_combinations": len(self.strategy_performance),
            "unique_strategies_tested": sum(
                len(strategies) for strategies in self.strategy_performance.values()
            ),
            "total_records": total_records,
            "evolution_events": len(self.evolution_history),
            "pending_offspring": sum(len(v) for v in self.pending_offspring.values()),
        }

    def _save(self):
        """Save evolution data to storage."""
        if self.db_only or not self.storage_path:
            return
        try:
            data = {
                "strategy_performance": self.strategy_performance,
                "evolution_history": self.evolution_history[-100:],
                "population": {
                    k: [asdict(v) for v in vs] for k, vs in self.population.items()
                },
                "pending_offspring": {
                    k: [asdict(v) for v in vs]
                    for k, vs in self.pending_offspring.items()
                },
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[Evolution] Save failed: {e}")

    def _load(self):
        """Load evolution data from storage."""
        if self.db_only or not self.storage_path:
            return
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                self.strategy_performance = data.get("strategy_performance", {})

                # Restore population
                self.population = {}
                for k, vs in data.get("population", {}).items():
                    self.population[k] = [EvolvedStrategy(**v) for v in vs]

                # Restore pending offspring
                self.pending_offspring = {}
                for k, vs in data.get("pending_offspring", {}).items():
                    self.pending_offspring[k] = [EvolvedStrategy(**v) for v in vs]

                print(
                    f"[Evolution] Loaded {len(self.strategy_performance)} model-task combinations"
                )
        except Exception as e:
            print(f"[Evolution] Load failed: {e}")
