#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
PostgreSQL + Qdrant Storage for PromptOS/PromptForge

Integrates with Frank's existing database infrastructure.
"""

import os
import json
import socket
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


def _is_port_open(host: str, port: int, timeout: float = 0.6) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _discover_wsl_windows_host() -> Optional[str]:
    # Explicit override first
    override = os.getenv("WSL_WINDOWS_DB_HOST")
    if override:
        return override

    # Then try default gateway from `ip route`
    try:
        route = subprocess.check_output(
            ["ip", "route", "show", "default"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if route:
            parts = route.split()
            if "via" in parts:
                idx = parts.index("via")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    except Exception:
        pass

    # Then try /etc/resolv.conf nameserver
    try:
        with open("/etc/resolv.conf", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and parts[0] == "nameserver":
                    return parts[1]
    except Exception:
        pass
    return None


def get_postgres_url() -> str:
    """Get PostgreSQL URL from environment with WSL->Windows host fallback."""
    explicit = os.getenv("POSTGRES_URL")
    if explicit:
        return explicit

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "REDACTED")
    database = os.getenv("POSTGRES_DB", "zolapress")
    host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
    port = int(os.getenv("POSTGRES_PORT", "5432"))

    # If localhost is unavailable in WSL, transparently target Windows Postgres host.
    if host in {"localhost", "127.0.0.1"} and not _is_port_open(host, port):
        wsl_host = _discover_wsl_windows_host()
        if wsl_host and _is_port_open(wsl_host, port):
            host = wsl_host

    return f"postgresql://{user}:REDACTED@{host}:{port}/{database}"


def get_qdrant_url() -> str:
    """Get Qdrant URL from environment or use Frank default."""
    return os.getenv("QDRANT_URL", "http://localhost:6333")


class PostgresStorage:
    """
    PostgreSQL storage for PromptOS/PromptForge data.

    Uses Frank's existing database infrastructure.
    """

    def __init__(self, postgres_url: Optional[str] = None):
        self.postgres_url = postgres_url or get_postgres_url()
        self._conn = None
        self._cursor = None

    def connect(self):
        """Connect to PostgreSQL."""
        try:
            import psycopg2

            self._conn = psycopg2.connect(self.postgres_url)
            self._cursor = self._conn.cursor()
            self._ensure_tables()
            print("[PostgreSQL] Connected successfully")
        except ImportError:
            print("[PostgreSQL] psycopg2 not available, using fallback")
        except Exception as e:
            print(f"[PostgreSQL] Connection failed: {e}")
            print("[PostgreSQL] Using JSON fallback")

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        if not self._cursor:
            return

        # PromptOS Genome table
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS promptos_genome (
                id SERIAL PRIMARY KEY,
                model VARCHAR(255),
                task_type VARCHAR(100),
                strategy TEXT,
                avg_score FLOAT,
                trials INTEGER,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # PromptOS Evolution table
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS promptos_evolution (
                id SERIAL PRIMARY KEY,
                model VARCHAR(255),
                task_type VARCHAR(100),
                strategy TEXT,
                fitness FLOAT,
                success BOOLEAN,
                score FLOAT,
                tokens_used INTEGER,
                timestamp TIMESTAMP
            )
        """)

        # PromptForge Strategy Farming table
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS promptforge_farming (
                id SERIAL PRIMARY KEY,
                model VARCHAR(255),
                task_type VARCHAR(100),
                strategy TEXT,
                score FLOAT,
                success BOOLEAN,
                timestamp TIMESTAMP
            )
        """)

        # PromptForge Experiments table
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS promptforge_experiments (
                id SERIAL PRIMARY KEY,
                prompt TEXT,
                model VARCHAR(255),
                task_type VARCHAR(100),
                strategy TEXT,
                score FLOAT,
                response TEXT,
                tokens_used INTEGER,
                latency_ms FLOAT,
                timestamp TIMESTAMP
            )
        """)

        self._conn.commit()

    def save_genome_record(self, record: Dict):
        """Save genome record."""
        if not self._cursor:
            return

        self._cursor.execute(
            """
            INSERT INTO promptos_genome (model, task_type, strategy, avg_score, trials, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                record.get("model"),
                record.get("task_type"),
                json.dumps(record.get("strategy", [])),
                record.get("avg_score", 0.5),
                record.get("trials", 0),
                datetime.now(),
            ),
        )
        self._conn.commit()

    def save_evolution_record(self, record: Dict):
        """Save evolution record."""
        if not self._cursor:
            return

        self._cursor.execute(
            """
            INSERT INTO promptos_evolution (model, task_type, strategy, fitness, success, score, tokens_used, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                record.get("model"),
                record.get("task_type"),
                json.dumps(record.get("strategy", [])),
                record.get("fitness", 0.5),
                record.get("success", False),
                record.get("score", 0.5),
                record.get("tokens_used", 0),
                datetime.now(),
            ),
        )
        self._conn.commit()

    def save_farming_record(self, record: Dict):
        """Save farming record."""
        if not self._cursor:
            return

        self._cursor.execute(
            """
            INSERT INTO promptforge_farming (model, task_type, strategy, score, success, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                record.get("model"),
                record.get("task_type"),
                json.dumps(record.get("strategy", [])),
                record.get("score", 0.5),
                record.get("success", False),
                datetime.now(),
            ),
        )
        self._conn.commit()

    def save_experiment(self, experiment: Dict):
        """Save experiment result."""
        if not self._cursor:
            return

        self._cursor.execute(
            """
            INSERT INTO promptforge_experiments (prompt, model, task_type, strategy, score, response, tokens_used, latency_ms, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                experiment.get("prompt", "")[:5000],
                experiment.get("model"),
                experiment.get("task_type"),
                json.dumps(experiment.get("strategy", [])),
                experiment.get("score", 0.5),
                experiment.get("response", "")[:10000],
                experiment.get("tokens_used", 0),
                experiment.get("latency_ms", 0),
                datetime.now(),
            ),
        )
        self._conn.commit()

    def get_genome(
        self, model: Optional[str] = None, task_type: Optional[str] = None
    ) -> List[Dict]:
        """Get genome records."""
        if not self._cursor:
            return []

        query = "SELECT model, task_type, strategy, avg_score, trials, last_updated FROM promptos_genome"
        params = []

        if model or task_type:
            conditions = []
            if model:
                conditions.append("model = %s")
                params.append(model)
            if task_type:
                conditions.append("task_type = %s")
                params.append(task_type)
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY avg_score DESC LIMIT 100"

        self._cursor.execute(query, params)
        rows = self._cursor.fetchall()

        return [
            {
                "model": r[0],
                "task_type": r[1],
                "strategy": json.loads(r[2]) if r[2] else [],
                "avg_score": r[3],
                "trials": r[4],
                "last_updated": r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ]

    def close(self):
        """Close connection."""
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()


class QdrantStorage:
    """
    Qdrant vector storage for PromptOS/PromptForge.

    Stores embeddings for semantic search of strategies and experiments.
    """

    def __init__(self, qdrant_url: Optional[str] = None):
        self.qdrant_url = qdrant_url or get_qdrant_url()
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.qdrant_url, check_compatibility=False)
            self._ensure_collections()
            print("[Qdrant] Connected successfully")
        except ImportError:
            print("[Qdrant] qdrant-client not available")
        except Exception as e:
            print(f"[Qdrant] Connection failed: {e}")

    def _ensure_collections(self):
        """Ensure collections exist."""
        if not self._client:
            return

        from qdrant_client.models import Distance, VectorParams

        # Strategy embeddings collection
        if not self._client.collection_exists("promptos_strategies"):
            self._client.create_collection(
                "promptos_strategies",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        # Experiment embeddings collection
        if not self._client.collection_exists("promptforge_experiments"):
            self._client.create_collection(
                "promptforge_experiments",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        # Try to use sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            return model.encode(text).tolist()
        except ImportError:
            pass

        # Fallback: simple hash-based embedding
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes[:48]] + [0.0] * (384 - 48)

    def store_strategy(
        self, strategy: List[str], model: str, task_type: str, score: float
    ):
        """Store strategy embedding."""
        if not self._client:
            return

        from qdrant_client.models import PointStruct

        text = f"Strategy: {strategy} for {task_type} on {model}"
        embedding = self._get_embedding(text)

        self._client.upsert(
            "promptos_strategies",
            points=[
                PointStruct(
                    id=f"{model}:{task_type}:{','.join(strategy)}",
                    vector=embedding,
                    payload={
                        "strategy": strategy,
                        "model": model,
                        "task_type": task_type,
                        "score": score,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            ],
        )

    def search_strategies(
        self, query: str, model: Optional[str] = None, limit: int = 5
    ) -> List[Dict]:
        """Search strategies by semantic similarity."""
        if not self._client:
            return []

        embedding = self._get_embedding(query)

        results = self._client.search(
            "promptos_strategies",
            query_vector=embedding,
            limit=limit,
        )

        return [
            {
                "strategy": r.payload.get("strategy"),
                "model": r.payload.get("model"),
                "task_type": r.payload.get("task_type"),
                "score": r.payload.get("score"),
                "similarity": r.score,
            }
            for r in results
        ]

    def store_experiment(
        self,
        prompt: str,
        response: str,
        strategy: List[str],
        model: str,
        task_type: str,
        score: float,
    ):
        """Store experiment for later analysis."""
        if not self._client:
            return

        from qdrant_client.models import PointStruct

        text = f"Prompt: {prompt}\nResponse: {response[:500]}"
        embedding = self._get_embedding(text)

        self._client.upsert(
            "promptforge_experiments",
            points=[
                PointStruct(
                    id=f"{datetime.now().timestamp()}",
                    vector=embedding,
                    payload={
                        "prompt": prompt[:1000],
                        "response": response[:2000],
                        "strategy": strategy,
                        "model": model,
                        "task_type": task_type,
                        "score": score,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            ],
        )

    def close(self):
        """Close connection."""
        if self._client:
            self._client.close()


# Convenience function to get storage instances
def get_storage() -> tuple:
    """
    Get PostgreSQL and Qdrant storage instances.

    Returns:
        (postgres, qdrant) tuple
    """
    pg = PostgresStorage()
    qd = QdrantStorage()

    pg.connect()

    return pg, qd
