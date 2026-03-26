"""
TraceLog - spans.py
Trace context and span data models.
Inspired by OpenTelemetry but zero external dependencies.
"""
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Span:
    """
    A single unit of work within a trace.

    Examples:
        - A single LLM API call
        - A tool invocation
        - A document retrieval
        - An agent handoff
    """
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    status: str = "ok"          # ok | error | timeout
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return round((self.end_time - self.start_time) * 1000, 2)

    def finish(self, status: str = "ok", error: str = None):
        self.end_time = time.monotonic()
        self.status = status
        if error:
            self.error = error
            self.status = "error"

    def add_event(self, name: str, attrs: Dict[str, Any] = None):
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attrs": attrs or {},
        })

    def set(self, key: str, value: Any) -> "Span":
        self.attributes[key] = value
        return self

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "error": self.error,
        }


@dataclass
class Trace:
    """Root container for all spans sharing a trace_id."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "trace"
    spans: List[Span] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def root_span(self) -> Optional[Span]:
        return next((s for s in self.spans if s.parent_id is None), None)

    def total_duration_ms(self) -> Optional[float]:
        root = self.root_span()
        return root.duration_ms if root else None

    def errors(self) -> List[Span]:
        return [s for s in self.spans if s.status == "error"]

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "created_at": self.created_at,
            "total_duration_ms": self.total_duration_ms(),
            "span_count": len(self.spans),
            "error_count": len(self.errors()),
            "spans": [s.to_dict() for s in self.spans],
        }
