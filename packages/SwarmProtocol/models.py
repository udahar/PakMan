"""
SwarmProtocol - models.py
Message schema and data models for inter-agent communication.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MessageType(str, Enum):
    OFFER = "OFFER"        # Broker proposes task to an agent
    ACCEPT = "ACCEPT"      # Agent accepts the task
    REJECT = "REJECT"      # Agent declines (too busy, incapable)
    PROGRESS = "PROGRESS"  # Agent sends a status update mid-task
    DONE = "DONE"          # Agent reports successful completion
    FAIL = "FAIL"          # Agent reports failure


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class SwarmMessage:
    """
    The universal inter-agent message packet.

    Schema:
        id        — globally unique message ID
        type      — MessageType enum
        sender    — agent_id that created this message
        recipient — agent_id target (or "broadcast")
        payload   — task details, results, or error info
        ref_id    — ID of the original OFFER this message responds to
        timestamp — ISO creation time
        ttl       — time-to-live in seconds (0 = no expiry)
    """
    sender: str
    recipient: str
    msg_type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"swarm_{uuid.uuid4().hex[:10]}")
    ref_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl: int = 300

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.msg_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "ref_id": self.ref_id,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SwarmMessage":
        return cls(
            sender=d["sender"],
            recipient=d["recipient"],
            msg_type=MessageType(d["type"]),
            payload=d.get("payload", {}),
            id=d.get("id", f"swarm_{uuid.uuid4().hex[:10]}"),
            ref_id=d.get("ref_id"),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat()),
            ttl=d.get("ttl", 300),
        )


@dataclass
class AgentCapability:
    """What an agent can do — broadcast during registration."""
    agent_id: str
    name: str
    skills: List[str]          # e.g. ["python", "research", "validation"]
    max_concurrent: int = 1
    status: AgentStatus = AgentStatus.IDLE

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "skills": self.skills,
            "max_concurrent": self.max_concurrent,
            "status": self.status.value,
        }
