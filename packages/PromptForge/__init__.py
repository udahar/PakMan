"""
PromptForge - Strategy Experimentation Engine

Parallel A/B testing, statistical analysis, and strategy evolution.
This is the "hammer" that forges better reasoning strategies.

Usage:
    from PromptForge import ForgeEngine

    forge = ForgeEngine(
        llm_callable=llm,
        bench_callback=bench_score,
        qdrant_url="http://localhost:6333"
    )

    # Run A/B test
    result = forge.ab_test(
        prompt="Debug this error",
        model="qwen2.5:7b",
        strategies=[
            ["scratchpad", "verify"],
            ["decompose", "scratchpad"],
            ["planner", "verify"]
        ],
        n_runs=10
    )

    print(f"Winner: {result['winner']}")
    print(f"Confidence: {result['confidence']:.1%}")
"""

from .ab_testing import ABTestingEngine, ABTestResult, ABTestReport
from .qdrant_pipeline import QdrantPipeline, ExperimentRecord
from .strategy_farming import StrategyFarming, SuccessRecord, FailureRecord
from .dashboard_integration import ForgeDashboard
from .model_distillation import (
    ModelDistillationEngine,
    DistillationDataset,
    TrainedModel,
    ArenaTestResult,
)
from .strategy_graph import StrategyGraph, StrategyGraphBuilder, ReasoningStep
from .training_data_generator import TrainingDataGenerator, TrainingExample, DPOExample
from .ollama_integration import OllamaClient, create_training_jsonl
from .bridge import PromptOSForgeBridge, create_bridge

__all__ = [
    "ForgeEngine",
    "ABTestingEngine",
    "ABTestResult",
    "ABTestReport",
    "QdrantPipeline",
    "ExperimentRecord",
    "StrategyFarming",
    "SuccessRecord",
    "FailureRecord",
    "ForgeDashboard",
    "ModelDistillationEngine",
    "DistillationDataset",
    "TrainedModel",
    "ArenaTestResult",
    "StrategyGraph",
    "StrategyGraphBuilder",
    "ReasoningStep",
    "TrainingDataGenerator",
    "TrainingExample",
    "DPOExample",
    "OllamaClient",
    "create_training_jsonl",
    "PromptOSForgeBridge",
    "create_bridge",
]

__version__ = "1.0.0"


