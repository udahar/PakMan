#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Qdrant Pipeline - Experiment Data Storage

Stores all A/B test experiments in Qdrant for:
- Semantic search
- Pattern discovery
- Historical analysis
- Knowledge retrieval
"""

import json
import time
import hashlib
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

# Qdrant imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None

# Embedder is loaded lazily to avoid importing heavy Torch/CUDA stacks on startup.
EMBEDDER = None
_EMBEDDER_INIT_ATTEMPTED = False


def _get_embedder():
    global EMBEDDER, _EMBEDDER_INIT_ATTEMPTED
    if _EMBEDDER_INIT_ATTEMPTED:
        return EMBEDDER

    _EMBEDDER_INIT_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer

        EMBEDDER = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("[QdrantPipeline] Using BGE-small embeddings")
    except Exception:
        EMBEDDER = None
        print("[QdrantPipeline] Using fallback hash-based embeddings")
    return EMBEDDER


@dataclass
class ExperimentRecord:
    """An experiment record stored in Qdrant."""

    experiment_id: str
    prompt: str
    prompt_embedding: List[float]
    model: str
    task_type: str
    strategies_tested: List[List[str]]
    winner: Optional[Dict]
    all_results: List[Dict]
    statistical_significance: float
    timestamp: str


class QdrantPipeline:
    """
    Qdrant pipeline for experiment storage.

    Features:
    - Semantic search
    - Pattern discovery
    - Export/import
    - Local fallback
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection: str = "promptforge_experiments",
        storage_path: Optional[str] = None,
    ):
        """
        Initialize Qdrant pipeline.

        Args:
            qdrant_url: Qdrant server URL
            collection: Collection name
            storage_path: Local storage path (fallback)
        """
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.storage_path = storage_path or "PromptForge/experiments.json"
        self.db_only = str(os.getenv("PROMPTFORGE_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self.qdrant_client = None

        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(
                    url=qdrant_url, check_compatibility=False
                )
                self._ensure_collection()
            except Exception as e:
                print(f"[QdrantPipeline] Connection failed: {e}")

        # Local cache
        self.experiments: List[ExperimentRecord] = []

        # Load existing data
        self._load()

    def _ensure_collection(self):
        """Ensure Qdrant collection exists."""
        if not self.qdrant_client:
            return

        try:
            if not self.qdrant_client.collection_exists(self.collection):
                self.qdrant_client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                print(f"[QdrantPipeline] Created collection: {self.collection}")
        except Exception as e:
            print(f"[QdrantPipeline] Failed to create collection: {e}")

    def store_experiment(
        self,
        prompt: str,
        model: str,
        task_type: str,
        strategies_tested: List[List[str]],
        winner: Optional[Dict],
        all_results: List[Dict],
        statistical_significance: float = 0.5,
    ) -> str:
        """
        Store experiment in Qdrant.

        Args:
            prompt: Test prompt
            model: Model used
            task_type: Task type
            strategies_tested: Strategies tested
            winner: Winning strategy
            all_results: All test results
            statistical_significance: Statistical significance

        Returns:
            Experiment ID
        """
        # Create experiment ID
        experiment_id = hashlib.sha256(
            f"{prompt}{model}{time.time()}".encode()
        ).hexdigest()[:16]

        # Create embedding (placeholder - use real embeddings in production)
        prompt_embedding = self._simple_embedding(prompt)

        # Create record
        record = ExperimentRecord(
            experiment_id=experiment_id,
            prompt=prompt,
            prompt_embedding=prompt_embedding,
            model=model,
            task_type=task_type,
            strategies_tested=strategies_tested,
            winner=winner,
            all_results=[
                asdict(r) if hasattr(r, "__dataclass_fields__") else r
                for r in all_results
            ],
            statistical_significance=statistical_significance,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Store in Qdrant
        if self.qdrant_client:
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection,
                    points=[
                        PointStruct(
                            id=hash(experiment_id) % (2**63),
                            vector=prompt_embedding,
                            payload=asdict(record),
                        )
                    ],
                )
            except Exception as e:
                print(f"[QdrantPipeline] Qdrant store failed: {e}")
                # Fallback to local storage
                self.experiments.append(record)
        else:
            # Fallback to local storage
            self.experiments.append(record)

        # Auto-save
        if len(self.experiments) % 50 == 0:
            self._save()

        return experiment_id

    def search_similar_experiments(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar experiments.

        Args:
            prompt: Query prompt
            task_type: Optional task type filter
            limit: Max results

        Returns:
            List of similar experiments
        """
        query_embedding = self._simple_embedding(prompt)

        results = []

        # Search Qdrant
        if self.qdrant_client:
            try:
                search_filter = None
                if task_type:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue

                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key="task_type",
                                match=MatchValue(value=task_type),
                            )
                        ]
                    )

                qdrant_results = self.qdrant_client.query_points(
                    collection_name=self.collection,
                    query=query_embedding,
                    query_filter=search_filter,
                    limit=limit,
                )

                for point in qdrant_results.points:
                    results.append(
                        {
                            "experiment_id": point.payload.get("experiment_id"),
                            "prompt": point.payload.get("prompt"),
                            "winner": point.payload.get("winner"),
                            "similarity": point.score,
                            "model": point.payload.get("model"),
                            "task_type": point.payload.get("task_type"),
                        }
                    )
            except Exception as e:
                print(f"[QdrantPipeline] Search failed: {e}")

        # Fallback to local search
        if not results:
            results = self._search_local(query_embedding, task_type, limit)

        return results

    def _search_local(
        self,
        query_embedding: List[float],
        task_type: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search local cache for similar experiments."""
        candidates = self.experiments

        if task_type:
            candidates = [exp for exp in candidates if exp.task_type == task_type]

        if not candidates:
            return []

        # Calculate similarities
        similarities = []

        for exp in candidates:
            similarity = self._cosine_similarity(query_embedding, exp.prompt_embedding)
            similarities.append((exp, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top results
        return [
            {
                "experiment_id": exp.experiment_id,
                "prompt": exp.prompt,
                "winner": exp.winner,
                "similarity": sim,
                "model": exp.model,
                "task_type": exp.task_type,
            }
            for exp, sim in similarities[:limit]
        ]

    def get_experiment_patterns(self, task_type: str) -> Dict[str, Any]:
        """
        Discover patterns in experiments for a task type.

        Args:
            task_type: Task type

        Returns:
            Pattern analysis
        """
        # Filter by task type
        if self.qdrant_client:
            # Would query Qdrant in production
            pass

        experiments = [exp for exp in self.experiments if exp.task_type == task_type]

        if not experiments:
            return {}

        # Count strategy wins
        strategy_wins = {}

        for exp in experiments:
            if exp.winner:
                winner_strategy = ",".join(sorted(exp.winner.get("strategy", [])))
                strategy_wins[winner_strategy] = (
                    strategy_wins.get(winner_strategy, 0) + 1
                )

        # Calculate win rates
        total = sum(strategy_wins.values())
        win_rates = {strategy: wins / total for strategy, wins in strategy_wins.items()}

        return {
            "total_experiments": len(experiments),
            "strategy_win_rates": win_rates,
            "best_strategy": max(win_rates, key=win_rates.get) if win_rates else None,
        }

    def _simple_embedding(self, text: str) -> List[float]:
        """Generate real semantic embedding."""
        embedder = _get_embedder()
        if embedder:
            return embedder.encode(text, convert_to_numpy=True).tolist()

        # Fallback to hash-based if embedder not available
        hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        return [(hash_val >> i) & 1 for i in range(384)]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def export_data(self, path: Optional[str] = None) -> str:
        """Export all experiment data to JSON."""
        export_path = path or self.storage_path

        data = {
            "experiments": [asdict(exp) for exp in self.experiments],
            "exported_at": time.time(),
        }

        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return export_path

    def import_data(self, path: str) -> int:
        """Import experiment data from JSON."""
        with open(path, "r") as f:
            data = json.load(f)

        imported = 0

        for exp_data in data.get("experiments", []):
            try:
                exp = ExperimentRecord(**exp_data)
                self.experiments.append(exp)
                imported += 1
            except Exception:
                pass

        print(f"[QdrantPipeline] Imported {imported} experiments")
        return imported

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        if self.qdrant_client:
            try:
                info = self.qdrant_client.get_collection(self.collection)
                return {
                    "total_experiments": info.points_count,
                    "collection": self.collection,
                    "qdrant_url": self.qdrant_url,
                }
            except Exception:
                pass

        return {
            "total_experiments": len(self.experiments),
            "storage": "local",
        }

    def _save(self):
        """Save experiments to local storage."""
        if self.db_only:
            return
        self.export_data()

    def _load(self):
        """Load experiments from local storage."""
        if self.db_only:
            return
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                self.experiments = [
                    ExperimentRecord(**exp_data)
                    for exp_data in data.get("experiments", [])
                ]

                print(f"[QdrantPipeline] Loaded {len(self.experiments)} experiments")
        except Exception as e:
            print(f"[QdrantPipeline] Load failed: {e}")
