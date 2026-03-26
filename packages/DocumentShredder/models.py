"""
DocumentShredder - models.py
Data models for chunks and parse results.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ChunkType(str, Enum):
    PROSE = "prose"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    HEADING = "heading"
    CAPTION = "caption"
    Q_AND_A = "q_and_a"


@dataclass
class Chunk:
    chunk_id: int
    source: str
    content: str
    chunk_type: ChunkType = ChunkType.PROSE
    tokens: int = 0
    tags: List[str] = field(default_factory=list)
    page: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "content": self.content,
            "type": self.chunk_type.value,
            "tokens": self.tokens,
            "tags": self.tags,
            "page": self.page,
        }


@dataclass
class ParseResult:
    source: str
    chunks: List[Chunk]
    total_tokens: int = 0
    parser_used: str = "unknown"
    errors: List[str] = field(default_factory=list)

    def to_jsonl(self) -> str:
        import json
        return "\n".join(json.dumps(c.to_dict()) for c in self.chunks)
