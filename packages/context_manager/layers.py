"""
Memory Layers
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class LayerItem:
    """Item in a memory layer."""

    name: str
    content: str
    added_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: Optional[int] = None
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if item has expired."""
        if self.ttl_seconds:
            return datetime.now() > self.added_at + timedelta(seconds=self.ttl_seconds)
        return False


class MemoryLayers:
    """Memory layer system with TTL support."""

    LAYER_ORDER = ["working", "short_term", "skills", "long_term", "reference"]

    DEFAULT_TTL = {
        "short_term": 300,
        "working": 1800,
        "skills": 3600,
        "long_term": None,
        "reference": None,
    }

    def __init__(self, default_ttl: Dict[str, int] = None):
        self.layers: Dict[str, List[LayerItem]] = {
            layer: [] for layer in self.LAYER_ORDER
        }
        self.ttl_overrides: Dict[str, int] = {}
        if default_ttl:
            self.DEFAULT_TTL.update(default_ttl)

    def add_to_layer(self, layer: str, name: str, content: str = "", ttl: int = None):
        """Add item to layer."""
        if layer not in self.layers:
            self.layers[layer] = []

        ttl_seconds = (
            ttl or self.ttl_overrides.get(layer) or self.DEFAULT_TTL.get(layer)
        )

        item = LayerItem(name=name, content=content, ttl_seconds=ttl_seconds)

        self.layers[layer].append(item)

    def get_from_layer(self, layer: str) -> List[LayerItem]:
        """Get non-expired items from layer."""
        if layer not in self.layers:
            return []

        return [item for item in self.layers[layer] if not item.is_expired()]

    def get_all(self, max_tokens: int = 8000) -> List[LayerItem]:
        """Get all items ordered by layer priority."""
        result = []
        total_chars = 0

        for layer in self.LAYER_ORDER:
            for item in self.get_from_layer(layer):
                if total_chars + len(item.content) <= max_tokens * 4:
                    result.append(item)
                    total_chars += len(item.content)

        return result

    def clear_layer(self, layer: str):
        """Clear a layer."""
        if layer in self.layers:
            self.layers[layer].clear()

    def expire_old_items(self):
        """Remove expired items from all layers."""
        for layer in self.layers:
            self.layers[layer] = [
                item for item in self.layers[layer] if not item.is_expired()
            ]

    def get_layer_counts(self) -> Dict[str, int]:
        """Get counts per layer (excluding expired)."""
        return {layer: len(self.get_from_layer(layer)) for layer in self.LAYER_ORDER}
