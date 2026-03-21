"""
Throne Management

Tracks who holds each throne and handles swaps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ThroneHolder:
    """Current or historical throne holder."""
    model: str
    role: str
    score: float
    crowned_at: datetime = field(default_factory=datetime.now)
    dethroned_at: Optional[datetime] = None
    reign_duration_days: float = 0.0
    defenses: int = 0  # Number of successful defenses
    
    @property
    def is_current(self) -> bool:
        """Check if this is the current holder."""
        return self.dethroned_at is None
    
    def dethrone(self):
        """Mark as dethroned."""
        self.dethroned_at = datetime.now()
        reign = self.dethroned_at - self.crowned_at
        self.reign_duration_days = reign.total_seconds() / 86400
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "role": self.role,
            "score": self.score,
            "crowned_at": self.crowned_at.isoformat(),
            "dethroned_at": self.dethroned_at.isoformat() if self.dethroned_at else None,
            "reign_duration_days": self.reign_duration_days,
            "defenses": self.defenses,
            "is_current": self.is_current,
        }


class ThroneManager:
    """
    Manages throne seats for all roles.
    
    Tracks current kings and historical holders.
    """
    
    ROLES = ["planner", "engineer", "scientist", "analyst"]
    
    def __init__(self):
        self._thrones: dict[str, Optional[ThroneHolder]] = {
            role: None for role in self.ROLES
        }
        self._history: list[ThroneHolder] = []
    
    def get_king(self, role: str) -> Optional[str]:
        """Get current king for a role."""
        holder = self._thrones.get(role)
        return holder.model if holder else None
    
    def get_king_score(self, role: str) -> Optional[float]:
        """Get current king's score."""
        holder = self._thrones.get(role)
        return holder.score if holder else None
    
    def crown_king(self, model: str, role: str, score: float) -> ThroneHolder:
        """
        Crown a new king.
        
        If there's a current king, they are dethroned first.
        """
        # Dethrone current king if exists
        current = self._thrones.get(role)
        if current:
            current.dethrone()
            self._history.append(current)
        
        # Crown new king
        new_king = ThroneHolder(
            model=model,
            role=role,
            score=score,
        )
        
        self._thrones[role] = new_king
        
        return new_king
    
    def record_defense(self, role: str):
        """Record successful throne defense."""
        holder = self._thrones.get(role)
        if holder:
            holder.defenses += 1
    
    def get_all_kings(self) -> dict[str, Optional[str]]:
        """Get all current kings."""
        return {
            role: self.get_king(role)
            for role in self.ROLES
        }
    
    def get_leaderboard(self, role: str) -> list[ThroneHolder]:
        """Get leaderboard for a role (current + historical)."""
        current = self._thrones.get(role)
        historical = [h for h in self._history if h.role == role]
        
        all_holders = []
        if current:
            all_holders.append(current)
        all_holders.extend(historical)
        
        # Sort by score descending
        return sorted(all_holders, key=lambda h: h.score, reverse=True)
    
    def get_full_leaderboard(self) -> dict[str, list[ThroneHolder]]:
        """Get leaderboards for all roles."""
        return {
            role: self.get_leaderboard(role)
            for role in self.ROLES
        }
    
    def get_stats(self) -> dict:
        """Get throne statistics."""
        current_kings = {k: v for k, v in self._thrones.items() if v}
        
        total_reigns = len(self._history) + len(current_kings)
        avg_reign_days = 0
        if self._history:
            avg_reign_days = sum(h.reign_duration_days for h in self._history) / len(self._history)
        
        return {
            "total_thrones": len(self.ROLES),
            "filled_thrones": len(current_kings),
            "total_reigns": total_reigns,
            "avg_reign_duration_days": avg_reign_days,
            "current_kings": {k: v.to_dict() for k, v in current_kings.items()},
        }
