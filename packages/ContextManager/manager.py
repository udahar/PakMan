"""
Core Context Manager
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


@dataclass
class ContextItem:
    """A piece of context."""

    name: str
    content: str
    layer: str = "working"
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def access(self):
        """Record access."""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def tokens(self) -> int:
        """Estimate token count."""
        return len(self.content) // 4


class ContextManager:
    """
    Smart context management with relevance scoring and pruning.
    """

    DEFAULT_MAX_TOKENS = 8000

    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self.items: Dict[str, ContextItem] = {}
        self.layers = MemoryLayers()

    def add(
        self, name: str, content: str, layer: str = "working", metadata: Dict = None
    ):
        """Add context item."""
        self.items[name] = ContextItem(
            name=name, content=content, layer=layer, metadata=metadata or {}
        )
        self.layers.add_to_layer(layer, name)

    def get(self, name: str) -> Optional[str]:
        """Get context item by name."""
        item = self.items.get(name)
        if item:
            item.access()
            return item.content
        return None

    def remove(self, name: str) -> bool:
        """Remove context item."""
        if name in self.items:
            del self.items[name]
            return True
        return False

    def get_for_task(self, query: str, task_type: str = None) -> str:
        """Get optimized context for task."""
        scorer = RelevanceScorer()

        scored = []
        for name, item in self.items.items():
            score = scorer.score(name, item.content, query, task_type)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        total_tokens = 0

        for score, item in scored:
            item_tokens = item.tokens()
            if total_tokens + item_tokens <= self.max_tokens:
                result.append(item.content)
                total_tokens += item_tokens

        return "\n\n".join(result)

    def prune(self, target_tokens: int = None) -> str:
        """Prune to fit token limit."""
        target = target_tokens or self.max_tokens

        scored = []
        for name, item in self.items.items():
            score = self._calculate_priority(item)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        total_tokens = 0

        for score, item in scored:
            item_tokens = item.tokens()
            if total_tokens + item_tokens <= target:
                result.append(item.content)
                total_tokens += item_tokens

        return "\n\n".join(result)

    def _calculate_priority(self, item: ContextItem) -> float:
        """Calculate priority score for pruning."""
        recency = (datetime.now() - item.last_accessed).total_seconds()
        recency_score = max(0, 1 - (recency / 86400))

        access_score = min(1.0, item.access_count / 10)

        layer_priority = {
            "working": 1.0,
            "short_term": 0.8,
            "skills": 0.6,
            "long_term": 0.4,
            "reference": 0.2,
        }
        layer_score = layer_priority.get(item.layer, 0.5)

        return (recency_score * 0.3) + (access_score * 0.2) + (layer_score * 0.5)

    def get_all(self) -> List[ContextItem]:
        """Get all context items."""
        return list(self.items.values())

    def clear(self, layer: str = None):
        """Clear context."""
        if layer:
            to_remove = [n for n, i in self.items.items() if i.layer == layer]
            for name in to_remove:
                del self.items[name]
        else:
            self.items.clear()

    def stats(self) -> Dict:
        """Get context stats."""
        total_tokens = sum(i.tokens() for i in self.items.values())
        return {
            "item_count": len(self.items),
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "layers": self.layers.get_layer_counts(),
        }


class MemoryLayers:
    """Memory layer system for context."""

    LAYER_PRIORITY = {
        "working": 0,
        "short_term": 1,
        "skills": 2,
        "long_term": 3,
        "reference": 4,
    }

    def __init__(self):
        self.layers: Dict[str, List[str]] = {
            "working": [],
            "short_term": [],
            "skills": [],
            "long_term": [],
            "reference": [],
        }

    def add_to_layer(self, layer: str, item_name: str):
        """Add item to layer."""
        if layer not in self.layers:
            self.layers[layer] = []
        if item_name not in self.layers[layer]:
            self.layers[layer].append(item_name)

    def remove_from_layer(self, layer: str, item_name: str):
        """Remove item from layer."""
        if layer in self.layers and item_name in self.layers[layer]:
            self.layers[layer].remove(item_name)

    def get_layer_counts(self) -> Dict[str, int]:
        """Get counts per layer."""
        return {layer: len(items) for layer, items in self.layers.items()}

    def get_ordered_items(self) -> List[str]:
        """Get all items ordered by layer priority."""
        result = []
        for layer in ["working", "short_term", "skills", "long_term", "reference"]:
            result.extend(self.layers.get(layer, []))
        return result
