"""
Council Decision Aggregation

Combines input from all roles into a unified decision.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime


class DecisionStatus(Enum):
    """Status of a council decision."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class CouncilDecision:
    """
    A unified decision from the council.
    
    Aggregates input from all five roles.
    """
    
    task: str
    status: DecisionStatus
    proposed_pipeline: list = field(default_factory=list)
    
    # Role votes
    planner_input: Optional[dict] = None
    engineer_input: Optional[dict] = None
    scientist_input: Optional[dict] = None
    governor_input: Optional[dict] = None
    archivist_input: Optional[dict] = None
    
    # Decision metadata
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Execution
    requires_human_review: bool = False
    execution_allowed: bool = False
    
    @property
    def approved(self) -> bool:
        """Check if decision is approved for execution."""
        return self.status == DecisionStatus.APPROVED and self.execution_allowed
    
    @property
    def rejected(self) -> bool:
        """Check if decision was rejected."""
        return self.status == DecisionStatus.REJECTED
    
    def get_role_votes(self) -> dict:
        """Get all role inputs."""
        return {
            "planner": self.planner_input,
            "engineer": self.engineer_input,
            "scientist": self.scientist_input,
            "governor": self.governor_input,
            "archivist": self.archivist_input,
        }
    
    def calculate_confidence(self) -> float:
        """Calculate overall confidence from role inputs."""
        confidences = []
        
        if self.planner_input:
            confidences.append(self.planner_input.get("confidence", 0.5))
        if self.engineer_input:
            confidences.append(self.engineer_input.get("confidence", 0.5))
        if self.scientist_input:
            confidences.append(self.scientist_input.get("confidence", 0.5))
        if self.governor_input:
            confidences.append(self.governor_input.get("confidence", 1.0))
        
        if not confidences:
            return 0.0
        
        self.confidence = sum(confidences) / len(confidences)
        return self.confidence
    
    def to_dict(self) -> dict:
        """Convert decision to dictionary."""
        return {
            "task": self.task,
            "status": self.status.value,
            "proposed_pipeline": self.proposed_pipeline,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "requires_human_review": self.requires_human_review,
            "execution_allowed": self.execution_allowed,
            "role_votes": self.get_role_votes(),
        }
    
    def __str__(self) -> str:
        status_emoji = {
            DecisionStatus.APPROVED: "✅",
            DecisionStatus.REJECTED: "❌",
            DecisionStatus.PENDING: "⏳",
            DecisionStatus.NEEDS_REVISION: "🔄",
        }
        return f"[{status_emoji.get(self.status, '?')}] {self.task}"
