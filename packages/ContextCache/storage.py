# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Context Storage
Persist contexts to disk
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime


class ContextStorage:
    """
    Persist contexts to disk.

    Storage formats:
    - JSON files
    - Search index
    """

    def __init__(self, storage_dir: str = "./contexts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

    def _load_index(self):
        """Load search index."""
        if self.index_file.exists():
            with open(self.index_file, "r") as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _save_index(self):
        """Save search index."""
        with open(self.index_file, "w") as f:
            json.dump(self.index, f)

    def save(
        self,
        entry_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save context to disk."""
        file_path = self.storage_dir / f"{entry_id}.json"

        data = {
            "entry_id": entry_id,
            "messages": messages,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        keywords = self._extract_keywords(messages)
        self.index[entry_id] = {
            "keywords": keywords,
            "message_count": len(messages),
            "created_at": data["created_at"],
        }
        self._save_index()

        return entry_id

    def load(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Load context from disk."""
        file_path = self.storage_dir / f"{entry_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            return json.load(f)

    def delete(self, entry_id: str) -> bool:
        """Delete context from disk."""
        file_path = self.storage_dir / f"{entry_id}.json"

        if file_path.exists():
            file_path.unlink()

            if entry_id in self.index:
                del self.index[entry_id]
                self._save_index()

            return True

        return False

    def search(self, query: str, limit: int = 10) -> List[str]:
        """Search contexts by keywords."""
        query_words = set(query.lower().split())

        matches = []

        for entry_id, data in self.index.items():
            keywords = set(data.get("keywords", []))

            if query_words & keywords:
                matches.append(entry_id)

        return matches[:limit]

    def _extract_keywords(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract keywords from messages."""
        all_text = " ".join(msg.get("content", "").lower() for msg in messages)

        words = all_text.split()

        stop_words = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "in"}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]

        return list(set(keywords))[:50]

    def list_all(self) -> List[str]:
        """List all saved context IDs."""
        return list(self.index.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get storage stats."""
        return {"total_contexts": len(self.index), "storage_dir": str(self.storage_dir)}


def create_context_storage(storage_dir: str = "./contexts") -> ContextStorage:
    """Factory function to create context storage."""
    return ContextStorage(storage_dir=storage_dir)
