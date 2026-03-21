"""
Strategy Embeddings - Experience-Driven Reasoning

Stores prompt embeddings with strategies in Qdrant.
Retrieves best strategies for similar problems via nearest-neighbor search.

Usage:
    from PromptOS.strategy_embeddings import StrategyEmbeddings

    embeddings = StrategyEmbeddings(
        qdrant_url="http://localhost:6333",
        collection="strategy_embeddings"
    )

    # Store experience
    embeddings.store_experience(
        prompt="Debug this crash",
        strategy=["scratchpad", "verify"],
        score=0.95,
        model="qwen2.5:7b",
        task_type="debugging"
    )

    # Retrieve best strategy for similar problem
    similar = embeddings.retrieve_best_strategy(
        prompt="Fix this IndexError",
        model="qwen2.5:7b",
        task_type="debugging"
    )

    print(f"Best strategy: {similar['strategy']}")
    print(f"Similarity: {similar['similarity']:.2f}")
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

# Qdrant imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        Range,
    )

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None


@dataclass
class StrategyExperience:
    """A stored strategy experience."""

    prompt: str
    prompt_embedding: List[float]
    strategy: List[str]
    score: float
    model: str
    task_type: str
    timestamp: float
    tokens_used: int = 0
    success: bool = True


class StrategyEmbeddings:
    """
    Strategy embeddings for experience-driven reasoning.

    Stores prompt embeddings with strategies in Qdrant.
    Retrieves best strategies for similar problems via nearest-neighbor search.
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection: str = "strategy_embeddings",
        embedding_model: Optional[str] = None,
    ):
        """
        Initialize strategy embeddings.

        Args:
            qdrant_url: Qdrant server URL
            collection: Collection name
            embedding_model: Embedding model (uses simple hash if None)
        """
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.embedding_model = embedding_model

        self.qdrant_client = None

        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(
                    url=qdrant_url, check_compatibility=False
                )
                self._ensure_collection()
            except Exception as e:
                print(f"[StrategyEmbeddings] Qdrant connection failed: {e}")

        # Experience cache
        self.experiences: List[StrategyExperience] = []

        # Storage path for local fallback
        self.storage_path = f"PromptOS/{collection}.json"

        # Load existing experiences
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
                print(f"[StrategyEmbeddings] Created collection: {self.collection}")
        except Exception as e:
            print(f"[StrategyEmbeddings] Failed to create collection: {e}")

    def store_experience(
        self,
        prompt: str,
        strategy: List[str],
        score: float,
        model: str,
        task_type: str,
        tokens_used: int = 0,
        success: bool = True,
    ) -> str:
        """
        Store a strategy experience.

        Args:
            prompt: Input prompt
            strategy: Strategy modules used
            score: Bench score
            model: Model name
            task_type: Task type
            tokens_used: Token count
            success: Whether it succeeded

        Returns:
            Experience ID
        """
        # Create prompt embedding
        prompt_embedding = self._embed_prompt(prompt)

        # Create experience
        experience = StrategyExperience(
            prompt=prompt,
            prompt_embedding=prompt_embedding,
            strategy=strategy,
            score=score,
            model=model,
            task_type=task_type,
            timestamp=time.time(),
            tokens_used=tokens_used,
            success=success,
        )

        # Store in Qdrant
        if self.qdrant_client:
            try:
                experience_id = hash(f"{prompt}{time.time()}") % (2**63)

                self.qdrant_client.upsert(
                    collection_name=self.collection,
                    points=[
                        PointStruct(
                            id=experience_id,
                            vector=prompt_embedding,
                            payload={
                                "prompt": prompt,
                                "strategy": strategy,
                                "score": score,
                                "model": model,
                                "task_type": task_type,
                                "tokens_used": tokens_used,
                                "success": success,
                                "timestamp": experience.timestamp,
                            },
                        )
                    ],
                )
            except Exception as e:
                print(f"[StrategyEmbeddings] Qdrant store failed: {e}")
                # Fallback to local storage
                self.experiences.append(experience)
        else:
            # Fallback to local storage
            self.experiences.append(experience)

        # Auto-save
        if len(self.experiences) % 100 == 0:
            self._save()

        return str(experience_id)

    def retrieve_best_strategy(
        self,
        prompt: str,
        model: str,
        task_type: str,
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve best strategy for a similar problem.

        Args:
            prompt: Input prompt
            model: Model name
            task_type: Task type
            limit: Max results to return
            min_similarity: Minimum similarity threshold

        Returns:
            Best strategy info or None
        """
        # Create query embedding
        query_embedding = self._embed_prompt(prompt)

        # Search Qdrant
        if self.qdrant_client:
            try:
                # Build filter for model and task type
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="task_type",
                            match=MatchValue(value=task_type),
                        ),
                        FieldCondition(
                            key="score",
                            match=Range(gte=0.7),  # Only successful experiences
                        ),
                    ]
                )

                # Search
                results = self.qdrant_client.query_points(
                    collection_name=self.collection,
                    query=query_embedding,
                    query_filter=search_filter,
                    limit=limit,
                )

                if results.points:
                    # Return best match
                    best = results.points[0]
                    return {
                        "strategy": best.payload["strategy"],
                        "score": best.payload["score"],
                        "similarity": best.score,
                        "prompt": best.payload["prompt"],
                        "model": best.payload["model"],
                    }
            except Exception as e:
                print(f"[StrategyEmbeddings] Qdrant search failed: {e}")

        # Fallback to local search
        return self._retrieve_local_best(
            query_embedding, model, task_type, limit, min_similarity
        )

    def _retrieve_local_best(
        self,
        query_embedding: List[float],
        model: str,
        task_type: str,
        limit: int,
        min_similarity: float,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve best strategy from local cache."""
        # Filter by task type and score
        candidates = [
            exp
            for exp in self.experiences
            if exp.task_type == task_type and exp.score >= 0.7
        ]

        if not candidates:
            return None

        # Calculate similarities
        similarities = []

        for exp in candidates:
            similarity = self._cosine_similarity(query_embedding, exp.prompt_embedding)
            if similarity >= min_similarity:
                similarities.append((exp, similarity))

        if not similarities:
            return None

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return best
        best_exp, best_sim = similarities[0]

        return {
            "strategy": best_exp.strategy,
            "score": best_exp.score,
            "similarity": best_sim,
            "prompt": best_exp.prompt,
            "model": best_exp.model,
        }

    def search_similar_experiences(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar experiences.

        Args:
            prompt: Input prompt
            task_type: Optional task type filter
            limit: Max results

        Returns:
            List of similar experiences
        """
        query_embedding = self._embed_prompt(prompt)

        results = []

        # Search Qdrant
        if self.qdrant_client:
            try:
                search_filter = None
                if task_type:
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
                            "prompt": point.payload["prompt"],
                            "strategy": point.payload["strategy"],
                            "score": point.payload["score"],
                            "similarity": point.score,
                            "model": point.payload["model"],
                            "task_type": point.payload["task_type"],
                        }
                    )
            except Exception as e:
                print(f"[StrategyEmbeddings] Qdrant search failed: {e}")

        # Fallback to local
        if not results:
            results = self._search_local_similar(query_embedding, task_type, limit)

        return results

    def _search_local_similar(
        self,
        query_embedding: List[float],
        task_type: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search local cache for similar experiences."""
        candidates = self.experiences

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
                "prompt": exp.prompt,
                "strategy": exp.strategy,
                "score": exp.score,
                "similarity": sim,
                "model": exp.model,
                "task_type": exp.task_type,
            }
            for exp, sim in similarities[:limit]
        ]

    def _embed_prompt(self, prompt: str) -> List[float]:
        """Create embedding for prompt."""
        # If embedding model available, use it
        if self.embedding_model:
            # Would use real embedding model here
            pass

        # Fallback to hash-based embedding
        return self._simple_embedding(prompt)

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding (384-dim)."""
        hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        return [(hash_val >> i) & 1 for i in range(384)]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        if self.qdrant_client:
            try:
                info = self.qdrant_client.get_collection(self.collection)
                return {
                    "total_experiences": info.points_count,
                    "collection": self.collection,
                    "qdrant_url": self.qdrant_url,
                }
            except Exception:
                pass

        return {
            "total_experiences": len(self.experiences),
            "storage": "local",
        }

    def _save(self):
        """Save experiences to local storage."""
        try:
            data = {
                "experiences": [asdict(exp) for exp in self.experiences[-1000:]],
                "saved_at": time.time(),
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[StrategyEmbeddings] Save failed: {e}")

    def _load(self):
        """Load experiences from local storage."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                self.experiences = [
                    StrategyExperience(**exp_data)
                    for exp_data in data.get("experiences", [])
                ]

                print(
                    f"[StrategyEmbeddings] Loaded {len(self.experiences)} experiences"
                )
        except Exception as e:
            print(f"[StrategyEmbeddings] Load failed: {e}")
