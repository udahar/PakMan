"""
WebHooker - models.py
Normalized event model. Raw webhook payloads from any source
are reduced to a standard WebhookEvent for downstream consumption.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class WebhookEvent:
    """
    Canonical inbound event. Everything from GitHub PRs to Stripe
    payments flows through this model before hitting the AiOS.

    Fields:
        id         — Unique event ID
        source     — Source system (github, stripe, slack, custom, ...)
        event_type — Namespaced event name (e.g. "github.pull_request.opened")
        payload    — Original parsed JSON payload
        summary    — Short human-readable description (auto-generated)
        timestamp  — UTC ISO timestamp of receipt
        metadata   — Optional enrichment dict (headers, IP, etc.)
    """
    source: str
    event_type: str
    payload: Dict[str, Any]
    summary: str = ""
    id: str = field(default_factory=lambda: f"wh_{uuid.uuid4().hex[:10]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_ticket(self) -> dict:
        """Convert to an AiOSKernel-compatible ticket dict."""
        return {
            "id": self.id,
            "title": self.summary or self.event_type,
            "description": (
                f"Source: {self.source}\n"
                f"Event:  {self.event_type}\n"
                f"Time:   {self.timestamp}\n\n"
                f"Payload:\n{self._payload_summary()}"
            ),
            "source": self.source,
            "event_type": self.event_type,
            "priority": "normal",
            "tags": [self.source, self.event_type],
        }

    def _payload_summary(self) -> str:
        import json
        try:
            return json.dumps(self.payload, indent=2, ensure_ascii=False)[:800]
        except Exception:
            return str(self.payload)[:800]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "event_type": self.event_type,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }
