"""
Health Checks Module
"""

from typing import Dict, Any, Callable, List
from dataclasses import dataclass


@dataclass
class HealthCheck:
    """A single health check."""

    name: str
    check_fn: Callable[[], Dict[str, Any]]
    critical: bool = True


class HealthChecker:
    """
    Custom health checks registry.

    Usage:
        checker = HealthChecker()
        checker.register("my_check", my_check_fn)
        results = checker.run_all()
    """

    def __init__(self):
        self.checks: List[HealthCheck] = []

    def register(self, name: str, check_fn: Callable[[], Dict], critical: bool = True):
        """Register a health check."""
        self.checks.append(HealthCheck(name=name, check_fn=check_fn, critical=critical))

    def run_all(self) -> Dict[str, Any]:
        """Run all registered checks."""
        results = {}

        for check in self.checks:
            try:
                results[check.name] = check.check_fn()
            except Exception as e:
                results[check.name] = {"ok": False, "error": str(e), "status": "error"}

        return results

    def get_status(self) -> str:
        """Get overall status."""
        results = self.run_all()

        critical_failures = sum(
            1
            for c in self.checks
            if c.critical and results.get(c.name, {}).get("ok") == False
        )

        if critical_failures > 0:
            return "degraded"
        return "healthy"


def create_health_check(name: str, fn: Callable) -> HealthCheck:
    """Create a health check."""
    return HealthCheck(name=name, check_fn=fn)
