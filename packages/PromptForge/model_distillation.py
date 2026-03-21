"""
Model Distillation Engine - Train Models on Discovered Strategies

Distills successful reasoning strategies into model weights.
Tests trained vs untrained models in the arena.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .ollama_integration import OllamaClient


@dataclass
class DistillationDataset:
    """A dataset for model distillation."""

    name: str
    task_type: str
    strategies_included: List[str]
    num_examples: int
    avg_score: float
    created_at: str
    path: str


@dataclass
class TrainedModel:
    """A distilled/trained model."""

    model_name: str
    base_model: str
    dataset_name: str
    strategies_distilled: List[str]
    training_examples: int
    avg_improvement: float
    created_at: str
    path: Optional[str]


@dataclass
class ArenaTestResult:
    """Result from arena testing of trained model."""

    trained_model: str
    untrained_model: str
    trained_wins: int
    untrained_wins: int
    total_tests: int
    improvement: float
    test_prompts: List[str]
    timestamp: str


class ModelDistillationEngine:
    """
    Model distillation engine for training models on discovered strategies.

    Features:
    - Prepare training datasets from successful strategies
    - Train models on distilled strategies
    - Test trained vs untrained in arena
    - Track improvement over time
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        training_data_path: str = "PromptForge/distillation_data/",
        models_path: str = "PromptForge/trained_models/",
        ollama_url: str = "http://localhost:11434",
    ):
        """
        Initialize distillation engine.

        Args:
            qdrant_url: Qdrant server URL
            training_data_path: Path for training datasets
            models_path: Path for trained models
            ollama_url: Ollama server URL
        """
        self.qdrant_url = qdrant_url
        self.training_data_path = training_data_path
        self.models_path = models_path
        self.ollama_url = ollama_url

        # Initialize Ollama client
        self.ollama = OllamaClient(
            base_url=ollama_url,
            training_data_path=training_data_path,
        )

        # Ensure directories exist
        Path(training_data_path).mkdir(parents=True, exist_ok=True)
        Path(models_path).mkdir(parents=True, exist_ok=True)

        # Track datasets and models
        self.datasets: List[DistillationDataset] = []
        self.trained_models: List[TrainedModel] = []

        # Arena test history
        self.arena_tests: List[ArenaTestResult] = []

        # LLM callable for arena testing
        self.llm_callable: Optional[Callable] = None
        self.bench_callback: Optional[Callable] = None

        # Load existing data
        self._load()

    def set_llm_callable(
        self, llm_callable: Callable, bench_callback: Optional[Callable] = None
    ):
        """Set LLM callable for arena testing."""
        self.llm_callable = llm_callable
        self.bench_callback = bench_callback

    def prepare_training_dataset(
        self,
        task_type: str,
        min_score: float = 0.8,
        strategies: Optional[List[str]] = None,
        max_examples: int = 1000,
    ) -> DistillationDataset:
        """
        Prepare training dataset from successful strategies.

        Args:
            task_type: Task type to focus on
            min_score: Minimum score threshold
            strategies: Specific strategies to include
            max_examples: Maximum examples to include

        Returns:
            DistillationDataset
        """
        # Load successful strategies from PromptForge
        farming_path = f"{self.training_data_path}../strategy_farming.json"

        successes = []
        if Path(farming_path).exists():
            with open(farming_path, "r") as f:
                farming_data = json.load(f)
                successes = farming_data.get("successes", [])

        # Filter by criteria
        filtered = [
            s
            for s in successes
            if s.get("task_type") == task_type
            and s.get("score", 0) >= min_score
            and (
                strategies is None
                or ",".join(sorted(s.get("strategy", []))) in strategies
            )
        ]

        # Limit examples
        filtered = filtered[:max_examples]

        # Calculate average score
        avg_score = (
            sum(s.get("score", 0) for s in filtered) / len(filtered) if filtered else 0
        )

        # Create dataset
        dataset_name = (
            f"{task_type}_distilled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        dataset_path = f"{self.training_data_path}{dataset_name}.json"

        # Save dataset
        dataset = DistillationDataset(
            name=dataset_name,
            task_type=task_type,
            strategies_included=list(
                set(",".join(sorted(s.get("strategy", []))) for s in filtered)
            ),
            num_examples=len(filtered),
            avg_score=avg_score,
            created_at=datetime.now().isoformat(),
            path=dataset_path,
        )

        # Save to file
        with open(dataset_path, "w") as f:
            json.dump(
                {
                    "dataset_info": asdict(dataset),
                    "examples": filtered,
                },
                f,
                indent=2,
            )

        self.datasets.append(dataset)

        print(f"[Distillation] Created dataset: {dataset_name}")
        print(f"  Examples: {len(filtered)}")
        print(f"  Avg score: {avg_score:.2f}")
        print(f"  Strategies: {dataset.strategies_included}")

        return dataset

    def train_model(
        self,
        base_model: str,
        dataset: DistillationDataset,
        output_model: Optional[str] = None,
        training_method: str = "supervised",
    ) -> TrainedModel:
        """
        Train model on distilled strategies.

        Args:
            base_model: Base model to fine-tune
            dataset: Training dataset
            output_model: Output model name
            training_method: Training method (supervised, DPO, etc.)

        Returns:
            TrainedModel
        """
        if output_model is None:
            output_model = f"{base_model}-distilled-{dataset.task_type}"

        # Load training examples from dataset
        dataset_path = Path(dataset.path)
        if dataset_path.exists():
            with open(dataset_path, "r") as f:
                data = json.load(f)
                training_examples = data.get("examples", [])
        else:
            training_examples = []

        # Try to use Ollama for model creation
        success = False
        if self.ollama.is_available():
            # Create model using Ollama with custom system prompt
            success = self.ollama.create_model(
                name=output_model,
                base_model=base_model,
                training_data=training_examples,
                force=True,
            )

        # If Ollama not available or failed, create placeholder model
        if not success:
            print(f"[Distillation] Ollama not available, creating placeholder model")
            output_model = f"{output_model}-placeholder"

        trained_model = TrainedModel(
            model_name=output_model,
            base_model=base_model,
            dataset_name=dataset.name,
            strategies_distilled=dataset.strategies_included,
            training_examples=dataset.num_examples,
            avg_improvement=0.0,  # Will be measured in arena
            created_at=datetime.now().isoformat(),
            path=f"{self.models_path}{output_model}/",
        )

        # Save model metadata
        model_metadata_path = Path(self.models_path) / output_model / "metadata.json"
        model_metadata_path.parent.mkdir(parents=True, exist_ok=True)

        with open(model_metadata_path, "w") as f:
            json.dump(asdict(trained_model), f, indent=2)

        self.trained_models.append(trained_model)

        print(f"[Distillation] Trained model: {output_model}")
        print(f"  Base model: {base_model}")
        print(f"  Dataset: {dataset.name}")
        print(f"  Examples: {dataset.num_examples}")

        return trained_model

    def test_in_arena(
        self,
        trained_model: str,
        untrained_model: str,
        test_prompts: List[str],
        task_type: str = "general",
        n_runs: int = 3,
    ) -> ArenaTestResult:
        """
        Test trained model against untrained model in arena.

        Args:
            trained_model: Trained model name
            untrained_model: Untrained model name (control)
            test_prompts: List of test prompts
            task_type: Task type
            n_runs: Number of runs per prompt

        Returns:
            ArenaTestResult
        """
        trained_wins = 0
        untrained_wins = 0
        ties = 0

        # Check if Ollama is available
        use_ollama = self.ollama.is_available()

        for prompt in test_prompts:
            # Run both models
            trained_scores = []
            untrained_scores = []

            for _ in range(n_runs):
                trained_response = ""
                untrained_response = ""

                if use_ollama:
                    # Use Ollama for both models
                    trained_response = self.ollama.generate(trained_model, prompt)
                    untrained_response = self.ollama.generate(untrained_model, prompt)
                elif self.llm_callable:
                    # Use provided LLM callable
                    trained_response = self.llm_callable(prompt, model=trained_model)
                    untrained_response = self.llm_callable(
                        prompt, model=untrained_model
                    )

                # Score responses
                trained_score = self._score_response(trained_response, prompt)
                untrained_score = self._score_response(untrained_response, prompt)

                trained_scores.append(trained_score)
                untrained_scores.append(untrained_score)

            # Determine winner for this prompt
            avg_trained = sum(trained_scores) / len(trained_scores)
            avg_untrained = sum(untrained_scores) / len(untrained_scores)

            if avg_trained > avg_untrained + 0.05:  # 5% margin
                trained_wins += 1
            elif avg_untrained > avg_trained + 0.05:
                untrained_wins += 1
            else:
                ties += 1

        total_tests = len(test_prompts)
        if total_tests == 0:
            improvement = 0.0
        else:
            improvement = (trained_wins - untrained_wins) / total_tests

        result = ArenaTestResult(
            trained_model=trained_model,
            untrained_model=untrained_model,
            trained_wins=trained_wins,
            untrained_wins=untrained_wins,
            total_tests=total_tests,
            improvement=improvement,
            test_prompts=test_prompts,
            timestamp=datetime.now().isoformat(),
        )

        self.arena_tests.append(result)

        # Update trained model with improvement
        for model in self.trained_models:
            if model.model_name == trained_model:
                model.avg_improvement = improvement
                break

        print(f"[Arena] Test complete: {trained_model} vs {untrained_model}")
        print(
            f"  Trained wins: {trained_wins}, Untrained wins: {untrained_wins}, Ties: {ties}"
        )
        print(f"  Improvement: {improvement:+.1%}")

        return result

    def _score_response(self, response: str, prompt: str) -> float:
        """Score a response using heuristics or callback."""
        if self.bench_callback:
            return self.bench_callback(response, prompt)

        # Fallback scoring
        score = 0.5

        # Length check
        if 100 < len(response) < 3000:
            score += 0.1

        # Contains reasoning indicators
        reasoning_words = ["step", "therefore", "because", "thus", "hence"]
        if any(word in response.lower() for word in reasoning_words):
            score += 0.15

        # Contains solution
        if "answer" in response.lower() or "solution" in response.lower():
            score += 0.1

        return min(1.0, score)

        # Update trained model with improvement
        for model in self.trained_models:
            if model.model_name == trained_model:
                model.avg_improvement = improvement
                break

        print(f"[Arena] Test complete: {trained_model} vs {untrained_model}")
        print(f"  Trained wins: {trained_wins}/{total_tests}")
        print(f"  Untrained wins: {untrained_wins}/{total_tests}")
        print(f"  Improvement: {improvement:+.1%}")

        return result

    def get_canary_models(self) -> List[TrainedModel]:
        """
        Get list of canary models for testing.

        Returns:
            List of canary models
        """
        # Return models marked as canaries
        # For now, return all trained models
        return self.trained_models

    def export_training_data(self, path: Optional[str] = None) -> str:
        """Export all training data to JSON."""
        export_path = path or f"{self.training_data_path}all_datasets.json"

        data = {
            "datasets": [asdict(d) for d in self.datasets],
            "trained_models": [asdict(m) for m in self.trained_models],
            "arena_tests": [asdict(t) for t in self.arena_tests],
            "exported_at": time.time(),
        }

        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return export_path

    def import_training_data(self, path: str) -> int:
        """Import training data from JSON."""
        with open(path, "r") as f:
            data = json.load(f)

        imported = 0

        # Import datasets
        for d_data in data.get("datasets", []):
            try:
                dataset = DistillationDataset(**d_data)
                self.datasets.append(dataset)
                imported += 1
            except Exception:
                pass

        # Import trained models
        for m_data in data.get("trained_models", []):
            try:
                model = TrainedModel(**m_data)
                self.trained_models.append(model)
                imported += 1
            except Exception:
                pass

        print(f"[Distillation] Imported {imported} items")
        return imported

    def get_stats(self) -> Dict[str, Any]:
        """Get distillation statistics."""
        return {
            "total_datasets": len(self.datasets),
            "total_trained_models": len(self.trained_models),
            "total_arena_tests": len(self.arena_tests),
            "avg_improvement": (
                sum(t.improvement for t in self.arena_tests) / len(self.arena_tests)
                if self.arena_tests
                else 0
            ),
        }

    def _save(self):
        """Save distillation data."""
        self.export_training_data()

    def _load(self):
        """Load distillation data."""
        try:
            all_data_path = f"{self.training_data_path}all_datasets.json"
            if Path(all_data_path).exists():
                with open(all_data_path, "r") as f:
                    data = json.load(f)

                self.datasets = [
                    DistillationDataset(**d) for d in data.get("datasets", [])
                ]
                self.trained_models = [
                    TrainedModel(**m) for m in data.get("trained_models", [])
                ]
                self.arena_tests = [
                    ArenaTestResult(**t) for t in data.get("arena_tests", [])
                ]

                print(
                    f"[Distillation] Loaded {len(self.datasets)} datasets, {len(self.trained_models)} models"
                )
        except Exception as e:
            print(f"[Distillation] Load failed: {e}")
