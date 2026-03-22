"""
Courtroom Session Management

Orchestrates the full courtroom loop.
"""

from dataclasses import dataclass
from typing import Optional

from .scribe import Scribe, ScribeOutput
from .critic import Critic, Criticism
from .judge import Judge, JudgeDecision, JudgeVerdict
from .harness import Harness, HarnessResult, HarnessVerdict


@dataclass
class CourtroomResult:
    """Final result from courtroom session."""
    passed: bool
    code: str
    harness_result: Optional[HarnessResult] = None
    judge_decision: Optional[JudgeDecision] = None
    criticism: Optional[Criticism] = None
    revisions: int = 0
    max_revisions_reached: bool = False
    error: Optional[str] = None


class CourtroomSession:
    """
    Manages a full courtroom session.
    
    Flow:
    1. Scribe writes code from ticket
    2. Critic attacks code
    3. Judge reviews and decides
    4. If approved → Harness verifies
    5. If rejected → Back to scribe (revision)
    """
    
    def __init__(
        self,
        scribe: Optional[Scribe] = None,
        critic: Optional[Critic] = None,
        judge: Optional[Judge] = None,
        harness: Optional[Harness] = None,
        max_revisions: int = 3,
    ):
        self.scribe = scribe or Scribe()
        self.critic = critic or Critic()
        self.judge = judge or Judge()
        self.harness = harness or Harness()
        
        self.max_revisions = max_revisions
        self._session_count = 0
    
    def run(self, ticket: dict) -> CourtroomResult:
        """
        Run a full courtroom session.
        
        Args:
            ticket: Filled ticket contract
        
        Returns:
            CourtroomResult with final verdict
        """
        self._session_count += 1
        
        revisions = 0
        current_ticket = ticket.copy()
        
        while revisions < self.max_revisions:
            # Phase 1: Scribe writes code
            scribe_output = self.scribe.write(current_ticket)
            
            # Phase 2: Critic attacks
            criticism = self.critic.attack(scribe_output.code, ticket)
            
            # Phase 3: Judge decides
            judge_decision = self.judge.decide(
                scribe_output.code,
                criticism,
                ticket,
            )
            
            # Check judge's decision
            if judge_decision.verdict == JudgeVerdict.REJECT:
                revisions += 1
                current_ticket = self._add_revision_notes(
                    current_ticket,
                    judge_decision.required_fixes,
                )
                continue
            
            # Judge approved → Phase 4: Harness verifies
            harness_result = self.harness.verify(scribe_output.code, ticket)
            
            if harness_result.verdict == HarnessVerdict.PASS:
                return CourtroomResult(
                    passed=True,
                    code=scribe_output.code,
                    harness_result=harness_result,
                    judge_decision=judge_decision,
                    criticism=criticism,
                    revisions=revisions,
                )
            else:
                # Harness failed
                revisions += 1
                current_ticket = self._add_revision_notes(
                    current_ticket,
                    harness_result.checks_failed,
                )
        
        # Max revisions reached
        return CourtroomResult(
            passed=False,
            code=scribe_output.code,
            harness_result=harness_result if 'harness_result' in locals() else None,
            judge_decision=judge_decision if 'judge_decision' in locals() else None,
            criticism=criticism if 'criticism' in locals() else None,
            revisions=revisions,
            max_revisions_reached=True,
            error="Max revisions reached without passing",
        )
    
    def _add_revision_notes(self, ticket: dict, fixes: list[str]) -> dict:
        """Add revision notes to ticket."""
        revised = ticket.copy()
        revised["revision_notes"] = fixes
        revised["revision_count"] = revised.get("revision_count", 0) + 1
        return revised
    
    def get_stats(self) -> dict:
        """Get session statistics."""
        return {
            "session_count": self._session_count,
            "scribe": self.scribe.get_stats(),
            "critic": self.critic.get_stats(),
            "judge": self.judge.get_stats(),
            "harness": self.harness.get_stats(),
        }