class ForgeEngine:
    """
    Unified PromptForge experimentation engine.

    Combines:
    - A/B Testing (parallel execution)
    - Qdrant Pipeline (data storage)
    - Strategy Farming (positive/negative learning)
    - Dashboard Integration (real-time monitoring)
    - Model Distillation (train models on strategies)
    """

    def __init__(
        self,
        llm_callable: callable,
        bench_callback: callable = None,
        qdrant_url: str = "http://localhost:6333",
        qdrant_collection: str = "promptforge_experiments",
        dashboard_enabled: bool = True,
        distillation_enabled: bool = True,
    ):
        """
        Initialize Forge Engine.

        Args:
            llm_callable: LLM callable function
            bench_callback: Bench scoring callback
            qdrant_url: Qdrant server URL
            qdrant_collection: Qdrant collection name
            dashboard_enabled: Enable dashboard integration
            distillation_enabled: Enable model distillation
        """
        self.llm_callable = llm_callable
        self.bench_callback = bench_callback

        # Initialize components
        self.ab_testing = ABTestingEngine(
            llm_callable=llm_callable, bench_callback=bench_callback
        )

        self.qdrant = QdrantPipeline(
            qdrant_url=qdrant_url, collection=qdrant_collection
        )

        self.farming = StrategyFarming()

        self.dashboard = ForgeDashboard() if dashboard_enabled else None

        self.distillation = (
            ModelDistillationEngine(qdrant_url=qdrant_url)
            if distillation_enabled
            else None
        )

        # Experiment history
        self.experiments_run = 0

    def ab_test(
        self,
        prompt: str,
        model: str,
        strategies: list,
        task_type: str = None,
        n_runs: int = 5,
        timeout_seconds: int = 60,
        store_in_qdrant: bool = True,
    ) -> dict:
        """
        Run A/B test of multiple strategies.

        Args:
            prompt: Test prompt
            model: Model to test with
            strategies: List of strategy combinations
            task_type: Task type (auto-detected if None)
            n_runs: Number of runs per strategy
            timeout_seconds: Timeout per run
            store_in_qdrant: Store results in Qdrant

        Returns:
            Test results with statistics
        """
        # Run A/B test
        result = self.ab_testing.ab_test(
            prompt=prompt,
            model=model,
            strategies=strategies,
            task_type=task_type,
            n_runs=n_runs,
            timeout_seconds=timeout_seconds,
        )

        # Store in Qdrant
        if store_in_qdrant:
            self.qdrant.store_experiment(
                prompt=prompt,
                model=model,
                task_type=result.get("task_type", "unknown"),
                strategies_tested=strategies,
                winner=result.get("analysis", {}).get("winner", {}),
                all_results=result.get("results", []),
            )

        # Update strategy farming
        winner = result.get("analysis", {}).get("winner")
        if winner:
            self.farming.record_success(
                model=model,
                task_type=result.get("task_type", "unknown"),
                strategy=winner.get("strategy", []),
                score=winner.get("fitness", 0),
            )

            # Record failures for losers
            for strategy_result in (
                result.get("analysis", {}).get("by_strategy", {}).values()
            ):
                if strategy_result != winner:
                    self.farming.record_failure(
                        model=model,
                        task_type=result.get("task_type", "unknown"),
                        strategy=strategy_result.get("strategy", []),
                        failure_mode="outperformed",
                    )

        # Log to dashboard
        if self.dashboard:
            self.dashboard.log_experiment(result)

        # Increment counter
        self.experiments_run += 1

        return result

    def batch_test(
        self,
        test_prompts: list,
        model: str,
        strategies: list,
        task_type: str = None,
        parallel: bool = True,
    ) -> dict:
        """
        Run batch A/B tests across multiple prompts.

        Args:
            test_prompts: List of test prompts
            model: Model to test with
            strategies: List of strategies
            task_type: Task type
            parallel: Run in parallel

        Returns:
            Aggregated results
        """
        results = []

        for prompt in test_prompts:
            result = self.ab_test(
                prompt=prompt,
                model=model,
                strategies=strategies,
                task_type=task_type,
                n_runs=3,  # Fewer runs for batch
                store_in_qdrant=True,
            )
            results.append(result)

        # Aggregate results
        return self._aggregate_results(results)

    def _aggregate_results(self, results: list) -> dict:
        """Aggregate multiple A/B test results."""
        if not results:
            return {}

        # Count strategy wins
        strategy_wins = {}
        total_tests = len(results)

        for result in results:
            winner = result.get("analysis", {}).get("winner")
            if winner:
                strategy_key = ",".join(sorted(winner.get("strategy", [])))
                strategy_wins[strategy_key] = strategy_wins.get(strategy_key, 0) + 1

        # Calculate win rates
        win_rates = {
            strategy: wins / total_tests for strategy, wins in strategy_wins.items()
        }

        return {
            "total_tests": total_tests,
            "strategy_win_rates": win_rates,
            "best_strategy": max(win_rates, key=win_rates.get) if win_rates else None,
            "individual_results": results,
        }

    def get_best_strategy(
        self,
        model: str,
        task_type: str,
        min_trials: int = 3,
    ) -> list:
        """
        Get best strategy for model/task from farming data.

        Args:
            model: Model name
            task_type: Task type
            min_trials: Minimum trials required

        Returns:
            Best strategy modules
        """
        return self.farming.get_best_strategy(model, task_type, min_trials)

    def get_experiment_stats(self) -> dict:
        """Get experiment statistics."""
        return {
            "experiments_run": self.experiments_run,
            "ab_testing_stats": self.ab_testing.get_stats(),
            "qdrant_stats": self.qdrant.get_stats(),
            "farming_stats": self.farming.get_stats(),
            "dashboard_active": self.dashboard is not None,
        }

    def export_results(self, path: str) -> str:
        """Export all experiment results to JSON."""
        return self.qdrant.export_data(path)

    def import_results(self, path: str) -> int:
        """Import experiment results from JSON."""
        return self.qdrant.import_data(path)
