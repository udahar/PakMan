# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Context Manager
Manages long context storage and retrieval for RLM-style processing
Inspired by RLM paper - custom implementation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
import re


@dataclass
class ContextChunk:
    """A chunk of context with metadata."""

    chunk_id: str
    content: str
    start_pos: int
    end_pos: int
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    Manages long context for recursive processing.

    Features:
    - Chunking large documents
    - Tag-based retrieval
    - Search within context
    - Statistics tracking
    """

    DEFAULT_CHUNK_SIZE = 4000
    DEFAULT_OVERLAP = 200

    def __init__(
        self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.contexts: Dict[str, str] = {}
        self.chunks: Dict[str, List[ContextChunk]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def load_context(
        self,
        key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk: bool = True,
    ) -> str:
        """
        Load context with optional chunking.

        Args:
            key: Unique identifier for context
            content: The context content
            metadata: Optional metadata
            chunk: Whether to chunk the context

        Returns:
            Context key
        """
        self.contexts[key] = content

        self.metadata[key] = metadata or {}
        self.metadata[key]["length"] = len(content)
        self.metadata[key]["loaded_at"] = self._get_timestamp()

        if chunk:
            self._create_chunks(key, content)

        return key

    def load_file(
        self, key: str, file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Load context from file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        file_metadata = metadata or {}
        file_metadata["file_path"] = str(path)
        file_metadata["file_name"] = path.name
        file_metadata["file_size"] = path.stat().st_size

        return self.load_context(key, content, file_metadata)

    def _create_chunks(self, key: str, content: str):
        """Create overlapping chunks from content."""
        chunks = []
        pos = 0
        chunk_id = 0

        while pos < len(content):
            chunk_content = content[pos : pos + self.chunk_size]

            chunk = ContextChunk(
                chunk_id=f"{key}_chunk_{chunk_id}",
                content=chunk_content,
                start_pos=pos,
                end_pos=pos + len(chunk_content),
                tags=self._extract_tags(chunk_content),
            )
            chunks.append(chunk)

            pos += self.chunk_size - self.overlap
            chunk_id += 1

        self.chunks[key] = chunks

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content."""
        tags = []

        code_patterns = [
            (r"def\s+(\w+)", "function"),
            (r"class\s+(\w+)", "class"),
            (r"import\s+(\w+)", "import"),
            (r"#\s*(.+)", "comment"),
        ]

        for pattern, tag_type in code_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:3]:
                tags.append(f"{tag_type}:{match}")

        return tags[:10]

    def get_context(self, key: str) -> Optional[str]:
        """Get full context by key."""
        return self.contexts.get(key)

    def get_chunk(self, key: str, chunk_index: int) -> Optional[ContextChunk]:
        """Get a specific chunk."""
        if key in self.chunks:
            chunks = self.chunks[key]
            if 0 <= chunk_index < len(chunks):
                return chunks[chunk_index]
        return None

    def get_chunks_by_tag(self, key: str, tag: str) -> List[ContextChunk]:
        """Get chunks matching a tag."""
        if key not in self.chunks:
            return []

        return [c for c in self.chunks[key] if tag in c.tags]

    def search(self, key: str, pattern: str) -> List[ContextChunk]:
        """Search for pattern in context."""
        if key not in self.chunks:
            return []

        matches = []
        for chunk in self.chunks[key]:
            if re.search(pattern, chunk.content, re.IGNORECASE):
                matches.append(chunk)

        return matches

    def search_full_text(self, key: str, query: str) -> List[str]:
        """Full-text search in context."""
        if key not in self.contexts:
            return []

        content = self.contexts[key]
        lines = content.split("\n")

        query_lower = query.lower()
        matches = []

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                matches.append("\n".join(lines[start:end]))

        return matches[:10]

    def get_stats(self, key: str) -> Dict[str, Any]:
        """Get statistics for context."""
        if key not in self.contexts:
            return {}

        content = self.contexts[key]

        return {
            "key": key,
            "length": len(content),
            "token_estimate": len(content) // 4,
            "line_count": len(content.split("\n")),
            "word_count": len(content.split()),
            "chunk_count": len(self.chunks.get(key, [])),
            "metadata": self.metadata.get(key, {}),
        }

    def list_contexts(self) -> List[str]:
        """List all loaded contexts."""
        return list(self.contexts.keys())

    def remove_context(self, key: str) -> bool:
        """Remove context and its chunks."""
        if key in self.contexts:
            del self.contexts[key]
            if key in self.chunks:
                del self.chunks[key]
            if key in self.metadata:
                del self.metadata[key]
            return True
        return False

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    def export_metadata(self, key: str) -> str:
        """Export context metadata as JSON."""
        if key in self.metadata:
            return json.dumps(self.metadata[key], indent=2)
        return "{}"

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all contexts."""
        return {
            "total_contexts": len(self.contexts),
            "total_chunks": sum(len(c) for c in self.chunks.values()),
            "contexts": {key: self.get_stats(key) for key in self.contexts.keys()},
        }


def create_context_manager(
    chunk_size: int = 4000, overlap: int = 200
) -> ContextManager:
    """Factory function to create context manager."""
    return ContextManager(chunk_size=chunk_size, overlap=overlap)
