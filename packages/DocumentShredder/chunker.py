"""
DocumentShredder - chunker.py
Semantic chunking layer: re-chunk by token budget and tag by type.
"""
from typing import List
from .models import Chunk, ChunkType, ParseResult


def rechunk(result: ParseResult, max_tokens: int = 512) -> ParseResult:
    """
    Re-chunk output from any parser to enforce a token max per chunk.
    Preserves table integrity (tables are never split mid-row).
    """
    new_chunks: List[Chunk] = []
    cid = 0

    for chunk in result.chunks:
        if chunk.tokens <= max_tokens or chunk.chunk_type == ChunkType.TABLE:
            new_chunk = Chunk(
                chunk_id=cid,
                source=chunk.source,
                content=chunk.content,
                chunk_type=chunk.chunk_type,
                tokens=chunk.tokens,
                tags=chunk.tags,
                page=chunk.page,
            )
            new_chunks.append(new_chunk)
            cid += 1
            continue

        # Split by sentences for prose
        sentences = chunk.content.replace("\n", " ").split(". ")
        buffer, buf_tokens = [], 0

        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            s_tokens = max(1, len(s) // 4)
            if buf_tokens + s_tokens > max_tokens and buffer:
                text = ". ".join(buffer) + "."
                new_chunks.append(Chunk(cid, chunk.source, text,
                                        chunk.chunk_type,
                                        tokens=buf_tokens,
                                        tags=chunk.tags,
                                        page=chunk.page))
                cid += 1
                buffer, buf_tokens = [], 0
            buffer.append(s)
            buf_tokens += s_tokens

        if buffer:
            text = ". ".join(buffer) + "."
            new_chunks.append(Chunk(cid, chunk.source, text,
                                    chunk.chunk_type,
                                    tokens=buf_tokens,
                                    tags=chunk.tags,
                                    page=chunk.page))
            cid += 1

    total = sum(c.tokens for c in new_chunks)
    return ParseResult(result.source, new_chunks, total, result.parser_used, result.errors)


def auto_tag(result: ParseResult) -> ParseResult:
    """
    Apply automatic content-based tags to each chunk.
    """
    code_patterns = ["```", "def ", "class ", "import ", "SELECT ", "function("]
    list_patterns = ["- ", "* ", "1. ", "2. "]

    for chunk in result.chunks:
        tags = set(chunk.tags)

        if any(p in chunk.content for p in code_patterns):
            tags.add("code")
            chunk.chunk_type = ChunkType.CODE

        if any(chunk.content.strip().startswith(p) for p in list_patterns):
            tags.add("list")
            chunk.chunk_type = ChunkType.LIST

        if chunk.content.startswith("[HUMAN]") or chunk.content.startswith("[ASSISTANT]"):
            tags.add("chatgpt")
            tags.add("q_and_a")

        if "|" in chunk.content and "---" in chunk.content:
            tags.add("table")
            chunk.chunk_type = ChunkType.TABLE

        chunk.tags = list(tags)

    return result
