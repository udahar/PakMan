"""
The Critic - Prosecution (Loki's Role)

Finds flaws, bugs, and ticket violations in code.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Flaw:
    """A flaw found in the code."""
    type: str  # bug, security, performance, ticket_violation, etc.
    severity: str  # critical, major, minor
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class Criticism:
    """Output from the critic."""
    flaws: list[Flaw] = field(default_factory=list)
    ticket_violations: list[str] = field(default_factory=list)
    security_issues: list[str] = field(default_factory=list)
    missing_features: list[str] = field(default_factory=list)
    overall_verdict: str = "reject"  # reject, pass_with_notes, approve
    confidence: float = 0.0
    reasoning: str = ""


class Critic:
    """
    Code critic that finds flaws and violations.
    
    Job: PROVE THE CODE IS WRONG
    """
    
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self._call_count = 0
    
    def attack(self, code: str, ticket: dict) -> Criticism:
        """
        Attack code and find all flaws.
        
        Args:
            code: Code to review
            ticket: Original ticket contract
        
        Returns:
            Criticism with all findings
        """
        self._call_count += 1
        
        # Build critic prompt
        prompt = self._build_prompt(code, ticket)
        
        # Call model
        output = self._call_model(prompt)
        
        # Parse criticism
        criticism = self._parse_criticism(output)
        
        return criticism
    
    def _build_prompt(self, code: str, ticket: dict) -> str:
        """Build the critic prompt."""
        return f"""
You are a CODE CRITIC. Your job is to PROVE this code is WRONG.

Be BRUTAL. Find EVERY flaw.

══════════════════════════════════════════════════════════════
CODE TO REVIEW
══════════════════════════════════════════════════════════════

{code}

══════════════════════════════════════════════════════════════
TICKET CONTRACT (CHECK FOR VIOLATIONS)
══════════════════════════════════════════════════════════════

OBJECTIVE:
{ticket.get('objective', 'N/A')}

CONSTRAINTS:
{self._bullet_list(ticket.get('constraints', []))}

FILES TO MODIFY:
{self._list_files(ticket.get('files_to_modify', []))}

EXPECTED OUTPUT:
{ticket.get('expected_output', {})}

══════════════════════════════════════════════════════════════
YOUR MISSION: DESTROY THIS CODE
══════════════════════════════════════════════════════════════

Find:

1. BUGS
   - Logic errors
   - Edge cases not handled
   - Missing error handling
   - Null/None issues

2. TICKET VIOLATIONS
   - Modified files not listed
   - Missing required features
   - Added unrequested features
   - Violated constraints

3. SECURITY ISSUES
   - Injection vulnerabilities
   - Unsafe operations
   - Missing validation
   - Exposed secrets

4. PERFORMANCE PROBLEMS
   - Inefficient algorithms
   - Unnecessary allocations
   - Memory leaks
   - Slow operations

5. CODE QUALITY
   - Poor naming
   - Missing documentation
   - Inconsistent style
   - Complex logic

══════════════════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════════════════

Respond with:

FLAWS:
1. [type] [severity] Line X: Description
   Suggestion: ...

2. [type] [severity] Line Y: Description
   Suggestion: ...

TICKET VIOLATIONS:
- ...

SECURITY ISSUES:
- ...

MISSING FEATURES:
- ...

OVERALL VERDICT: [reject | pass_with_notes | approve]

CONFIDENCE: [0.0-1.0]

REASONING:
[Brief summary of your decision]
"""
    
    def _call_model(self, prompt: str) -> str:
        """Call the model to generate criticism."""
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            
            return ""
            
        except Exception as e:
            return f"# Error calling model: {e}"
    
    def _parse_criticism(self, output: str) -> Criticism:
        """Parse model output into Criticism object."""
        criticism = Criticism()
        
        # Simple parsing - in production use better extraction
        if "OVERALL VERDICT: reject" in output.lower():
            criticism.overall_verdict = "reject"
        elif "OVERALL VERDICT: pass_with_notes" in output.lower():
            criticism.overall_verdict = "pass_with_notes"
        else:
            criticism.overall_verdict = "approve"
        
        # Extract confidence
        if "CONFIDENCE:" in output:
            try:
                conf_part = output.split("CONFIDENCE:")[1].split("\n")[0].strip()
                criticism.confidence = float(conf_part)
            except:
                criticism.confidence = 0.5
        
        # Extract reasoning
        if "REASONING:" in output:
            criticism.reasoning = output.split("REASONING:")[1].strip()
        
        # Count flaws (simplified)
        flaw_count = output.count("[critical]") + output.count("[major]")
        if flaw_count > 5:
            criticism.overall_verdict = "reject"
        
        return criticism
    
    def _bullet_list(self, items: list) -> str:
        """Format items as bullet list."""
        if not items:
            return "  (none)"
        return "\n".join(f"  • {item}" for item in items)
    
    def _list_files(self, items: list) -> str:
        """Format file list."""
        if not items:
            return "  (none)"
        return "\n".join(f"  - {item}" for item in items)
    
    def get_stats(self) -> dict:
        """Get critic statistics."""
        return {
            "call_count": self._call_count,
            "model": self.model,
        }


class LokiCritic(Critic):
    """
    Loki-specific critic - extra brutal.
    
    Loki's specialty: finding hidden flaws and edge cases.
    """
    
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        super().__init__(model)
        self.loki_mode = True  # Extra aggressive
    
    def attack(self, code: str, ticket: dict) -> Criticism:
        """Loki's attack - more aggressive than standard critic."""
        # In production, Loki would have custom prompts
        # For now, use standard critic with extra aggression
        return super().attack(code, ticket)
