"""
DocumentShredder - shredder.py
Main entry point. Routes files to parsers, chunks, and emits output.

Usage:
    from DocumentShredder import shred

    # Parse a ChatGPT export
    result = shred("conversations.html")
    print(result.to_jsonl())

    # Parse a PDF with a custom token budget
    result = shred("report.pdf", max_tokens=256)

    # Emit as Markdown
    from DocumentShredder.shredder import to_markdown
    print(to_markdown(result))
"""
import os
import json
from pathlib import Path
from typing import Optional
from .models import ParseResult
from .parsers import (
    parse_chatgpt_html,
    parse_pdf,
    parse_docx,
    parse_xlsx,
    parse_markdown,
    parse_image,
)
from .chunker import rechunk, auto_tag


# ── router ───────────────────────────────────────────────────────────────────

EXTENSION_MAP = {
    ".html": parse_chatgpt_html,
    ".htm": parse_chatgpt_html,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".xls": parse_xlsx,
    ".md": parse_markdown,
    ".txt": parse_markdown,
    ".png": parse_image,
    ".jpg": parse_image,
    ".jpeg": parse_image,
    ".webp": parse_image,
}


def shred(
    filepath: str,
    max_tokens: int = 512,
    auto_tag_chunks: bool = True,
) -> ParseResult:
    """
    Shred any supported document into structured AI-ready chunks.

    Args:
        filepath:        Absolute or relative path to the file.
        max_tokens:      Max tokens per output chunk (default: 512).
        auto_tag_chunks: Auto-detect chunk type and apply content tags.

    Returns:
        ParseResult with .chunks (list of Chunk), .to_jsonl(), etc.

    Raises:
        ValueError: If file type is unsupported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = path.suffix.lower()
    parser = EXTENSION_MAP.get(ext)

    if parser is None:
        raise ValueError(
            f"Unsupported file type: {ext!r}. "
            f"Supported: {', '.join(sorted(EXTENSION_MAP.keys()))}"
        )

    result = parser(str(path))
    result = rechunk(result, max_tokens=max_tokens)

    if auto_tag_chunks:
        result = auto_tag(result)

    return result


# ── output helpers ────────────────────────────────────────────────────────────

def to_markdown(result: ParseResult) -> str:
    """Render all chunks as a single clean Markdown document."""
    lines = [f"# Shredded: {result.source}\n",
             f"*Parser: {result.parser_used} | "
             f"Chunks: {len(result.chunks)} | "
             f"Tokens: {result.total_tokens}*\n",
             "---\n"]
    for chunk in result.chunks:
        lines.append(f"**[chunk {chunk.chunk_id} | {chunk.chunk_type.value}]**\n")
        lines.append(chunk.content)
        lines.append("\n---\n")
    return "\n".join(lines)


def to_jsonl(result: ParseResult, filepath: Optional[str] = None) -> str:
    """Emit all chunks as JSONL. Optionally write to a file."""
    jsonl = "\n".join(json.dumps(c.to_dict(), ensure_ascii=False)
                      for c in result.chunks)
    if filepath:
        Path(filepath).write_text(jsonl, encoding="utf-8")
    return jsonl


def shred_folder(
    folder: str,
    output_jsonl: Optional[str] = None,
    max_tokens: int = 512,
) -> ParseResult:
    """
    Shred an entire folder of documents. Returns a combined ParseResult.
    Silently skips unsupported files.
    """
    from .models import Chunk, ParseResult as PR
    all_chunks = []
    cid = 0
    errors = []

    for entry in sorted(Path(folder).iterdir()):
        if not entry.is_file() or entry.suffix.lower() not in EXTENSION_MAP:
            continue
        try:
            result = shred(str(entry), max_tokens=max_tokens)
            for chunk in result.chunks:
                chunk.chunk_id = cid
                cid += 1
            all_chunks.extend(result.chunks)
        except Exception as e:
            errors.append(f"{entry.name}: {e}")

    combined = PR(
        source=folder,
        chunks=all_chunks,
        total_tokens=sum(c.tokens for c in all_chunks),
        parser_used="multi",
        errors=errors,
    )
    if output_jsonl:
        to_jsonl(combined, output_jsonl)

    return combined
