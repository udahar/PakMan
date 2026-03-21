# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Vetter
Safety vetting system for prompts
"""

import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VetStatus(Enum):
    """Vetting status."""

    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass
class VetResult:
    """Result of vetting a prompt."""

    status: VetStatus
    score: float
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)


class PromptVetter:
    """
    Safety vetting system for prompts.

    Checks for:
    - Malicious patterns
    - Harmful content
    - Security issues
    - Variable syntax validity
    """

    REJECT_PATTERNS = [
        (
            r"hack\s+(the\s+)?(system|password|server|account)",
            "Attempted hacking content",
        ),
        (r"bypass\s+(security|authentication|permission)", "Security bypass attempt"),
        (
            r"steal\s+(data|information|credentials|password)",
            "Theft/infiltration attempt",
        ),
        (r"destroy\s+(data|system|file|network)", "Destructive intent"),
        (r"malware|virus|trojan|ransomware", "Malware-related content"),
        (r"generate\s+(harmful|illegal|weapon)", "Harmful content generation"),
    ]

    FLAG_PATTERNS = [
        (r"sudo|root|admin\s+access", "Elevated privileges"),
        (r"delete\s+.*database|drop\s+table", "Destructive database operations"),
        (r"exec\s*\(|system\s*\(", "Code execution patterns"),
        (r"sql\s+injection", "SQL injection patterns"),
        (r"prompt\s+injection|jailbreak", "Prompt injection patterns"),
    ]

    SUSPICIOUS_VARS = [
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "credential",
        "ssn",
        "social_security",
        "credit_card",
        "cc_number",
    ]

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.stats = {"approved": 0, "flagged": 0, "rejected": 0, "pending": 0}

    def vet(self, prompt_text: str, act_name: str = "") -> VetResult:
        """
        Vet a prompt for safety.

        Args:
            prompt_text: The prompt content
            act_name: Optional act name

        Returns:
            VetResult with status and details
        """
        issues = []
        warnings = []
        passed_checks = []

        prompt_lower = prompt_text.lower()

        for pattern, desc in self.REJECT_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                issues.append(f"Rejected: {desc}")

        for pattern, desc in self.FLAG_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                warnings.append(f"Flagged: {desc}")

        var_issues = self._check_variables(prompt_text)
        issues.extend(var_issues["issues"])
        warnings.extend(var_issues["warnings"])

        if self._has_dangerous_variables(prompt_text):
            warnings.append("Contains potentially sensitive variable names")

        if self._has_incomplete_variables(prompt_text):
            issues.append("Incomplete or malformed variables")

        passed_checks.extend(self._get_passed_checks(issues, warnings))

        score = self._calculate_score(issues, warnings)

        if issues:
            status = VetStatus.REJECTED
            self.stats["rejected"] += 1
        elif warnings and self.strict:
            status = VetStatus.FLAGGED
            self.stats["flagged"] += 1
        elif warnings:
            status = VetStatus.FLAGGED
            self.stats["flagged"] += 1
        else:
            status = VetStatus.APPROVED
            self.stats["approved"] += 1

        return VetResult(
            status=status,
            score=score,
            issues=issues,
            warnings=warnings,
            passed_checks=passed_checks,
        )

    def _check_variables(self, text: str) -> Dict[str, List[str]]:
        """Check variable syntax."""
        issues = []
        warnings = []

        unclosed = text.count("${") - text.count("}")
        if unclosed > 0:
            issues.append(f"Unclosed variables: {unclosed}")

        empty_var = re.findall(r"\$\{\}", text)
        if empty_var:
            warnings.append("Empty variable placeholder found")

        return {"issues": issues, "warnings": warnings}

    def _has_dangerous_variables(self, text: str) -> bool:
        """Check for dangerous variable names."""
        for var in self.SUSPICIOUS_VARS:
            if re.search(rf"\${{\s*{var}\s*}}", text, re.IGNORECASE):
                return True
        return False

    def _has_incomplete_variables(self, text: str) -> bool:
        """Check for incomplete variable syntax."""
        return "${" in text and "}" not in text

    def _get_passed_checks(self, issues: List[str], warnings: List[str]) -> List[str]:
        """List passed checks."""
        passed = []

        if not any("Reject" in i for i in issues):
            passed.append("No rejection patterns found")

        if not any("security" in i.lower() or "bypass" in i.lower() for i in issues):
            passed.append("No security issues detected")

        if not any("hack" in i.lower() for i in issues):
            passed.append("No hacking patterns detected")

        return passed

    def _calculate_score(self, issues: List[str], warnings: List[str]) -> float:
        """Calculate safety score (0-1)."""
        score = 1.0
        score -= len(issues) * 0.3
        score -= len(warnings) * 0.1
        return max(0.0, min(1.0, score))

    def vet_batch(self, prompts: List[Tuple[str, str]]) -> List[VetResult]:
        """Vet multiple prompts."""
        return [self.vet(text, act) for act, text in prompts]

    def get_stats(self) -> Dict[str, Any]:
        """Get vetting statistics."""
        total = sum(self.stats.values())
        return {
            "total_vetted": total,
            **self.stats,
            "approval_rate": self.stats["approved"] / total if total > 0 else 0,
        }


def create_prompt_vetter(strict: bool = False) -> PromptVetter:
    """Factory function to create prompt vetter."""
    return PromptVetter(strict=strict)
