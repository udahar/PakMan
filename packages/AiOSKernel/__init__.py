"""
AiOS Kernel - AI Operating System Kernel for Frank

The core reasoning loop that orchestrates AI operations.

Architecture:
- Conversational Core (reasoning loop)
- Event Driven (handlers for external triggers)
- Scheduler Driven (queued tasks for background work)
- Ticket Hierarchy: Project → Epic → Chapter → Story → Ticket

Usage:
    from AiOSKernel import get_kernel, create_ticket, execute_ready_tickets
    
    kernel = await get_kernel().initialize()
    
    # Create tickets
    project_id = await create_ticket("project", "Build Report", "Generate AI report")
    ticket_id = await create_ticket("ticket", "Research", "Search papers", parent_id=project_id)
    
    # Execute ready tickets
    results = await execute_ready_tickets()
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import sqlite3
import uuid
import traceback


# === Ticket Hierarchy ===

class TicketLevel(Enum):
    """Ticket hierarchy levels"""
    PROJECT = "project"
    EPIC = "epic"
    CHAPTER = "chapter"
    STORY = "story"
    TICKET = "ticket"


class TicketStatus(Enum):
    """Ticket execution status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Ticket:
    """
    A ticket in the hierarchy.
    
    Hierarchy: Project → Epic → Chapter → Story → Ticket
    """
    ticket_id: str
    level: TicketLevel
    title: str
    description: str
    status: TicketStatus = TicketStatus.PENDING
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    assigned_to: Optional[str] = None  # worker_id
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "ticket_id": self.ticket_id,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "assigned_to": self.assigned_to,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Ticket":
        return cls(
            ticket_id=data["ticket_id"],
            level=TicketLevel(data["level"]),
            title=data["title"],
            description=data["description"],
            status=TicketStatus(data["status"]),
            parent_id=data.get("parent_id"),
            dependencies=data.get("dependencies", []),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            assigned_to=data.get("assigned_to"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )


# === Capability System ===

class CapabilityType(Enum):
    """Types of capabilities"""
    MODEL = "model"
    TOOL = "tool"
    SKILL = "skill"
    WORKFLOW = "workflow"


@dataclass
class Capability:
    """A capability that workers can provide"""
    capability_id: str
    name: str
    capability_type: CapabilityType
    pool: str
    benchmark_score: float = 0.0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "capability_type": self.capability_type.value,
            "pool": self.pool,
            "benchmark_score": self.benchmark_score,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "metadata": self.metadata,
            "is_active": self.is_active
        }


@dataclass
class Worker:
    """A worker that can execute tasks"""
    worker_id: str
    name: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "idle"
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata
        }


# === Kernel State ===

@dataclass
class KernelState:
    """Current state of the kernel"""
    status: str = "initializing"
    uptime: datetime = field(default_factory=datetime.now)
    tickets_processed: int = 0
    tickets_failed: int = 0
    events_processed: int = 0
    active_workers: int = 0
    queue_size: int = 0
    memory_usage_mb: float = 0.0
    last_tick: datetime = field(default_factory=datetime.now)


# === Event System ===

@dataclass
class Event:
    """An event in the system"""
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


# === Main Kernel ===

