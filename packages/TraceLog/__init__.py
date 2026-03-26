"""
TraceLog
Distributed AI prompt execution tracing. Zero external dependencies.

Quick start:
    from TraceLog import Tracer, SQLiteStore
    from TraceLog.renderer import render_timeline

    store = SQLiteStore("traces.db")
    tracer = Tracer(store=store)

    with tracer.start_trace("process_ticket") as trace:
        with tracer.span(trace, "llm_call") as span:
            span.set("model", "gpt-4o")
            response = call_llm(prompt)
            span.set("tokens", 512)
        with tracer.span(trace, "tool_read_file") as span:
            span.set("path", "/tmp/context.md")

    print(render_timeline(trace))

    # Query recent errors
    errors = store.get_errors()
"""
from .tracer import Tracer
from .spans import Span, Trace
from .store import InMemoryStore, JSONLStore, SQLiteStore
from .renderer import render_timeline, render_summary

__version__ = "0.1.0"
__all__ = [
    "Tracer",
    "Span",
    "Trace",
    "InMemoryStore",
    "JSONLStore",
    "SQLiteStore",
    "render_timeline",
    "render_summary",
]
