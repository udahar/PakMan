import os
import json
import hashlib
import re
from collections import defaultdict
from datetime import datetime
from dataclasses import asdict
from typing import Optional

from .models import Action, FilterType, Severity, FilterResult, AuditEvent, Filter
from .filters_input import EnhancedInjectionFilter, SocialEngineeringFilter, OutputValidationFilter
from .filters_output import PIIFilter, SecretsFilter, HarmfulContentFilter, ProfanityFilter, FormatValidator, LengthLimitFilter

class SafetySentry:
    """
    Main safety guardrail system.

    Chains multiple filters together for comprehensive protection.
    """

    def __init__(
        self,
        storage_path: str = "logs/safety",
        strict_mode: bool = False,
    ):
        self.storage_path = storage_path
        self.strict_mode = strict_mode

        # Ensure storage exists
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(os.path.join(storage_path, "audit"), exist_ok=True)

        # Initialize filters
        self.input_filters: list[Filter] = []
        self.output_filters: list[Filter] = []

        # Audit
        self.audit_events: list[AuditEvent] = []

        # Stats
        self.total_checked = 0
        self.total_blocked = 0

        # Register default filters
        self._register_defaults()

    def _register_defaults(self):
        """Register default filter set"""
        # Input filters - USE ENHANCED VERSION
        self.add_filter(EnhancedInjectionFilter(), FilterType.INPUT)

        # Social engineering filter (NEW - blocks "grandma jailbreak" etc)
        self.add_filter(SocialEngineeringFilter(), FilterType.INPUT)

        # Output filters
        self.add_filter(PIIFilter(), FilterType.OUTPUT)
        self.add_filter(SecretsFilter(), FilterType.OUTPUT)
        self.add_filter(HarmfulContentFilter(), FilterType.OUTPUT)
        self.add_filter(ProfanityFilter(), FilterType.OUTPUT)
        self.add_filter(FormatValidator(), FilterType.OUTPUT)
        # Add output validation to detect compromised responses
        self.add_filter(OutputValidationFilter(), FilterType.OUTPUT)

    def add_filter(self, filter: Filter, filter_type: FilterType = FilterType.BOTH):
        """Add a filter to the pipeline"""
        if filter_type in (FilterType.INPUT, FilterType.BOTH):
            self.input_filters.append(filter)
        if filter_type in (FilterType.OUTPUT, FilterType.BOTH):
            self.output_filters.append(filter)

    def remove_filter(self, filter_name: str):
        """Remove a filter by name"""
        self.input_filters = [f for f in self.input_filters if f.name != filter_name]
        self.output_filters = [f for f in self.output_filters if f.name != filter_name]

    def check_input(self, text: str, session_id: str = "default") -> FilterResult:
        """Check input before LLM processing"""
        self.total_checked += 1

        current = text
        results = []

        for filter in self.input_filters:
            if not filter.enabled:
                continue

            result = filter.check(current)
            results.append(asdict(result))

            if not result.passed:
                if result.action == Action.BLOCK:
                    self.total_blocked += 1
                    self._save_audit(session_id, "input", text, results, result)
                    return result
                elif result.action == Action.MODIFY and result.replacement:
                    current = result.replacement

        # Input passed
        return FilterResult(
            passed=True,
            action=Action.PASS,
            filter_name="input_pipeline",
            replacement=current,
        )

    def check_output(
        self, text: str, session_id: str = "default", original_input: str = ""
    ) -> FilterResult:
        """Check output after LLM processing"""
        self.total_checked += 1

        current = text
        results = []

        for filter in self.output_filters:
            if not filter.enabled:
                continue

            result = filter.check(current)
            results.append(asdict(result))

            if result.action == Action.BLOCK:
                self.total_blocked += 1
                self._save_audit(session_id, "output", text, results, result)
                return FilterResult(
                    passed=False,
                    action=Action.BLOCK,
                    filter_name="output_pipeline",
                    severity=Severity.CRITICAL.value,
                    reason=f"Blocked by {result.filter_name}: {result.reason}",
                    replacement="[Content blocked by Safety Sentry]",
                )
            elif result.action == Action.MODIFY and result.replacement:
                current = result.replacement
            elif result.action == Action.FLAG:
                pass

        # Output passed
        self._save_audit(
            session_id,
            "output",
            text,
            results,
            FilterResult(passed=True, action=Action.PASS, filter_name=""),
        )

        return FilterResult(
            passed=True,
            action=Action.PASS,
            filter_name="output_pipeline",
            replacement=current,
        )

    def _save_audit(
        self,
        session_id: str,
        direction: str,
        original: str,
        results: list,
        final_result: FilterResult,
    ):
        """Save audit event to disk"""
        event = AuditEvent(
            event_id=hashlib.md5(
                f"{session_id}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            direction=direction,
            session_id=session_id,
            original_content=original[:500],  # Truncate for storage
            filter_results=results,
            final_action=final_result.action.value,
            final_content=final_result.replacement[:500]
            if final_result.replacement
            else "",
            blocked=final_result.action == Action.BLOCK,
            timestamp=datetime.now().isoformat(),
        )

        self.audit_events.append(event)

        # Save to file
        filepath = os.path.join(
            self.storage_path, "audit", f"{direction}_{event.event_id}.json"
        )

        # Convert enums to strings for JSON serialization
        event_dict = asdict(event)
        for i, fr in enumerate(event_dict.get("filter_results", [])):
            if "action" in fr and hasattr(fr["action"], "value"):
                fr["action"] = fr["action"].value
        if "final_action" in event_dict and hasattr(
            event_dict["final_action"], "value"
        ):
            event_dict["final_action"] = event_dict["final_action"].value

        with open(filepath, "w") as f:
            json.dump(event_dict, f, indent=2)

    def get_stats(self) -> dict:
        """Get comprehensive statistics"""
        filter_stats = {}
        for f in self.input_filters + self.output_filters:
            filter_stats.update(f.get_stats())

        return {
            "total_checked": self.total_checked,
            "total_blocked": self.total_blocked,
            "block_rate": f"{(self.total_blocked / self.total_checked * 100):.2f}%"
            if self.total_checked > 0
            else "0%",
            "filters": filter_stats,
            "input_filters": [f.name for f in self.input_filters],
            "output_filters": [f.name for f in self.output_filters],
        }

    def get_recent_audit(self, limit: int = 10, blocked_only: bool = False) -> list:
        """Get recent audit events"""
        events = sorted(self.audit_events, key=lambda e: e.timestamp, reverse=True)

        if blocked_only:
            events = [e for e in events if e.blocked]

        return [
            {
                "event_id": e.event_id,
                "direction": e.direction,
                "timestamp": e.timestamp,
                "blocked": e.blocked,
                "filters_triggered": len(
                    [r for r in e.filter_results if not r.get("passed", True)]
                ),
            }
            for e in events[:limit]
        ]

    def get_dashboard_data(self) -> dict:
        """Get data for dashboard visualization"""
        # Group by hour
        hourly = defaultdict(lambda: {"checked": 0, "blocked": 0})

        for event in self.audit_events[-1000:]:  # Last 1000 events
            hour = event.timestamp[:13]  # YYYY-MM-DDTHH
            hourly[hour]["checked"] += 1
            if event.blocked:
                hourly[hour]["blocked"] += 1

        # Sort and limit to last 24 hours
        sorted_hours = sorted(hourly.items())[-24:]

        return {
            "stats": self.get_stats(),
            "recent_events": self.get_recent_audit(5),
            "hourly_trends": [
                {"hour": h, "checked": d["checked"], "blocked": d["blocked"]}
                for h, d in sorted_hours
            ],
        }

    def export_audit(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> str:
        """Export audit logs for a date range"""
        export_file = os.path.join(
            self.storage_path,
            f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
        )

        with open(export_file, "w") as f:
            for event in self.audit_events:
                if start_date and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp > end_date:
                    continue
                f.write(json.dumps(asdict(event)) + "\n")

        return export_file

def apply_instruction_distancing(user_input: str) -> str:
    """
    Apply instruction distancing (sandwich defense).
    Wraps user input to signal it's DATA, not instructions.
    """
    return f"""<|user_input|>\n{user_input}\n<|end_input|>"""


def create_paranoid_sentry() -> SafetySentry:
    """Create a maximally paranoid version with all defenses."""
    sentry = SafetySentry(strict_mode=True)
    sentry.add_filter(
        EnhancedInjectionFilter(sanitize=True, block_threshold=1), FilterType.INPUT
    )
    sentry.add_filter(LengthLimitFilter(max_tokens=2000), FilterType.OUTPUT)
    sentry.add_filter(OutputValidationFilter(), FilterType.OUTPUT)
    return sentry


# =============================================================================


def create_safety_sentry(strict_mode: bool = False) -> SafetySentry:
    """Factory function for creating a configured SafetySentry"""
    return SafetySentry(strict_mode=strict_mode)


def create_strict_sentry() -> SafetySentry:
    """Create a strict version with all filters"""
    sentry = SafetySentry(strict_mode=True)
    sentry.add_filter(LengthLimitFilter(max_tokens=2000), FilterType.OUTPUT)
    return sentry


