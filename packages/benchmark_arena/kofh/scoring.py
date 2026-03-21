"""
Score Calculation for King-of-the-Hill

Formula:
  final_score = quality * 0.6 + reliability * 0.2 + speed * 0.2
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown."""
    quality: float = 0.0        # 0-100
    reliability: float = 0.0     # 0-100
    speed: float = 0.0           # 0-100 (higher = faster)
    
    # Computed
    final_score: float = 0.0
    latency_ms: float = 0.0
    
    # Metadata
    test_count: int = 0
    passed_count: int = 0
    
    @property
    def quality_score(self) -> float:
        """Get quality component."""
        return self.quality * 0.6
    
    @property
    def reliability_score(self) -> float:
        """Get reliability component."""
        return self.reliability * 0.2
    
    @property
    def speed_score(self) -> float:
        """Get speed component."""
        return self.speed * 0.2
    
    def calculate_final(self):
        """Calculate final score from components."""
        self.final_score = (
            self.quality * 0.6 +
            self.reliability * 0.2 +
            self.speed * 0.2
        )
        return self.final_score
    
    def meets_threshold(self, min_quality: float = 80.0, min_reliability: float = 90.0) -> bool:
        """Check if scores meet minimum thresholds."""
        return (
            self.quality >= min_quality and
            self.reliability >= min_reliability
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "quality": self.quality,
            "reliability": self.reliability,
            "speed": self.speed,
            "final_score": self.final_score,
            "latency_ms": self.latency_ms,
            "test_count": self.test_count,
            "passed_count": self.passed_count,
            "components": {
                "quality_component": self.quality_score,
                "reliability_component": self.reliability_score,
                "speed_component": self.speed_score,
            }
        }


class ScoreCalculator:
    """Calculates and validates scores."""
    
    def __init__(
        self,
        min_quality: float = 80.0,
        min_reliability: float = 90.0,
        throne_buffer: float = 0.03,  # 3% buffer for throne swaps
    ):
        self.min_quality = min_quality
        self.min_reliability = min_reliability
        self.throne_buffer = throne_buffer
    
    def calculate(
        self,
        quality: float,
        reliability: float,
        latency_ms: float,
        max_latency_ms: float = 2000.0,
    ) -> ScoreBreakdown:
        """
        Calculate score from raw metrics.
        
        Args:
            quality: Quality score (0-100)
            reliability: Reliability score (0-100)
            latency_ms: Average latency in milliseconds
            max_latency_ms: Maximum acceptable latency
        
        Returns:
            ScoreBreakdown with all components
        """
        # Convert latency to speed score (faster = higher score)
        speed = max(0, 100 - (latency_ms / max_latency_ms * 100))
        
        breakdown = ScoreBreakdown(
            quality=quality,
            reliability=reliability,
            speed=speed,
            latency_ms=latency_ms,
        )
        
        breakdown.calculate_final()
        
        return breakdown
    
    def should_swap_throne(
        self,
        current_king_score: float,
        challenger_score: float,
    ) -> bool:
        """
        Determine if throne should swap.
        
        Challenger must exceed king's score by buffer percentage.
        """
        threshold = current_king_score * (1 + self.throne_buffer)
        return challenger_score > threshold
    
    def is_eligible(self, breakdown: ScoreBreakdown) -> bool:
        """Check if score meets minimum thresholds."""
        return breakdown.meets_threshold(
            self.min_quality,
            self.min_reliability
        )
