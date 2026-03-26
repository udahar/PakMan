"""
TraceLog - tracer.py
Context-manager based tracer. Thread-safe, zero dependencies.

Usage:
    from TraceLog import Tracer

    tracer = Tracer()

    with tracer.start_trace("process_ticket") as trace:
        with tracer.span(trace, "llm_call") as span:
            span.set("model", "gpt-4o")
            response = llm(prompt)
            span.set("tokens", 512)
        with tracer.span(trace, "tool_call", parent=span) as s2:
            s2.set("tool", "read_file")
"""
import threading
from contextlib import contextmanager
from typing import Optional

from .spans import Span, Trace


class Tracer:
    """
    Thread-safe tracer. Manages active traces by thread ID.

    Each call to start_trace() creates a fresh Trace.
    Nested span() calls are automatically linked as parent→child.
    """

    def __init__(self, store=None):
        """
        Args:
            store: Optional TraceStore instance. If provided, completed
                   traces are automatically persisted.
        """
        self._store = store
        self._active: dict[int, Trace] = {}
        self._span_stack: dict[int, list] = {}
        self._lock = threading.Lock()

    @contextmanager
    def start_trace(self, name: str):
        """Start a new root trace. Use as a context manager."""
        trace = Trace(name=name)
        tid = threading.get_ident()
        with self._lock:
            self._active[tid] = trace
            self._span_stack[tid] = []

        try:
            yield trace
        finally:
            with self._lock:
                self._active.pop(tid, None)
                self._span_stack.pop(tid, None)
            if self._store:
                self._store.save(trace)

    @contextmanager
    def span(self, trace: Trace, name: str, parent: Optional[Span] = None):
        """
        Create a child span within a trace.

        Args:
            trace:  The parent Trace object.
            name:   Human-readable span name (e.g., "llm_call", "tool_read_file").
            parent: Optional explicit parent Span. If None, uses the
                    most recent active span in this thread.
        """
        tid = threading.get_ident()
        stack = self._span_stack.get(tid, [])

        parent_id = None
        if parent:
            parent_id = parent.span_id
        elif stack:
            parent_id = stack[-1].span_id

        s = Span(name=name, trace_id=trace.trace_id, parent_id=parent_id)
        trace.spans.append(s)
        stack.append(s)

        try:
            yield s
            s.finish("ok")
        except Exception as e:
            s.finish("error", error=str(e))
            raise
        finally:
            if s in stack:
                stack.remove(s)

    def current_trace(self) -> Optional[Trace]:
        """Return the active trace for the current thread, or None."""
        return self._active.get(threading.get_ident())
