"""
Council Session Management

Orchestrates deliberation between all five roles.
"""

import json
from typing import Any, Optional
from datetime import datetime

from .roles import (
    RoleContext,
    Planner,
    Engineer,
    Scientist,
    Governor,
    Archivist,
)
from .decision import CouncilDecision, DecisionStatus


class CouncilSession:
    """
    Manages a council deliberation session.
    
    Orchestrates the flow:
    Planner → Engineer → Scientist → Governor → Archivist
    """
    
    def __init__(
        self,
        planner: Optional[Planner] = None,
        engineer: Optional[Engineer] = None,
        scientist: Optional[Scientist] = None,
        governor: Optional[Governor] = None,
        archivist: Optional[Archivist] = None,
    ):
        self.planner = planner or Planner()
        self.engineer = engineer or Engineer()
        self.scientist = scientist or Scientist()
        self.governor = governor or Governor()
        self.archivist = archivist or Archivist()
        
        self._session_count = 0
    
    def deliberate(self, task: str, context: Optional[dict] = None) -> CouncilDecision:
        """
        Run a full council deliberation.
        
        Args:
            task: The task to deliberate on
            context: Additional context data
        
        Returns:
            CouncilDecision with all role inputs
        """
        self._session_count += 1
        
        # Build context
        role_context = RoleContext(
            task=task,
            input_data=context or {},
            timestamp=datetime.now(),
        )
        
        # Phase 1: Planner proposes
        planner_response = self.planner.deliberate(role_context)
        
        # Phase 2: Engineer validates
        engineer_response = self.engineer.deliberate(role_context)
        
        # Phase 3: Scientist evaluates
        scientist_response = self.scientist.deliberate(role_context)
        
        # Phase 4: Governor checks safety
        governor_response = self.governor.deliberate(role_context)
        
        # Phase 5: Archivist records
        archivist_response = self.archivist.deliberate(role_context)
        
        # Aggregate decision
        decision = self._aggregate(
            task=task,
            planner=planner_response,
            engineer=engineer_response,
            scientist=scientist_response,
            governor=governor_response,
            archivist=archivist_response,
        )
        
        return decision
    
    def _aggregate(
        self,
        task: str,
        planner: Any,
        engineer: Any,
        scientist: Any,
        governor: Any,
        archivist: Any,
    ) -> CouncilDecision:
        """Aggregate role responses into unified decision."""
        
        # Extract content
        planner_content = planner.content if hasattr(planner, 'content') else planner
        engineer_content = engineer.content if hasattr(engineer, 'content') else engineer
        scientist_content = scientist.content if hasattr(scientist, 'content') else scientist
        governor_content = governor.content if hasattr(governor, 'content') else governor
        archivist_content = archivist.content if hasattr(archivist, 'content') else archivist
        
        # Create decision
        decision = CouncilDecision(
            task=task,
            status=DecisionStatus.PENDING,
            planner_input=planner_content,
            engineer_input=engineer_content,
            scientist_input=scientist_content,
            governor_input=governor_content,
            archivist_input=archivist_content,
        )
        
        # Calculate confidence
        decision.calculate_confidence()
        
        # Determine approval status
        engineer_ok = engineer_content.get("feasible", False) if engineer_content else True
        governor_ok = governor_content.get("approved", False) if governor_content else True
        
        if not engineer_ok:
            decision.status = DecisionStatus.REJECTED
            decision.reasoning = "Engineer rejected: technical infeasibility"
        elif not governor_ok:
            decision.status = DecisionStatus.REJECTED
            decision.reasoning = "Governor rejected: safety constraint violation"
        else:
            decision.status = DecisionStatus.APPROVED
            decision.execution_allowed = True
            decision.reasoning = "All roles approved"
        
        # Check if human review needed
        if decision.confidence < 0.7:
            decision.requires_human_review = True
        
        return decision
    
    def get_stats(self) -> dict:
        """Get session statistics."""
        return {
            "session_count": self._session_count,
            "planner": self.planner.get_stats(),
            "engineer": self.engineer.get_stats(),
            "scientist": self.scientist.get_stats(),
            "governor": self.governor.get_stats(),
            "archivist": self.archivist.get_stats(),
        }


class Council:
    """
    High-level Council interface.
    
    Simple wrapper around CouncilSession for easy use.
    """
    
    def __init__(self):
        self.session = CouncilSession()
    
    def deliberate(self, task: str, context: Optional[dict] = None) -> CouncilDecision:
        """Run council deliberation."""
        return self.session.deliberate(task, context)
    
    def get_stats(self) -> dict:
        """Get council statistics."""
        return self.session.get_stats()
