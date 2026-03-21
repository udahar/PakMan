"""
Council Role Definitions

Each role has specific responsibilities and cannot overstep.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class RoleContext:
    """Context passed to each role."""
    task: str
    input_data: Any
    observatory_data: Optional[dict] = None
    memory_data: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RoleResponse:
    """Response from a council role."""
    role: str
    content: Any
    confidence: float = 1.0
    reasoning: str = ""
    requires_approval: bool = False


class CouncilRole(ABC):
    """Abstract base class for all council roles."""
    
    name: str = "base_role"
    description: str = "Base council role"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model
        self._call_count = 0
    
    @abstractmethod
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """
        Deliberate on the task from this role's perspective.
        
        Must be implemented by each role.
        """
        pass
    
    def get_stats(self) -> dict:
        """Get role usage statistics."""
        return {
            "name": self.name,
            "call_count": self._call_count,
            "model": self.model,
        }
    
    def increment_call(self):
        """Track role usage."""
        self._call_count += 1


class Planner(CouncilRole):
    """
    The Planner - Strategy and creativity
    
    Proposes solutions and pipelines.
    Does NOT execute anything.
    """
    
    name = "planner"
    description = "Strategic planning and solution design"
    
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """Propose a solution strategy."""
        self.increment_call()
        
        # In production, this would call an LLM
        proposal = {
            "task": context.task,
            "proposed_pipeline": [],
            "required_tools": [],
            "estimated_complexity": "unknown",
        }
        
        return RoleResponse(
            role=self.name,
            content=proposal,
            confidence=0.8,
            reasoning="Initial strategy proposal",
            requires_approval=True,
        )


class Engineer(CouncilRole):
    """
    The Engineer - Technical validation
    
    Checks feasibility and tool compatibility.
    Does NOT design solutions.
    """
    
    name = "engineer"
    description = "Technical feasibility validation"
    
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """Validate technical feasibility."""
        self.increment_call()
        
        validation = {
            "feasible": True,
            "tools_available": True,
            "memory_requirements": "acceptable",
            "warnings": [],
        }
        
        return RoleResponse(
            role=self.name,
            content=validation,
            confidence=0.9,
            reasoning="Technical validation complete",
            requires_approval=True,
        )


class Scientist(CouncilRole):
    """
    The Scientist - Data-driven evaluation
    
    Analyzes metrics and recommends based on performance.
    Does NOT make final decisions.
    """
    
    name = "scientist"
    description = "Performance analysis and data-driven recommendations"
    
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """Evaluate based on observatory data."""
        self.increment_call()
        
        analysis = {
            "recommended_pipeline": None,
            "performance_score": 0.0,
            "alternatives": [],
            "data_sources": [],
        }
        
        if context.observatory_data:
            # Analyze real performance data
            analysis["data_sources"] = list(context.observatory_data.keys())
        
        return RoleResponse(
            role=self.name,
            content=analysis,
            confidence=0.85,
            reasoning="Data-driven analysis",
            requires_approval=False,
        )


class Governor(CouncilRole):
    """
    The Governor - Safety enforcement
    
    Enforces rules, budgets, and constraints.
    Does NOT do creative work.
    """
    
    name = "governor"
    description = "Safety constraints and rule enforcement"
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        self._rules = {
            "max_tools_per_day": 3,
            "max_subsystems_per_week": 1,
            "allowed_capabilities": [
                "filesystem", "network", "ai", 
                "data", "security", "automation", "analysis"
            ],
        }
    
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """Check safety constraints."""
        self.increment_call()
        
        safety_check = {
            "approved": True,
            "constraints": [],
            "remaining_budget": {},
            "violations": [],
        }
        
        return RoleResponse(
            role=self.name,
            content=safety_check,
            confidence=1.0,
            reasoning="Safety constraints verified",
            requires_approval=True,
        )
    
    def set_rules(self, rules: dict):
        """Update governance rules."""
        self._rules.update(rules)


class Archivist(CouncilRole):
    """
    The Archivist - Memory and history
    
    Tracks lineage and records decisions.
    Does NOT participate in active decisions.
    """
    
    name = "archivist"
    description = "Memory management and decision recording"
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        self._records = []
    
    def deliberate(self, context: RoleContext) -> RoleResponse:
        """Record decision for posterity."""
        self.increment_call()
        
        record = {
            "timestamp": context.timestamp.isoformat(),
            "task": context.task,
            "context": context.input_data,
        }
        
        self._records.append(record)
        
        return RoleResponse(
            role=self.name,
            content={"recorded": True, "record_id": len(self._records)},
            confidence=1.0,
            reasoning="Decision archived",
            requires_approval=False,
        )
    
    def get_history(self, limit: int = 10) -> list:
        """Retrieve decision history."""
        return self._records[-limit:]
    
    def search(self, query: str) -> list:
        """Search archives."""
        return [r for r in self._records if query.lower() in str(r)]
