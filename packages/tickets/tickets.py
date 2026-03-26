"""
Tickets - Lightweight ticket and task tracking for AI workflows.

Usage:
    from tickets import TicketManager, create_ticket, list_tickets
    
    mgr = TicketManager()
    ticket_id = mgr.create("Fix login bug", "priority:high", "open")
    
    open_tickets = mgr.list(status="open")
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CLOSED = "closed"


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    tags: List[str]
    metadata: Dict


class TicketManager:
    def __init__(self, storage_path: str = "~/.pakman/tickets.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.tickets: Dict[str, Ticket] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for tid, t in data.get("tickets", {}).items():
                    self.tickets[tid] = Ticket(**t)
            except Exception:
                pass
    
    def _save(self):
        data = {"tickets": {tid: asdict(t) for tid, t in self.tickets.items()}}
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def create(
        self,
        title: str,
        description: str = "",
        status: str = "open",
        priority: str = "medium",
        tags: Optional[List[str]] = None
    ) -> str:
        import uuid
        ticket_id = f"TICKET-{uuid.uuid4().hex[:6].upper()}"
        
        now = datetime.now().isoformat()
        ticket = Ticket(
            id=ticket_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            metadata={}
        )
        self.tickets[ticket_id] = ticket
        self._save()
        return ticket_id
    
    def get(self, ticket_id: str) -> Optional[Ticket]:
        return self.tickets.get(ticket_id)
    
    def update(self, ticket_id: str, **kwargs) -> bool:
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        ticket.updated_at = datetime.now().isoformat()
        self._save()
        return True
    
    def delete(self, ticket_id: str) -> bool:
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            self._save()
            return True
        return False
    
    def list(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Ticket]:
        results = list(self.tickets.values())
        
        if status:
            results = [t for t in results if t.status == status]
        if priority:
            results = [t for t in results if t.priority == priority]
        
        return sorted(results, key=lambda t: t.created_at, reverse=True)


def create_ticket(title: str, description: str = "", **kwargs) -> str:
    """Quick create ticket function."""
    mgr = TicketManager()
    return mgr.create(title, description, **kwargs)


def list_tickets(status: Optional[str] = None) -> List[Ticket]:
    """Quick list tickets function."""
    mgr = TicketManager()
    return mgr.list(status=status)


__all__ = ["TicketManager", "Ticket", "TicketStatus", "TicketPriority", "create_ticket", "list_tickets"]