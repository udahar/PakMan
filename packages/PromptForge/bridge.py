#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
PromptOS + PromptForge Integration

Bridges the two systems:
- PromptOS genome ↔ PromptForge strategy farming
- A/B test results update genome
- Genome best strategies feed into farming
- End-to-end distillation pipeline
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import time


class PromptOSForgeBridge:
    """
    Bridge between PromptOS and PromptForge.

    Enables:
    - Bidirectional data flow between genome and farming
    - End-to-end strategy discovery and distillation
    - Seamless model training pipeline

    Usage:
        bridge = PromptOSForgeBridge(promptos, promptforge)

        # Run experiment, update both systems
        bridge.run_and_learn(prompt, model, strategies)

        # Get best strategy for a model/task
        best = bridge.get_best_strategy("qwen2.5:7b", "coding")

        # Run full pipeline: discover → test → distill → train
        result = bridge.run_distillation_pipeline("coding", base_model="qwen2.5:3b")
    """

    def __init__(
        self,
        promptos_instance: Any,
        promptforge_instance: Any,
    ):
        """
        Initialize bridge.

        Args:
            promptos_instance: PromptOS instance
            promptforge_instance: ForgeEngine instance
        """
        self.promptos = promptos_instance
        self.forge = promptforge_instance

        # Track integration stats
        self.sync_stats = {
            "genome_to_farming": 0,
            "farming_to_genome": 0,
            "ab_tests_performed": 0,
            "distillations_run": 0,
        }

        # Initial sync
        self._sync_genome_to_farming()

    def _sync_genome_to_farming(self):
        """Sync genome best strategies to PromptForge farming."""
        if not hasattr(self.promptos, "genome") or not self.forge.farming:
            return

        # Get all genome records
        genome = self.promptos.genome

        if not hasattr(genome, "genome") or not genome.genome:
            return

        # Extract best strategies per model/task
        model_tasks = set()
        for record in genome.genome:
            model_tasks.add(
                (record.get("model", "unknown"), record.get("task_type", "unknown"))
            )

        for model, task_type in model_tasks:
            best = genome.query_best(model, task_type)
            if best and best.get("trials", 0) > 0:
                # Record in farming as success
                self.forge.farming.record_success(
                    model=model,
                    task_type=task_type,
                    strategy=best.get("strategy", []),
                    score=best.get("avg_score", 0.5),
                )
                self.sync_stats["genome_to_farming"] += 1

    def _sync_farming_to_genome(self):
        """Sync PromptForge farming best strategies to genome."""
        if not hasattr(self.promptos, "genome") or not self.forge.farming:
            return

        # This is handled automatically when A/B tests complete
        # This method is for explicit synchronization
        pass

    def run_and_learn(
        self,
        prompt: str,
        model: str,
        strategies: List[List[str]],
        task_type: Optional[str] = None,
        n_runs: int = 3,
    ) -> Dict[str, Any]:
        """
        Run A/B test and sync results to both systems.

        Args:
            prompt: Test prompt
            model: Model to test
            strategies: List of strategy combinations to test
            task_type: Task type
            n_runs: Number of runs per strategy

        Returns:
            A/B test results
        """
        # Run A/B test
        result = self.forge.ab_test(
            prompt=prompt,
            model=model,
            strategies=strategies,
            task_type=task_type,
            n_runs=n_runs,
        )

        self.sync_stats["ab_tests_performed"] += 1

        # Update genome with results
        winner = result.get("analysis", {}).get("winner", {})
        if winner:
            # Record in genome
            self.promptos.genome.record(
                model=model,
                task_type=result.get("task_type", "unknown"),
                strategy=winner.get("strategy", []),
                score=winner.get("fitness", 0.5),
                success=winner.get("fitness", 0.5) >= 0.7,
            )

            # Record in evolution
            self.promptos.evolution.record_result(
                model=model,
                task_type=result.get("task_type", "unknown"),
                strategy=winner.get("strategy", []),
                success=winner.get("fitness", 0.5) >= 0.7,
                score=winner.get("fitness", 0.5),
            )

        return result

    def get_best_strategy(
        self,
        model: str,
        task_type: str,
    ) -> List[str]:
        """
        Get best strategy from combined intelligence.

        Checks: 1) Genome 2) Farming 3) Evolution

        Args:
            model: Model name
            task_type: Task type

        Returns:
            Best strategy modules
        """
        # Try genome first
        genome_best = self.promptos.genome.query_best(model, task_type)
        if genome_best and genome_best.get("trials", 0) >= 3:
            return genome_best.get("strategy", [])

        # Try farming
        farming_best = self.forge.farming.get_best_strategy(model, task_type)
        if farming_best:
            return farming_best

        # Try evolution
        evolution_best = self.promptos.evolution.get_best_strategy(model, task_type)
        if evolution_best:
            return evolution_best

        # Default
        return ["scratchpad", "verify"]

    def run_distillation_pipeline(
        self,
        task_type: str,
        base_model: str,
        test_prompts: Optional[List[str]] = None,
        min_score: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Run full distillation pipeline:
        1. Prepare training dataset from successful strategies
        2. Train model on distilled strategies
        3. Test in arena against base model

        Args:
            task_type: Task type to focus on
            base_model: Base model to train
            test_prompts: Prompts for arena testing
            min_score: Minimum score for training data

        Returns:
            Pipeline results
        """
        # Step 1: Prepare dataset
        dataset = self.forge.distillation.prepare_training_dataset(
            task_type=task_type,
            min_score=min_score,
            max_examples=100,
        )

        if dataset.num_examples == 0:
            return {"error": "No training data available", "success": False}

        # Step 2: Train model
        output_model = f"{base_model.replace(':', '-')}-distilled-{task_type}"
        trained = self.forge.distillation.train_model(
            base_model=base_model,
            dataset=dataset,
            output_model=output_model,
        )

        self.sync_stats["distillations_run"] += 1

        # Step 3: Test in arena if we have test prompts
        arena_result = None
        if test_prompts:
            arena_result = self.forge.distillation.test_in_arena(
                trained_model=trained.model_name,
                untrained_model=base_model,
                test_prompts=test_prompts,
                task_type=task_type,
                n_runs=3,
            )

        return {
            "success": True,
            "dataset": dataset.name,
            "trained_model": trained.model_name,
            "arena_result": arena_result,
            "improvement": arena_result.improvement if arena_result else None,
        }

    def run_full_optimization(
        self,
        prompt: str,
        model: str,
        task_type: str,
        n_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Run full optimization loop:
        1. Get current best strategy
        2. Run A/B test with variations
        3. Update genome with winner
        4. Repeat

        Args:
            prompt: Test prompt
            model: Model to optimize
            task_type: Task type
            n_iterations: Number of optimization iterations

        Returns:
            Optimization results
        """
        best_strategy = self.get_best_strategy(model, task_type)

        # Generate variations
        variations = [
            best_strategy,
            best_strategy + ["verify"] if best_strategy else ["scratchpad", "verify"],
            ["scratchpad", "verify"],
            ["planner", "verify"],
        ]

        # Deduplicate
        variations = [list(set(v)) for v in variations]

        all_results = []

        for i in range(n_iterations):
            result = self.run_and_learn(
                prompt=prompt,
                model=model,
                strategies=variations,
                task_type=task_type,
                n_runs=3,
            )

            all_results.append(result)

            # Update best strategy
            winner = result.get("analysis", {}).get("winner", {})
            if winner:
                best_strategy = winner.get("strategy", [])

        return {
            "iterations": n_iterations,
            "final_best": best_strategy,
            "results": all_results,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            "sync_stats": self.sync_stats,
            "genome_records": len(getattr(self.promptos.genome, "genome", [])),
            "farming_stats": self.forge.farming.get_stats()
            if self.forge.farming
            else {},
            "evolution_stats": self.promptos.evolution.get_evolution_stats(),
        }


def create_bridge(
    llm_callable: Callable,
    bench_callback: Optional[Callable] = None,
    **kwargs,
) -> PromptOSForgeBridge:
    """
    Create a fully integrated PromptOS + PromptForge system.

    Args:
        llm_callable: LLM callable function
        bench_callback: Optional bench scoring callback
        **kwargs: Additional arguments

    Returns:
        PromptOSForgeBridge instance
    """
    try:
        from PromptOS import PromptOS
    except ImportError:
        # PromptOS is not installed, so return early or raise a runtime exception depending on use case
        # Since this is explicitly designed to bridge both, raising an error or returning a mock is expected.
        raise ImportError("PromptOS is required to create a PromptOSForgeBridge. Please install it.")

    from PromptForge import ForgeEngine

    promptos_keys = {
        "available_tools",
        "dspy_optimize",
        "answer_key_path",
        "genome_path",
        "cache_enabled",
        "cache_ttl",
        "token_budget_enabled",
        "default_token_limit",
    }
    forge_keys = {
        "qdrant_url",
        "qdrant_collection",
        "dashboard_enabled",
        "distillation_enabled",
    }
    promptos_kwargs = {k: v for k, v in kwargs.items() if k in promptos_keys}
    forge_kwargs = {k: v for k, v in kwargs.items() if k in forge_keys}

    # Create PromptOS
    promptos = PromptOS(
        llm_callable=llm_callable,
        bench_callback=bench_callback,
        **promptos_kwargs,
    )

    # Create PromptForge
    forge = ForgeEngine(
        llm_callable=llm_callable,
        bench_callback=bench_callback,
        **forge_kwargs,
    )

    # Connect PromptForge distillation to use the LLM
    if forge.distillation:
        forge.distillation.set_llm_callable(llm_callable, bench_callback)

    # Create bridge
    return PromptOSForgeBridge(promptos, forge)
