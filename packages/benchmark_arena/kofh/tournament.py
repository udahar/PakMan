"""
King-of-the-Hill Tournament System

Main tournament orchestrator.
"""

import json
from datetime import datetime
from typing import Any, Optional

from kofh.scoring import ScoreCalculator, ScoreBreakdown
from kofh.throne import ThroneManager, ThroneHolder
from kofh.leaderboard import Leaderboard


class TournamentSystem:
    """
    Main tournament system.
    
    Manages model evaluations, throne competitions, and leaderboards.
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
        self.scoring = ScoreCalculator(
            min_quality=self.config.get("min_quality", 80.0),
            min_reliability=self.config.get("min_reliability", 90.0),
            throne_buffer=self.config.get("throne_buffer", 0.03),
        )
        
        self.thrones = ThroneManager()
        self.leaderboard = Leaderboard()
        
        # Track all evaluations
        self._evaluations: list[dict] = []
    
    def evaluate_model(
        self,
        model: str,
        role: str,
        test_results: dict[str, Any],
    ) -> ScoreBreakdown:
        """
        Evaluate a model for a specific role.
        
        Args:
            model: Model name
            role: Role to evaluate for
            test_results: Dict with quality, reliability, latency metrics
        
        Returns:
            ScoreBreakdown with all components
        """
        # Extract metrics
        quality = test_results.get("quality", 0.0)
        reliability = test_results.get("reliability", 0.0)
        latency_ms = test_results.get("latency_ms", 1000.0)
        
        # Calculate score
        breakdown = self.scoring.calculate(
            quality=quality,
            reliability=reliability,
            latency_ms=latency_ms,
        )
        
        # Record evaluation
        self._evaluations.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "role": role,
            "score": breakdown.final_score,
            "breakdown": breakdown.to_dict(),
        })
        
        return breakdown
    
    def challenge_throne(
        self,
        model: str,
        role: str,
        test_results: dict[str, Any],
    ) -> dict:
        """
        Challenge the current throne holder.
        
        Args:
            model: Challenger model name
            role: Role to challenge
            test_results: Test results dict
        
        Returns:
            Dict with challenge result
        """
        # Evaluate challenger
        breakdown = self.evaluate_model(model, role, test_results)
        
        # Check eligibility
        if not self.scoring.is_eligible(breakdown):
            return {
                "success": False,
                "reason": "Score below threshold",
                "score": breakdown.final_score,
                "threshold_quality": self.scoring.min_quality,
                "threshold_reliability": self.scoring.min_reliability,
            }
        
        # Get current king
        current_king = self.thrones.get_king(role)
        current_score = self.thrones.get_king_score(role)
        
        if not current_king:
            # No king - auto-crown
            self.thrones.crown_king(model, role, breakdown.final_score)
            return {
                "success": True,
                "crowned": True,
                "reason": "No current king",
                "score": breakdown.final_score,
            }
        
        # Check if challenger wins
        if self.scoring.should_swap_throne(current_score, breakdown.final_score):
            # Dethrone and crown new king
            self.thrones.crown_king(model, role, breakdown.final_score)
            
            return {
                "success": True,
                "dethroned": current_king,
                "new_king": model,
                "old_score": current_score,
                "new_score": breakdown.final_score,
                "reason": "Challenger exceeded throne buffer",
            }
        else:
            # King survives
            self.thrones.record_defense(role)
            
            return {
                "success": False,
                "king_survives": current_king,
                "challenger": model,
                "king_score": current_score,
                "challenger_score": breakdown.final_score,
                "reason": "Challenger did not exceed buffer",
            }
    
    def get_throne_holder(self, role: str) -> Optional[str]:
        """Get current throne holder for a role."""
        return self.thrones.get_king(role)
    
    def get_leaderboard(self, role: str) -> str:
        """Get formatted leaderboard for a role."""
        holders = self.thrones.get_leaderboard(role)
        return self.leaderboard.format_leaderboard(role, holders)
    
    def get_all_leaderboards(self) -> str:
        """Get all leaderboards."""
        all_leaderboards = self.thrones.get_full_leaderboard()
        return self.leaderboard.format_all_leaderboards(all_leaderboards)
    
    def get_stats(self) -> dict:
        """Get tournament statistics."""
        return {
            "evaluations": len(self._evaluations),
            "thrones": self.thrones.get_stats(),
        }
    
    def export_state(self) -> str:
        """Export tournament state as JSON."""
        state = {
            "evaluations": self._evaluations,
            "thrones": self.thrones.get_full_leaderboard(),
            "stats": self.get_stats(),
        }
        return json.dumps(state, indent=2, default=str)
