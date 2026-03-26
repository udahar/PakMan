"""
ContextCompressor
Token-aware context window manager for AI agents. Zero external deps.

Quick start:
    from ContextCompressor import ContextCompressor

    cc = ContextCompressor(max_tokens=4096)

    # System prompt is pinned — never dropped
    cc.add("system", "You are a code review assistant.", pin=True)

    # Add conversation turns
    cc.add("user", very_long_document)
    cc.add("assistant", previous_response)
    cc.add("user", new_question)

    # Compress and get API-ready messages
    messages = cc.fit()
    response = llm(messages=messages)

    # With LLM summarization for maximum context retention
    from ContextCompressor import ContextCompressor
    cc = ContextCompressor(max_tokens=8192, llm=my_llm)

    # Check stats
    print(cc.stats())
    # {"messages": 12, "current_tokens": 3200, "budget": 7680, "utilization_pct": 41.7}
"""
from .compressor import ContextCompressor, Message

__version__ = "0.1.0"
__all__ = ["ContextCompressor", "Message"]
