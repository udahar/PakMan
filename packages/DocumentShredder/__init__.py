"""
DocumentShredder
Universal document ingestion pipeline for AI systems.

Takes PDFs, Word docs, Excel sheets, ChatGPT exports, and images,
and converts them to clean Markdown-formatted chunks ready for RAG.

Quick start:
    from DocumentShredder import shred
    result = shred("conversations.html")
    print(result.to_jsonl())

    # Shred a whole folder
    from DocumentShredder import shred_folder
    result = shred_folder("./my_docs", output_jsonl="out.jsonl")
"""
from .shredder import shred, shred_folder, to_markdown, to_jsonl
from .models import Chunk, ChunkType, ParseResult

__version__ = "0.1.0"
__all__ = [
    "shred",
    "shred_folder",
    "to_markdown",
    "to_jsonl",
    "Chunk",
    "ChunkType",
    "ParseResult",
]
