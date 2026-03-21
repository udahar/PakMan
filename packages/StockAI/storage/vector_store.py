"""Qdrant Vector Store for Stock Similarity Search."""

from typing import List, Dict, Optional

from .config import get_config

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


COLLECTION_NAME = "stock_similarity"


class VectorStore:
    """Qdrant-based vector store for finding similar stocks."""

    def __init__(self, host: str = None, port: int = None, cfg=None):
        cfg = cfg or get_config()
        self.host = host or cfg.qdrant_host
        self.port = port or cfg.qdrant_port
        self.client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Qdrant."""
        if not HAS_QDRANT:
            print("✗ qdrant-client not installed. Run: pip install qdrant-client")
            return False

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._connected = True
            self._ensure_collection()
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Qdrant: {e}")
            print(f"  Make sure Qdrant is running at {self.host}:{self.port}")
            return False

    def _ensure_collection(self):
        """Ensure collection exists."""
        if not self.client:
            return

        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=8, distance=Distance.EUCLID),
            )

    def add_stock(self, symbol: str, metrics: Dict) -> bool:
        """Add a stock vector to the store."""
        if not self.client or not self._connected:
            return False

        embedding = self._create_embedding(metrics)

        payload = {
            "symbol": symbol,
            "sector": metrics.get("sector", "Unknown"),
            "total_return": metrics.get("total_return", 0),
            "volatility": metrics.get("volatility", 0),
            "sharpe_ratio": metrics.get("sharpe_ratio", 0),
            "pe_ratio": metrics.get("pe_ratio", 0),
            "peg_ratio": metrics.get("peg_ratio", 0),
        }

        point = PointStruct(
            id=self._hash_symbol(symbol), vector=embedding, payload=payload
        )

        self.client.upsert(collection_name=COLLECTION_NAME, points=[point])

        return True

    def _hash_symbol(self, symbol: str) -> int:
        """Create a unique ID from symbol."""
        return hash(symbol) % 1000000

    def _create_embedding(self, metrics: Dict) -> List[float]:
        """Create embedding vector from metrics."""
        return [
            metrics.get("total_return", 0),
            metrics.get("volatility", 0),
            metrics.get("sharpe_ratio", 0),
            metrics.get("beta", 1.0),
            (metrics.get("pe_ratio", 0) or 0) / 100,
            (metrics.get("peg_ratio", 0) or 0) / 5,
            metrics.get("revenue_growth", 0),
            metrics.get("institutional_ownership", 0),
        ]

    def find_similar(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Find stocks similar to the given symbol."""
        if not self.client or not self._connected:
            return []

        target = self.get_stock(symbol)
        if not target:
            return []

        embedding = self._create_embedding(target)

        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=limit + 1,
            score_threshold=0.0,
        )

        similar = []
        for result in results:
            if result.payload.get("symbol") != symbol:
                similar.append(
                    {
                        "symbol": result.payload.get("symbol"),
                        "score": 1 - result.score,
                        "sector": result.payload.get("sector"),
                        "total_return": result.payload.get("total_return"),
                        "volatility": result.payload.get("volatility"),
                        "sharpe_ratio": result.payload.get("sharpe_ratio"),
                    }
                )

        return similar[:limit]

    def get_stock(self, symbol: str) -> Optional[Dict]:
        """Get metrics for a specific stock."""
        if not self.client or not self._connected:
            return None

        results = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter={"must": [{"key": "symbol", "match": {"value": symbol}}]},
            limit=1,
        )

        if results[0]:
            return results[0][0].payload
        return None

    def get_all_stocks(self) -> List[Dict]:
        """Get all stocks in the store."""
        if not self.client or not self._connected:
            return []

        results = self.client.scroll(collection_name=COLLECTION_NAME, limit=1000)

        return [r.payload for r in results[0]] if results[0] else []

    def delete_stock(self, symbol: str) -> bool:
        """Delete a stock from the store."""
        if not self.client or not self._connected:
            return False

        self.client.delete(
            collection_name=COLLECTION_NAME, points_selector=[self._hash_symbol(symbol)]
        )
        return True

    def count(self) -> int:
        """Count stocks in store."""
        if not self.client or not self._connected:
            return 0

        info = self.client.get_collection(COLLECTION_NAME)
        return info.vectors_count


def get_similar_to_winners(
    winners: List[str], vector_store: VectorStore, limit: int = 5
) -> Dict[str, List[Dict]]:
    """Find stocks similar to all winners.

    Args:
        winners: List of winning stock symbols
        vector_store: Connected VectorStore
        limit: Number of similar stocks per winner

    Returns:
        Dict mapping winner symbol to list of similar stocks
    """
    results = {}

    for winner in winners:
        similar = vector_store.find_similar(winner, limit=limit)
        results[winner] = similar

    return results