class AiOSKernel:
    """
    AI Operating System Kernel.
    
    Manages:
    - Ticket hierarchy (Project→Epic→Chapter→Story→Ticket)
    - Dependency graph scheduling
    - Capability pools
    - Worker routing
    - Event system
    - Model execution via PromptRouter
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.state = KernelState()
        
        # Ticket storage
        self.tickets: Dict[str, Ticket] = {}
        self.ticket_hierarchy: Dict[str, List[str]] = {}
        
        # Worker system
        self.workers: Dict[str, Worker] = {}
        self.capabilities: Dict[str, Capability] = {}
        self.capability_pools: Dict[str, List[str]] = {}
        
        # Event system
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        
        # Execution
        self._running = False
        self._execution_lock = asyncio.Lock()
        
        # Database
        self._init_db()
        self._load_from_db()
    
    def _init_db(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                parent_id TEXT,
                dependencies TEXT,
                priority INTEGER DEFAULT 0,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                metadata TEXT,
                assigned_to TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Capabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                capability_type TEXT NOT NULL,
                pool TEXT NOT NULL,
                benchmark_score REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                avg_latency_ms REAL DEFAULT 0.0,
                metadata TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Workers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                worker_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                capabilities TEXT,
                status TEXT DEFAULT 'idle',
                current_task TEXT,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                last_active TEXT,
                metadata TEXT
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT,
                timestamp TEXT,
                source TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_parent ON tickets(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_pool ON capabilities(pool)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status)")
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """Load all data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load tickets
        cursor.execute("SELECT * FROM tickets")
        for row in cursor.fetchall():
            ticket = Ticket(
                ticket_id=row[0], level=TicketLevel(row[1]), title=row[2],
                description=row[3], status=TicketStatus(row[4]), parent_id=row[5],
                dependencies=json.loads(row[6]) if row[6] else [], priority=row[7],
                created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                started_at=datetime.fromisoformat(row[9]) if row[9] else None,
                completed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                result=json.loads(row[11]) if row[11] else None, error=row[12],
                metadata=json.loads(row[13]) if row[13] else {},
                assigned_to=row[14], retry_count=row[15] or 0
            )
            self.tickets[ticket.ticket_id] = ticket
            if ticket.parent_id:
                self.ticket_hierarchy.setdefault(ticket.parent_id, []).append(ticket.ticket_id)
        
        # Load capabilities
        cursor.execute("SELECT * FROM capabilities")
        for row in cursor.fetchall():
            cap = Capability(
                capability_id=row[0], name=row[1], capability_type=CapabilityType(row[2]),
                pool=row[3], benchmark_score=row[4] or 0.0, success_rate=row[5] or 0.0,
                avg_latency_ms=row[6] or 0.0, metadata=json.loads(row[7]) if row[7] else {},
                is_active=bool(row[8])
            )
            self.capabilities[cap.capability_id] = cap
            self.capability_pools.setdefault(cap.pool, []).append(cap.capability_id)
        
        # Load workers
        cursor.execute("SELECT * FROM workers")
        for row in cursor.fetchall():
            worker = Worker(
                worker_id=row[0], name=row[1],
                capabilities=json.loads(row[2]) if row[2] else [],
                status=row[3] or "idle", current_task=row[4],
                tasks_completed=row[5] or 0, tasks_failed=row[6] or 0,
                last_active=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                metadata=json.loads(row[8]) if row[8] else {}
            )
            self.workers[worker.worker_id] = worker
        
        conn.close()
    
    def _save_ticket(self, ticket: Ticket):
        """Save ticket to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO tickets 
            (ticket_id, level, title, description, status, parent_id, dependencies, priority,
             created_at, started_at, completed_at, result, error, metadata, assigned_to, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket.ticket_id, ticket.level.value, ticket.title, ticket.description,
            ticket.status.value, ticket.parent_id, json.dumps(ticket.dependencies),
            ticket.priority, ticket.created_at.isoformat() if ticket.created_at else None,
            ticket.started_at.isoformat() if ticket.started_at else None,
            ticket.completed_at.isoformat() if ticket.completed_at else None,
            json.dumps(ticket.result) if ticket.result else None, ticket.error,
            json.dumps(ticket.metadata), ticket.assigned_to, ticket.retry_count
        ))
        conn.commit()
        conn.close()
    
    def _save_capability(self, cap: Capability):
        """Save capability to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO capabilities
            (capability_id, name, capability_type, pool, benchmark_score, success_rate, avg_latency_ms, metadata, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cap.capability_id, cap.name, cap.capability_type.value, cap.pool,
            cap.benchmark_score, cap.success_rate, cap.avg_latency_ms,
            json.dumps(cap.metadata), 1 if cap.is_active else 0
        ))
        conn.commit()
        conn.close()
    
    def _save_worker(self, worker: Worker):
        """Save worker to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO workers
            (worker_id, name, capabilities, status, current_task, tasks_completed, tasks_failed, last_active, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            worker.worker_id, worker.name, json.dumps(worker.capabilities), worker.status,
            worker.current_task, worker.tasks_completed, worker.tasks_failed,
            worker.last_active.isoformat(), json.dumps(worker.metadata)
        ))
        conn.commit()
        conn.close()
    
    # === Lifecycle ===
    
    async def initialize(self):
        """Initialize the kernel"""
        self.state.status = "initializing"
        
        # Register default handlers
        self._register_default_handlers()
        
        # Sync capabilities from PromptRouter
        self.sync_capabilities_from_prompt_router()
        
        self.state.status = "running"
        self.state.uptime = datetime.now()
        self._running = True
        
        print(f"✅ AiOS Kernel initialized")
        print(f"   Status: {self.state.status}")
        print(f"   Tickets loaded: {len(self.tickets)}")
        print(f"   Workers loaded: {len(self.workers)}")
        print(f"   Capabilities loaded: {len(self.capabilities)}")
        
        return self
    
    async def shutdown(self):
        """Shutdown the kernel"""
        self._running = False
        self.state.status = "stopped"
        print("⏹️  AiOS Kernel stopped")
    
    # === Ticket Management ===
    
    async def create_ticket(
        self,
        level: Union[str, TicketLevel],
        title: str,
        description: str,
        parent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        priority: int = 0,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new ticket"""
        ticket_id = f"{level if isinstance(level, str) else level.value}_{uuid.uuid4().hex[:8]}"
        
        ticket = Ticket(
            ticket_id=ticket_id,
            level=level if isinstance(level, TicketLevel) else TicketLevel(level),
            title=title,
            description=description,
            parent_id=parent_id,
            dependencies=dependencies or [],
            priority=priority,
            metadata=metadata or {}
        )
        
        self.tickets[ticket_id] = ticket
        
        if parent_id:
            self.ticket_hierarchy.setdefault(parent_id, []).append(ticket_id)
        
        self._save_ticket(ticket)
        await self.emit_event("ticket.created", {"ticket_id": ticket_id, "level": ticket.level.value})
        
        return ticket_id
    
    def get_ready_tickets(self) -> List[Ticket]:
        """Get tickets ready to execute (all dependencies satisfied)"""
        ready = []
        
        for ticket in self.tickets.values():
            if ticket.status != TicketStatus.PENDING:
                continue
            
            deps_satisfied = all(
                self.tickets.get(dep_id, Ticket("", TicketLevel.TICKET, "", "", TicketStatus.COMPLETED)).status == TicketStatus.COMPLETED
                for dep_id in ticket.dependencies
            )
            
            if deps_satisfied:
                ticket.status = TicketStatus.READY
                ready.append(ticket)
        
        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready
    
    async def execute_ready_tickets(self, max_concurrent: int = 5) -> List[Dict]:
        """Execute all ready tickets"""
        async with self._execution_lock:
            ready = self.get_ready_tickets()
            
            if not ready:
                return []
            
            results = []
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_with_semaphore(ticket):
                async with semaphore:
                    result = await self.execute_ticket(ticket)
                    results.append(result)
            
            await asyncio.gather(*[execute_with_semaphore(t) for t in ready])
            
            return results
    
    async def execute_ticket(self, ticket: Ticket) -> Dict:
        """Execute a single ticket"""
        ticket.status = TicketStatus.RUNNING
        ticket.started_at = datetime.now()
        self._save_ticket(ticket)
        
        try:
            # Route based on level
            if ticket.level == TicketLevel.PROJECT:
                result = await self._execute_project(ticket)
            elif ticket.level == TicketLevel.EPIC:
                result = await self._execute_epic(ticket)
            elif ticket.level == TicketLevel.CHAPTER:
                result = await self._execute_chapter(ticket)
            elif ticket.level == TicketLevel.STORY:
                result = await self._execute_story(ticket)
            else:
                result = await self._execute_basic_ticket(ticket)
            
            ticket.status = TicketStatus.COMPLETED
            ticket.result = result
            ticket.completed_at = datetime.now()
            self.state.tickets_processed += 1
            
            self._save_ticket(ticket)
            await self.emit_event("ticket.completed", {"ticket_id": ticket.ticket_id, "result": result})
            
            return result
            
        except Exception as e:
            ticket.retry_count += 1
            
            if ticket.retry_count < ticket.max_retries:
                ticket.status = TicketStatus.PENDING
                ticket.error = f"Retry {ticket.retry_count}/{ticket.max_retries}: {str(e)}"
            else:
                ticket.status = TicketStatus.FAILED
                ticket.error = str(e)
                ticket.completed_at = datetime.now()
                self.state.tickets_failed += 1
            
            self._save_ticket(ticket)
            await self.emit_event("ticket.failed", {"ticket_id": ticket.ticket_id, "error": str(e), "traceback": traceback.format_exc()})
            
            raise
    
    async def _execute_basic_ticket(self, ticket: Ticket) -> Dict:
        """Execute a basic ticket using PromptRouter for model selection"""
        from PromptRouter import rank_cards
        
        prompt = f"{ticket.title}: {ticket.description}"
        best_models = rank_cards(prompt, top_k=3)
        
        if best_models:
            best = best_models[0]
            return {
                "ticket_id": ticket.ticket_id,
                "title": ticket.title,
                "selected_model": best.get("model", "unknown"),
                "model_score": best.get("score", 0.0),
                "alternatives": [m.get("model") for m in best_models[1:3]],
                "status": "routed"
            }
        
        return {"ticket_id": ticket.ticket_id, "title": ticket.title, "status": "no_model_found"}
    
    async def _execute_project(self, ticket: Ticket) -> Dict:
        """Execute project - process all epics"""
        children = self.ticket_hierarchy.get(ticket.ticket_id, [])
        child_results = []
        
        for child_id in children:
            child = self.tickets.get(child_id)
            if child and child.level == TicketLevel.EPIC:
                if child.status == TicketStatus.PENDING:
                    child.status = TicketStatus.READY
                result = await self.execute_ticket(child)
                child_results.append(result)
        
        return {"level": "project", "ticket_id": ticket.ticket_id, "epics": child_results}
    
    async def _execute_epic(self, ticket: Ticket) -> Dict:
        """Execute epic - process all chapters"""
        children = self.ticket_hierarchy.get(ticket.ticket_id, [])
        child_results = []
        
        for child_id in children:
            child = self.tickets.get(child_id)
            if child and child.level == TicketLevel.CHAPTER:
                if child.status == TicketStatus.PENDING:
                    child.status = TicketStatus.READY
                result = await self.execute_ticket(child)
                child_results.append(result)
        
        return {"level": "epic", "ticket_id": ticket.ticket_id, "chapters": child_results}
    
    async def _execute_chapter(self, ticket: Ticket) -> Dict:
        """Execute chapter - process all stories"""
        children = self.ticket_hierarchy.get(ticket.ticket_id, [])
        child_results = []
        
        for child_id in children:
            child = self.tickets.get(child_id)
            if child and child.level == TicketLevel.STORY:
                if child.status == TicketStatus.PENDING:
                    child.status = TicketStatus.READY
                result = await self.execute_ticket(child)
                child_results.append(result)
        
        return {"level": "chapter", "ticket_id": ticket.ticket_id, "stories": child_results}
    
    async def _execute_story(self, ticket: Ticket) -> Dict:
        """Execute story - process all tickets"""
        children = self.ticket_hierarchy.get(ticket.ticket_id, [])
        child_results = []
        
        for child_id in children:
            child = self.tickets.get(child_id)
            if child and child.level == TicketLevel.TICKET:
                if child.status == TicketStatus.PENDING:
                    child.status = TicketStatus.READY
                result = await self.execute_ticket(child)
                child_results.append(result)
        
        return {"level": "story", "ticket_id": ticket.ticket_id, "tickets": child_results}
    
    # === Capability System ===
    
    def register_capability(self, capability: Capability):
        """Register a capability"""
        self.capabilities[capability.capability_id] = capability
        self.capability_pools.setdefault(capability.pool, []).append(capability.capability_id)
        self._save_capability(capability)
    
    def sync_capabilities_from_prompt_router(self):
        """Sync capabilities from PromptRouter rankings"""
        try:
            from PromptRouter import get_all_models
            
            models = get_all_models()
            
            for model in models:
                model_id = model.get("model", "unknown")
                model_score = model.get("score", 0.0)
                
                # Determine pool based on model name
                pool = "general"
                if "coder" in model_id.lower() or "code" in model_id.lower():
                    pool = "code_generation"
                elif "math" in model_id.lower():
                    pool = "math"
                elif "research" in model_id.lower() or "claude" in model_id.lower():
                    pool = "research"
                
                cap = Capability(
                    capability_id=f"model_{model_id}",
                    name=model_id,
                    capability_type=CapabilityType.MODEL,
                    pool=pool,
                    benchmark_score=model_score
                )
                self.register_capability(cap)
            
            print(f"   ✅ Synced {len(models)} models from PromptRouter")
            
        except Exception as e:
            # Register defaults if PromptRouter unavailable
            defaults = [
                ("claude_3_5", "Claude 3.5", "research", 0.92),
                ("deepseek_math", "DeepSeek Math", "math", 0.95),
                ("qwen_coder", "Qwen Coder", "code_generation", 0.88),
            ]
            for model_id, name, pool, score in defaults:
                self.register_capability(Capability(model_id, name, CapabilityType.MODEL, pool, score))
            print(f"   ⚠️  Registered {len(defaults)} default capabilities")
    
    def get_best_capability(self, pool: str) -> Optional[Capability]:
        """Get best capability for a pool"""
        if pool not in self.capability_pools:
            return None
        
        pool_caps = [
            self.capabilities[cap_id]
            for cap_id in self.capability_pools[pool]
            if cap_id in self.capabilities and self.capabilities[cap_id].is_active
        ]
        
        return max(pool_caps, key=lambda c: c.benchmark_score) if pool_caps else None
    
    # === Worker Management ===
    
    def register_worker(self, worker: Worker):
        """Register a worker"""
        self.workers[worker.worker_id] = worker
        self._save_worker(worker)
    
    def get_idle_worker(self, pool: str) -> Optional[Worker]:
        """Get idle worker with capability for pool"""
        for worker in self.workers.values():
            if worker.status != "idle":
                continue
            
            # Check if worker has any capability in the pool
            if pool in self.capability_pools:
                for cap_id in self.capability_pools[pool]:
                    if cap_id in worker.capabilities:
                        return worker
        
        return None
    
    # === Event System ===
    
    async def emit_event(self, event_type: str, payload: Dict):
        """Emit an event"""
        event = Event(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            payload=payload,
            source="kernel"
        )
        
        self.event_history.append(event)
        self.state.events_processed += 1
        
        # Save to DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (event_id, event_type, payload, timestamp, source) VALUES (?, ?, ?, ?, ?)",
                      (event.event_id, event.event_type, json.dumps(payload), event.timestamp.isoformat(), event.source))
        conn.commit()
        conn.close()
        
        # Call handlers
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event.to_dict())
                    else:
                        handler(event.to_dict())
                except Exception as e:
                    print(f"Handler error for {event_type}: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.handlers.setdefault(event_type, []).append(handler)
    
    def _register_default_handlers(self):
        """Register default handlers"""
        self.register_handler("ticket.created", lambda e: print(f"📋 Ticket created: {e['payload'].get('ticket_id')}"))
        self.register_handler("ticket.completed", lambda e: print(f"✅ Ticket completed: {e['payload'].get('ticket_id')}"))
        self.register_handler("ticket.failed", lambda e: print(f"❌ Ticket failed: {e['payload'].get('ticket_id')} - {e['payload'].get('error', 'Unknown')}"))
    
    # === State & Monitoring ===
    
    def get_state(self) -> KernelState:
        """Get kernel state"""
        self.state.queue_size = len([t for t in self.tickets.values() if t.status == TicketStatus.READY])
        self.state.active_workers = len([w for w in self.workers.values() if w.status == "idle"])
        self.state.last_tick = datetime.now()
        return self.state
    
    def get_stats(self) -> Dict:
        """Get kernel statistics"""
        state = self.get_state()
        uptime = (datetime.now() - state.uptime).total_seconds()
        
        return {
            "status": state.status,
            "uptime_seconds": uptime,
            "tickets_processed": state.tickets_processed,
            "tickets_failed": state.tickets_failed,
            "events_processed": state.events_processed,
            "active_workers": state.active_workers,
            "queue_size": state.queue_size,
            "total_tickets": len(self.tickets),
            "total_capabilities": len(self.capabilities),
            "total_pools": len(self.capability_pools),
            "total_workers": len(self.workers)
        }


# === Global API ===

_kernel: Optional[AiOSKernel] = None

def get_kernel(db_path: str = ":memory:") -> AiOSKernel:
    """Get or create kernel instance"""
    global _kernel
    if not _kernel:
        _kernel = AiOSKernel(db_path)
    return _kernel

async def initialize_kernel(db_path: str = ":memory:") -> AiOSKernel:
    """Initialize the global kernel"""
    kernel = get_kernel(db_path)
    await kernel.initialize()
    return kernel

async def create_ticket(level: str, title: str, description: str, **kwargs) -> str:
    """Create a ticket"""
    kernel = get_kernel()
    return await kernel.create_ticket(level, title, description, **kwargs)

def get_ready_tickets() -> List[Ticket]:
    """Get ready tickets"""
    return get_kernel().get_ready_tickets()

async def execute_ready_tickets(max_concurrent: int = 5) -> List[Dict]:
    """Execute all ready tickets"""
    return await get_kernel().execute_ready_tickets(max_concurrent)

def get_best_capability(pool: str) -> Optional[Capability]:
    """Get best capability for pool"""
    return get_kernel().get_best_capability(pool)

def register_capability(cap: Capability):
    """Register a capability"""
    get_kernel().register_capability(cap)

def register_worker(worker: Worker):
    """Register a worker"""
    get_kernel().register_worker(worker)

def register_handler(event_type: str, handler: Callable):
    """Register an event handler"""
    get_kernel().register_handler(event_type, handler)
