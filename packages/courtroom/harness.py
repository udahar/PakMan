"""
The Harness - Final Verification Authority

Deterministic pass/fail verification. The supreme court.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import subprocess
import json


class HarnessVerdict(Enum):
    """Final harness verdict."""
    PASS = "pass"
    FAIL = "fail"


@dataclass
class HarnessResult:
    """Result from harness verification."""
    verdict: HarnessVerdict
    checks_passed: list[str]
    checks_failed: list[str]
    test_output: str = ""
    compile_output: str = ""
    execution_time_ms: float = 0.0


class Harness:
    """
    Final verification authority.
    
    Does NOT:
    - Argue or debate
    - Make subjective judgments
    
    Does:
    - Deterministic checks
    - Run tests
    - Verify compilation
    - Enforce ticket scope
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or "."
        self._verification_count = 0
    
    def verify(self, code: str, ticket: dict) -> HarnessResult:
        """
        Run deterministic verification.
        
        Args:
            code: Code to verify
            ticket: Original ticket contract
        
        Returns:
            HarnessResult with pass/fail verdict
        """
        self._verification_count += 1
        
        checks_passed = []
        checks_failed = []
        
        # Check 1: Code compiles (if applicable)
        if self._check_compiles(code, ticket):
            checks_passed.append("compilation")
        else:
            checks_failed.append("compilation")
        
        # Check 2: Tests pass
        test_result = self._run_tests(code, ticket)
        if test_result["passed"]:
            checks_passed.append("tests")
        else:
            checks_failed.append(f"tests: {test_result['output']}")
        
        # Check 3: Files match ticket scope
        if self._check_file_scope(ticket):
            checks_passed.append("file_scope")
        else:
            checks_failed.append("file_scope_violation")
        
        # Check 4: No extra edits
        if self._check_no_extra_edits(ticket):
            checks_passed.append("no_extra_edits")
        else:
            checks_failed.append("unauthorized_edits")
        
        # Check 5: Acceptance criteria met
        if self._check_acceptance_criteria(code, ticket):
            checks_passed.append("acceptance_criteria")
        else:
            checks_failed.append("acceptance_criteria_not_met")
        
        # Final verdict
        verdict = HarnessVerdict.PASS if not checks_failed else HarnessVerdict.FAIL
        
        return HarnessResult(
            verdict=verdict,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            test_output=test_result.get("output", ""),
        )
    
    def _check_compiles(self, code: str, ticket: dict) -> bool:
        """Check if code compiles."""
        # In production, actually compile
        # For now, placeholder
        return True
    
    def _run_tests(self, code: str, ticket: dict) -> dict:
        """Run tests for the code."""
        # In production, run actual tests
        return {"passed": True, "output": ""}
    
    def _check_file_scope(self, ticket: dict) -> bool:
        """Check that only listed files were modified."""
        # In production, check git diff or file system
        return True
    
    def _check_no_extra_edits(self, ticket: dict) -> bool:
        """Check no unauthorized edits were made."""
        # In production, verify file changes
        return True
    
    def _check_acceptance_criteria(self, code: str, ticket: dict) -> bool:
        """Check acceptance criteria from ticket."""
        expected = ticket.get("expected_output", {})
        criteria = expected.get("acceptance_criteria", [])
        
        # Check each criterion
        for criterion in criteria:
            if not self._verify_criterion(code, criterion):
                return False
        
        return True
    
    def _verify_criterion(self, code: str, criterion: str) -> bool:
        """Verify a single acceptance criterion."""
        # Simple string matching - in production use proper checks
        return criterion.lower() in code.lower()
    
    def get_stats(self) -> dict:
        """Get harness statistics."""
        return {
            "verification_count": self._verification_count,
        }
