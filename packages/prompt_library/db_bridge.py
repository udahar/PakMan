# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
PromptOS Database Bridge
Connect prompt_library to Frank's database tables for learning
"""

import json
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    import psycopg2
    from qdrant_client import QdrantClient

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class PromptOSDatabaseBridge:
    """
    Bridge between prompt_library and Frank's database.

    Uses Frank's tables:
    - frank_prompts (learning data)
    - frank_prompt_performance (usage stats)
    - frank_strategy_effectiveness (strategy results)
    """

    TABLE_PROMPTS = "frank_prompts"
    TABLE_PERFORMANCE = "frank_prompt_performance"
    TABLE_STRATEGIES = "frank_strategy_effectiveness"

    COLLECTION_PROMPTS = "frank_prompts_embeddings"
    COLLECTION_STRATEGIES = "frank_strategy_embeddings"

    def __init__(
        self,
        postgres_url: str = "postgresql://postgres:postgres@localhost:5432/zolapress",
        qdrant_url: str = "http://localhost:6333",
        embedding_model: str = "bge-m3:latest",
        ollama_url: str = "http://127.0.0.1:11434",
    ):
        self.postgres_url = postgres_url
        self.qdrant_url = qdrant_url
        self.embedding_model = embedding_model
        self.ollama_url = ollama_url

        self.pg_conn = None
        self.qdrant_client = None
        self.use_db = False

        self._connect()

    def _connect(self):
        """Connect to databases."""
        if not DB_AVAILABLE:
            print("[PromptOS Bridge] Database drivers not available")
            return

        try:
            self.pg_conn = psycopg2.connect(self.postgres_url)
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
            self._ensure_schema()
            self.use_db = True
            print("[PromptOS Bridge] Connected to Frank's database")
        except Exception as e:
            print(f"[PromptOS Bridge] Connection failed: {e}")
            self.use_db = False

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        if not self.pg_conn:
            return

        cursor = self.pg_conn.cursor()

        # Prompts table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_PROMPTS} (
                id SERIAL PRIMARY KEY,
                prompt_id VARCHAR(100) UNIQUE,
                act VARCHAR(500),
                prompt_text TEXT,
                source VARCHAR(100),
                vetted BOOLEAN DEFAULT FALSE,
                effectiveness_score FLOAT DEFAULT 0.0,
                usage_count INT DEFAULT 0,
                success_count INT DEFAULT 0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT[],
                for_devs BOOLEAN DEFAULT FALSE
            )
        """)

        # Performance tracking
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_PERFORMANCE} (
                id SERIAL PRIMARY KEY,
                prompt_id VARCHAR(100),
                user_input TEXT,
                model_used VARCHAR(100),
                score FLOAT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Strategy effectiveness
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_STRATEGIES} (
                id SERIAL PRIMARY KEY,
                strategy_id VARCHAR(100),
                task_type VARCHAR(100),
                effectiveness_score FLOAT DEFAULT 0.0,
                usage_count INT DEFAULT 0,
                success_count INT DEFAULT 0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.pg_conn.commit()

        # Qdrant collections
        self._ensure_qdrant_collection(self.COLLECTION_PROMPTS)
        self._ensure_qdrant_collection(self.COLLECTION_STRATEGIES)

    def _ensure_qdrant_collection(self, name: str):
        """Ensure Qdrant collection exists."""
        try:
            collections = self.qdrant_client.get_collections().collections
            if not any(c.name == name for c in collections):
                self.qdrant_client.create_collection(
                    collection_name=name,
                    vectors_config={"size": 1024, "distance": "Cosine"},
                )
        except Exception:
            pass

    def store_prompt(
        self,
        prompt_id: str,
        act: str,
        prompt_text: str,
        source: str = "prompts.chat",
        vetted: bool = False,
        tags: Optional[List[str]] = None,
        for_devs: bool = False,
    ) -> bool:
        """Store a prompt in the database."""
        if not self.use_db:
            return False

        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_PROMPTS} 
                (prompt_id, act, prompt_text, source, vetted, tags, for_devs)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (prompt_id) DO UPDATE
                SET act = EXCLUDED.act, prompt_text = EXCLUDED.prompt_text
            """,
                (
                    prompt_id,
                    act,
                    prompt_text,
                    source,
                    vetted,
                    json.dumps(tags or []),
                    for_devs,
                ),
            )

            self.pg_conn.commit()

            # Also store in Qdrant for semantic search
            self._store_embedding(
                self.COLLECTION_PROMPTS, prompt_id, f"{act}: {prompt_text}"
            )

            return True
        except Exception as e:
            print(f"Error storing prompt: {e}")
            return False

    def _store_embedding(self, collection: str, doc_id: str, text: str):
        """Store embedding in Qdrant."""
        try:
            embedding = self._get_embedding(text)
            self.qdrant_client.upsert(
                collection_name=collection,
                points=[
                    {
                        "id": hashlib.md5(doc_id.encode()).hexdigest()[:12],
                        "vector": embedding,
                        "payload": {"text": text, "doc_id": doc_id},
                    }
                ],
            )
        except Exception:
            pass

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama."""
        try:
            import requests

            resp = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30,
            )
            return resp.json()["embedding"]
        except Exception:
            return [0.0] * 1024

    def record_usage(
        self,
        prompt_id: str,
        user_input: str,
        model_used: str,
        score: float,
        feedback: Optional[str] = None,
    ) -> bool:
        """Record prompt usage for learning."""
        if not self.use_db:
            return False

        try:
            cursor = self.pg_conn.cursor()

            # Update prompt stats
            cursor.execute(
                f"""
                UPDATE {self.TABLE_PROMPTS}
                SET usage_count = usage_count + 1,
                    success_count = success_count + %s,
                    effectiveness_score = CASE 
                        WHEN usage_count = 0 THEN %s
                        ELSE (effectiveness_score * usage_count + %s) / (usage_count + 1)
                    END,
                    last_used = CURRENT_TIMESTAMP
                WHERE prompt_id = %s
            """,
                (1 if score > 0.5 else 0, score, score, prompt_id),
            )

            # Record performance
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_PERFORMANCE}
                (prompt_id, user_input, model_used, score, feedback)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (prompt_id, user_input, model_used, score, feedback),
            )

            self.pg_conn.commit()
            return True
        except Exception as e:
            print(f"Error recording usage: {e}")
            return False

    def record_strategy_effectiveness(
        self, strategy_id: str, task_type: str, score: float
    ) -> bool:
        """Record strategy effectiveness for learning."""
        if not self.use_db:
            return False

        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_STRATEGIES}
                (strategy_id, task_type, effectiveness_score, usage_count, success_count)
                VALUES (%s, %s, %s, 1, %s)
                ON CONFLICT (strategy_id, task_type) DO UPDATE
                SET usage_count = {self.TABLE_STRATEGIES}.usage_count + 1,
                    success_count = {self.TABLE_STRATEGIES}.success_count + %s,
                    effectiveness_score = (
                        {self.TABLE_STRATEGIES}.effectiveness_score * {self.TABLE_STRATEGIES}.usage_count + %s
                    ) / ({self.TABLE_STRATEGIES}.usage_count + 1),
                    last_used = CURRENT_TIMESTAMP
            """,
                (
                    strategy_id,
                    task_type,
                    score,
                    1 if score > 0.5 else 0,
                    1 if score > 0.5 else 0,
                    score,
                ),
            )

            self.pg_conn.commit()
            return True
        except Exception:
            return False

    def get_best_prompts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get best performing prompts."""
        if not self.use_db:
            return []

        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                f"""
                SELECT prompt_id, act, prompt_text, effectiveness_score, usage_count
                FROM {self.TABLE_PROMPTS}
                WHERE usage_count > 0
                ORDER BY effectiveness_score DESC
                LIMIT %s
            """,
                (limit,),
            )

            return [
                {
                    "prompt_id": row[0],
                    "act": row[1],
                    "prompt_text": row[2],
                    "effectiveness": row[3],
                    "usage_count": row[4],
                }
                for row in cursor.fetchall()
            ]
        except Exception:
            return []

    def get_best_strategies(
        self, task_type: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get best strategies for a task type."""
        if not self.use_db:
            return []

        try:
            cursor = self.pg_conn.cursor()
            if task_type:
                cursor.execute(
                    f"""
                    SELECT strategy_id, task_type, effectiveness_score, usage_count
                    FROM {self.TABLE_STRATEGIES}
                    WHERE task_type = %s
                    ORDER BY effectiveness_score DESC
                    LIMIT %s
                """,
                    (task_type, limit),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT strategy_id, task_type, effectiveness_score, usage_count
                    FROM {self.TABLE_STRATEGIES}
                    ORDER BY effectiveness_score DESC
                    LIMIT %s
                """,
                    (limit,),
                )

            return [
                {
                    "strategy_id": row[0],
                    "task_type": row[1],
                    "effectiveness": row[2],
                    "usage_count": row[3],
                }
                for row in cursor.fetchall()
            ]
        except Exception:
            return []

    def search_prompts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search prompts."""
        try:
            embedding = self._get_embedding(query)
            results = self.qdrant_client.search(
                collection_name=self.COLLECTION_PROMPTS,
                query_vector=embedding,
                limit=limit,
            )

            return [
                {
                    "prompt_id": r.payload.get("doc_id"),
                    "text": r.payload.get("text"),
                    "score": r.score,
                }
                for r in results
            ]
        except Exception:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get learning stats."""
        if not self.use_db:
            return {"available": False}

        try:
            cursor = self.pg_conn.cursor()

            cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_PROMPTS}")
            prompt_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_STRATEGIES}")
            strategy_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_PERFORMANCE}")
            performance_count = cursor.fetchone()[0]

            return {
                "available": True,
                "prompts": prompt_count,
                "strategies": strategy_count,
                "performance_records": performance_count,
            }
        except Exception:
            return {"available": False}

    def close(self):
        """Close connections."""
        if self.pg_conn:
            self.pg_conn.close()


def create_prompos_bridge(
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/zolapress",
    qdrant_url: str = "http://localhost:6333",
) -> PromptOSDatabaseBridge:
    """Factory function to create PromptOS bridge."""
    return PromptOSDatabaseBridge(postgres_url=postgres_url, qdrant_url=qdrant_url)
