"""
Ticket Executor - Task agent for Frank/Alfred AI

Executes tickets using skills, reasoning strategies, and multi-model orchestration.
"""

import logging
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from .skill_loader import SkillLoader
except ImportError:
    from skill_loader import SkillLoader

logger = logging.getLogger(__name__)


class TicketStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_CONTEXT = "waiting_context"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Ticket:
    """Represents a task ticket"""
    ticket_id: str
    title: str
    description: str
    status: TicketStatus = TicketStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Execution details
    assigned_skills: List[str] = field(default_factory=list)
    strategy: Optional[str] = None
    assigned_model: Optional[str] = None
    
    # Results
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_log: List[Dict] = field(default_factory=list)
    
    # Counsel collaboration
    shared_context_key: Optional[str] = None
    contributing_models: List[str] = field(default_factory=list)


@dataclass
class TicketResult:
    """Result from ticket execution"""
    ticket_id: str
    success: bool
    result: Any
    skills_used: List[str]
    strategies_used: List[str]
    models_used: List[str]
    execution_time_ms: int = 0
    error: Optional[str] = None


class TicketExecutor:
    """
    Executes tickets using skills and reasoning strategies.
    
    Workflow:
    1. Load ticket
    2. Select best skills (auto or manual)
    3. Execute skills with model
    4. Record results
    5. Update shared context (Counsel)
    
    Usage:
        executor = TicketExecutor()
        
        # Create ticket
        ticket = await executor.create_ticket(
            title="Research quantum computing",
            description="I need to understand..."
        )
        
        # Execute
        result = await executor.execute(ticket)
    """
    
    def __init__(
        self,
        skill_loader: SkillLoader = None,
        tickets_dir: str = None,
        context_client=None
    ):
        logger.info("Initializing TicketExecutor")
        self.skill_loader = skill_loader or SkillLoader()
        self.tickets_dir = Path(tickets_dir) if tickets_dir else self._default_tickets_dir()
        self.context_client = context_client  # For Counsel collaboration
        self.tickets: Dict[str, Ticket] = {}
    
    def _default_tickets_dir(self) -> Path:
        """Get default tickets directory"""
        return Path(__file__).parent.parent / "tickets"
    
    async def initialize(self):
        """Initialize the executor"""
        await self.skill_loader.initialize()
        self._ensure_tickets_dir()
    
    def _ensure_tickets_dir(self):
        """Create tickets directory if not exists"""
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_ticket(
        self,
        title: str,
        description: str,
        ticket_id: str = None
    ) -> Ticket:
        """
        Create a new ticket.
        
        Args:
            title: Ticket title
            description: Detailed description
            ticket_id: Optional custom ID (auto-generated if not provided)
        
        Returns:
            Created ticket
        """
        if not ticket_id:
            ticket_id = self._generate_ticket_id()
        
        ticket = Ticket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            shared_context_key=f"ticket_{ticket_id}"
        )
        
        self.tickets[ticket_id] = ticket
        
        # Save to disk
        await self._save_ticket(ticket)
        
        return ticket
    
    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        import random
        timestamp = datetime.now().strftime("%Y%m%d")
        rand = random.randint(1000, 9999)
        return f"{timestamp}_{rand}"
    
    async def _save_ticket(self, ticket: Ticket):
        """Save ticket to disk"""
        ticket.updated_at = datetime.now()
        
        file_path = self.tickets_dir / f"{ticket.ticket_id}.json"
        
        data = {
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status.value,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "assigned_skills": ticket.assigned_skills,
            "strategy": ticket.strategy,
            "assigned_model": ticket.assigned_model,
            "result": ticket.result,
            "error": ticket.error,
            "execution_log": ticket.execution_log,
            "shared_context_key": ticket.shared_context_key,
            "contributing_models": ticket.contributing_models
        }
        
        file_path.write_text(json.dumps(data, indent=2))
    
    async def load_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Load ticket from disk"""
        # Check memory first
        if ticket_id in self.tickets:
            return self.tickets[ticket_id]
        
        # Load from disk
        file_path = self.tickets_dir / f"{ticket_id}.json"
        if not file_path.exists():
            return None
        
        data = json.loads(file_path.read_text())
        
        ticket = Ticket(
            ticket_id=data["ticket_id"],
            title=data["title"],
            description=data["description"],
            status=TicketStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            assigned_skills=data.get("assigned_skills", []),
            strategy=data.get("strategy"),
            assigned_model=data.get("assigned_model"),
            result=data.get("result"),
            error=data.get("error"),
            execution_log=data.get("execution_log", []),
            shared_context_key=data.get("shared_context_key"),
            contributing_models=data.get("contributing_models", [])
        )
        
        self.tickets[ticket_id] = ticket
        return ticket
    
    async def execute(
        self,
        ticket: Ticket,
        model_fn: Callable,
        auto_select_skills: bool = True
    ) -> TicketResult:
        """
        Execute a ticket.
        
        Args:
            ticket: Ticket to execute
            model_fn: Async function to call LLM
            auto_select_skills: Whether to auto-select skills
        
        Returns:
            TicketResult with execution outcome
        """
        import time
        
        ticket.status = TicketStatus.IN_PROGRESS
        start_time = time.time()
        
        skills_used = []
        strategies_used = []
        models_used = []
        
        try:
            # Step 1: Select skills
            if auto_select_skills:
                selected_skills = await self._select_skills_for_ticket(ticket)
                ticket.assigned_skills = [s.skill_id for s in selected_skills]
            else:
                selected_skills = [
                    self.skill_loader.get(sid)
                    for sid in ticket.assigned_skills
                    if self.skill_loader.get(sid)
                ]
            
            # Step 2: Read shared context (Counsel collaboration)
            context = await self._read_shared_context(ticket)
            
            # Step 3: Execute skills
            results = []
            for skill in selected_skills:
                self._log_execution(ticket, f"Executing skill: {skill.skill_id}")
                
                result = await self.skill_loader.execute(
                    skill.skill_id,
                    model_fn,
                    task=ticket.description,
                    context=context
                )
                
                results.append(result)
                skills_used.append(skill.skill_id)
                
                if result.success:
                    self._log_execution(ticket, f"✓ {skill.skill_id} completed")
                else:
                    self._log_execution(ticket, f"✗ {skill.skill_id} failed: {result.error}")
            
            # Step 4: Synthesize results
            final_result = await self._synthesize_results(ticket, results, model_fn)
            
            # Step 5: Write to shared context
            await self._write_shared_context(ticket, final_result, skills_used)
            
            ticket.status = TicketStatus.COMPLETED
            ticket.result = final_result
            ticket.contributing_models.append("frank")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            await self._save_ticket(ticket)
            
            return TicketResult(
                ticket_id=ticket.ticket_id,
                success=True,
                result=final_result,
                skills_used=skills_used,
                strategies_used=strategies_used,
                models_used=models_used,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            ticket.status = TicketStatus.FAILED
            ticket.error = str(e)
            await self._save_ticket(ticket)
            
            return TicketResult(
                ticket_id=ticket.ticket_id,
                success=False,
                result=None,
                skills_used=skills_used,
                strategies_used=strategies_used,
                models_used=models_used,
                error=str(e)
            )
    
    async def _select_skills_for_ticket(self, ticket: Ticket) -> List[Skill]:
        """Auto-select skills based on ticket description"""
        # Semantic search for relevant skills
        query = f"{ticket.title} {ticket.description}"
        matches = self.skill_loader.search(query, top_k=3)
        
        # Always include humble_inquiry for research tasks
        if "research" in query.lower() or "understand" in query.lower():
            humble = self.skill_loader.get("humble_inquiry")
            if humble and humble not in matches:
                matches.append(humble)
        
        return matches
    
    async def _read_shared_context(self, ticket: Ticket) -> Dict:
        """Read shared context from Counsel"""
        if not self.context_client:
            return {}
        
        try:
            context = await self.context_client.read(ticket.shared_context_key)
            return context or {}
        except Exception:
            return {}
    
    async def _write_shared_context(
        self,
        ticket: Ticket,
        result: Any,
        skills_used: List[str]
    ):
        """Write results to shared context"""
        if not self.context_client:
            return
        
        try:
            await self.context_client.write(ticket.shared_context_key, {
                "ticket_id": ticket.ticket_id,
                "result": result,
                "skills_used": skills_used,
                "timestamp": datetime.now().isoformat(),
                "model": "frank"
            })
        except Exception:
            pass  # Don't fail ticket if context write fails
    
    async def _synthesize_results(
        self,
        ticket: Ticket,
        skill_results: List[SkillResult],
        model_fn: Callable
    ) -> Any:
        """Synthesize results from multiple skills"""
        successful = [r for r in skill_results if r.success]
        
        if not successful:
            raise Exception("All skills failed")
        
        # Simple synthesis - would use LLM in production
        return {
            "ticket": ticket.title,
            "skill_results": [
                {"skill": r.skill_id, "result": r.result}
                for r in successful
            ]
        }
    
    def _log_execution(self, ticket: Ticket, message: str):
        """Log execution step"""
        ticket.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    def list_tickets(self, status: TicketStatus = None) -> List[Ticket]:
        """List tickets, optionally filtered by status"""
        if status:
            return [t for t in self.tickets.values() if t.status == status]
        return list(self.tickets.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics"""
        tickets = list(self.tickets.values())
        
        return {
            "total_tickets": len(tickets),
            "by_status": {
                status.value: len([t for t in tickets if t.status == status])
                for status in TicketStatus
            },
            "most_used_skills": self._get_most_used_skills()
        }
    
    def _get_most_used_skills(self) -> List[Dict[str, Any]]:
        """Get most frequently used skills"""
        skill_counts = {}
        
        for ticket in self.tickets.values():
            for skill_id in ticket.assigned_skills:
                skill_counts[skill_id] = skill_counts.get(skill_id, 0) + 1
        
        return sorted(
            [{"skill_id": k, "count": v} for k, v in skill_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]


# Global instance
_executor: Optional[TicketExecutor] = None


def get_executor() -> TicketExecutor:
    """Get or create global ticket executor"""
    global _executor
    if not _executor:
        _executor = TicketExecutor()
    return _executor


async def initialize_executor(context_client=None):
    """Initialize the global executor"""
    executor = get_executor()
    executor.context_client = context_client
    await executor.initialize()
    return executor
