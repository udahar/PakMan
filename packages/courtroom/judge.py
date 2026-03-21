"""
The Judge - Decision Maker

Reviews critic's arguments and decides: pass to harness or reject.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class JudgeVerdict(Enum):
    """Judge's decision."""
    PASS_TO_HARNESS = "pass_to_harness"
    REJECT = "reject"
    REJECT_WITH_FIXES = "reject_with_fixes"


@dataclass
class JudgeDecision:
    """Judge's decision with reasoning."""
    verdict: JudgeVerdict
    reasoning: str
    required_fixes: list[str]
    dismissed_criticisms: list[str]
    confidence: float = 0.0


class Judge:
    """
    Reviews critic's arguments and makes decisions.
    
    Does NOT:
    - Write code
    - Argue with critic
    - Ignore valid criticisms
    
    Does:
    - Evaluate critic's findings
    - Dismiss invalid criticisms
    - Decide if code goes to harness
    """
    
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self._call_count = 0
        self._decisions: list[JudgeDecision] = []
    
    def decide(
        self,
        code: str,
        criticism,
        ticket: dict,
    ) -> JudgeDecision:
        """
        Make a decision on the code.
        
        Args:
            code: The code to review
            criticism: Critic's findings
            ticket: Original ticket contract
        
        Returns:
            JudgeDecision with verdict and reasoning
        """
        self._call_count += 1
        
        # Build judge prompt
        prompt = self._build_prompt(code, criticism, ticket)
        
        # Call model
        output = self._call_model(prompt)
        
        # Parse decision
        decision = self._parse_decision(output)
        
        # Record decision
        self._decisions.append(decision)
        
        return decision
    
    def _build_prompt(self, code: str, criticism, ticket: dict) -> str:
        """Build the judge prompt."""
        return f"""
You are a JUDGE. Review the critic's arguments and make a decision.

══════════════════════════════════════════════════════════════
CODE
══════════════════════════════════════════════════════════════

{code}

══════════════════════════════════════════════════════════════
CRITIC'S FINDINGS
══════════════════════════════════════════════════════════════

Overall Verdict: {criticism.overall_verdict}
Confidence: {criticism.confidence:.1%}

{criticism.reasoning}

Flaws Found: {len(criticism.flaws) if hasattr(criticism, 'flaws') else 0}
Ticket Violations: {len(criticism.ticket_violations) if hasattr(criticism, 'ticket_violations') else 0}
Security Issues: {len(criticism.security_issues) if hasattr(criticism, 'security_issues') else 0}

══════════════════════════════════════════════════════════════
TICKET CONTRACT
══════════════════════════════════════════════════════════════

Objective: {ticket.get('objective', 'N/A')}

Constraints:
{self._bullet_list(ticket.get('constraints', []))}

══════════════════════════════════════════════════════════════
YOUR DECISION
══════════════════════════════════════════════════════════════

Decide:

1. Are the critic's findings VALID?
   - Critical bugs → REJECT
   - Major violations → REJECT
   - Minor issues → PASS with notes
   - Invalid criticisms → DISMISS and PASS

2. Should this code go to HARNESS?
   - Only if no critical/major issues
   - Only if ticket is fulfilled
   - Only if security is sound

══════════════════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════════════════

Respond with:

VERDICT: [pass_to_harness | reject | reject_with_fixes]

REASONING:
[Explain your decision]

REQUIRED FIXES:
- [List fixes needed if reject_with_fixes]

DISMISSED CRITICISMS:
- [List criticisms you found invalid]

CONFIDENCE: [0.0-1.0]
"""
    
    def _call_model(self, prompt: str) -> str:
        """Call the model to generate decision."""
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            
            return ""
            
        except Exception as e:
            return f"# Error: {e}"
    
    def _parse_decision(self, output: str) -> JudgeDecision:
        """Parse model output into JudgeDecision."""
        # Default decision
        decision = JudgeDecision(
            verdict=JudgeVerdict.REJECT,
            reasoning="Parsing failed",
            required_fixes=[],
            dismissed_criticisms=[],
            confidence=0.5,
        )
        
        # Parse verdict
        if "VERDICT: pass_to_harness" in output:
            decision.verdict = JudgeVerdict.PASS_TO_HARNESS
        elif "VERDICT: reject_with_fixes" in output:
            decision.verdict = JudgeVerdict.REJECT_WITH_FIXES
        elif "VERDICT: reject" in output:
            decision.verdict = JudgeVerdict.REJECT
        
        # Parse reasoning
        if "REASONING:" in output:
            reasoning_section = output.split("REASONING:")[1]
            if "REQUIRED FIXES:" in reasoning_section:
                decision.reasoning = reasoning_section.split("REQUIRED FIXES:")[0].strip()
            else:
                decision.reasoning = reasoning_section.split("\n\n")[0].strip()
        
        # Parse required fixes
        if "REQUIRED FIXES:" in output:
            fixes_section = output.split("REQUIRED FIXES:")[1]
            if "DISMISSED CRITICISMS:" in fixes_section:
                fixes_section = fixes_section.split("DISMISSED CRITICISMS:")[0]
            decision.required_fixes = self._extract_list(fixes_section)
        
        # Parse dismissed criticisms
        if "DISMISSED CRITICISMS:" in output:
            dismissed_section = output.split("DISMISSED CRITICISMS:")[1]
            if "CONFIDENCE:" in dismissed_section:
                dismissed_section = dismissed_section.split("CONFIDENCE:")[0]
            decision.dismissed_criticisms = self._extract_list(dismissed_section)
        
        # Parse confidence
        if "CONFIDENCE:" in output:
            try:
                conf_part = output.split("CONFIDENCE:")[1].split("\n")[0].strip()
                decision.confidence = float(conf_part)
            except:
                pass
        
        return decision
    
    def _extract_list(self, text: str) -> list[str]:
        """Extract bullet list from text."""
        items = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                items.append(line[1:].strip())
        return items
    
    def _bullet_list(self, items: list) -> str:
        """Format items as bullet list."""
        if not items:
            return "  (none)"
        return "\n".join(f"  • {item}" for item in items)
    
    def get_stats(self) -> dict:
        """Get judge statistics."""
        verdict_counts = {}
        for d in self._decisions:
            verdict = d.verdict.value
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        return {
            "call_count": self._call_count,
            "model": self.model,
            "decisions": verdict_counts,
            "avg_confidence": sum(d.confidence for d in self._decisions) / len(self._decisions) if self._decisions else 0,
        }
