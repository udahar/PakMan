"""
Prompt Analytics - Usage Tracking and Analysis
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class UsageEvent:
    """A single usage event."""

    event_type: str  # blueprint_used, skill_used, prompt_used
    name: str
    success: bool
    user_rating: float = 0.5
    latency_ms: int = 0
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class PromptAnalytics:
    """
    Track and analyze prompt/blueprint/skill usage.

    Usage:
        analytics = PromptAnalytics()
        analytics.track("blueprint_used", "streetpunk", success=True, user_rating=0.9)
        stats = analytics.get_stats(period="week")
    """

    def __init__(self, data_dir: str = "prompt_analytics_data"):
        self.data_dir = data_dir
        self.events: List[UsageEvent] = []
        self._load_events()

    def track(
        self,
        event_type: str,
        name: str,
        success: bool = True,
        user_rating: float = 0.5,
        latency_ms: int = 0,
        tokens_used: int = 0,
        metadata: Dict = None,
    ):
        """Track a usage event."""
        event = UsageEvent(
            event_type=event_type,
            name=name,
            success=success,
            user_rating=user_rating,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata=metadata or {},
        )
        self.events.append(event)
        self._save_event(event)

    def get_stats(self, period: str = "week") -> Dict[str, Any]:
        """Get usage statistics."""
        cutoff = self._get_cutoff(period)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]

        blueprint_usage = defaultdict(
            lambda: {"count": 0, "success": 0, "total_rating": 0}
        )
        skill_usage = defaultdict(lambda: {"count": 0, "success": 0, "total_rating": 0})

        for event in recent_events:
            if event.event_type == "blueprint_used":
                blueprint_usage[event.name]["count"] += 1
                if event.success:
                    blueprint_usage[event.name]["success"] += 1
                blueprint_usage[event.name]["total_rating"] += event.user_rating
            elif event.event_type == "skill_used":
                skill_usage[event.name]["count"] += 1
                if event.success:
                    skill_usage[event.name]["success"] += 1
                skill_usage[event.name]["total_rating"] += event.user_rating

        top_blueprint = max(
            blueprint_usage.items(),
            key=lambda x: x[1]["count"],
            default=(None, {"count": 0}),
        )
        top_skill = max(
            skill_usage.items(),
            key=lambda x: x[1]["count"],
            default=(None, {"count": 0}),
        )

        best_skill = max(
            skill_usage.items(),
            key=lambda x: x[1]["total_rating"] / max(x[1]["count"], 1),
            default=(None, {"count": 0}),
        )

        return {
            "period": period,
            "total_events": len(recent_events),
            "top_blueprint": top_blueprint[0] if top_blueprint[0] else "N/A",
            "top_blueprint_count": top_blueprint[1]["count"],
            "top_skill": top_skill[0] if top_skill[0] else "N/A",
            "top_skill_count": top_skill[1]["count"],
            "best_skill": best_skill[0] if best_skill[0] else "N/A",
            "best_skill_rating": best_skill[1]["total_rating"]
            / max(best_skill[1]["count"], 1),
            "blueprint_stats": dict(blueprint_usage),
            "skill_stats": dict(skill_usage),
        }

    def get_trends(self, metric: str = "usage", period: str = "week") -> List[Dict]:
        """Get trend data over time."""
        cutoff = self._get_cutoff(period)
        recent = [e for e in self.events if e.timestamp >= cutoff]

        trends = defaultdict(int)
        for event in recent:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            trends[date_key] += 1

        return [{"date": k, "count": v} for k, v in sorted(trends.items())]

    def get_success_rate(self, name: str = None, event_type: str = None) -> float:
        """Get success rate for blueprint or skill."""
        filtered = self.events

        if name:
            filtered = [e for e in filtered if e.name == name]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if not filtered:
            return 0.0

        successes = sum(1 for e in filtered if e.success)
        return successes / len(filtered)

    def _get_cutoff(self, period: str) -> datetime:
        """Get cutoff datetime for period."""
        now = datetime.now()

        if period == "day":
            return now - timedelta(days=1)
        elif period == "week":
            return now - timedelta(weeks=1)
        elif period == "month":
            return now - timedelta(days=30)
        elif period == "year":
            return now - timedelta(days=365)

        return now - timedelta(weeks=1)

    def _load_events(self):
        """Load events from disk."""
        import os

        os.makedirs(self.data_dir, exist_ok=True)

        events_file = os.path.join(self.data_dir, "events.json")
        if os.path.exists(events_file):
            try:
                with open(events_file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        self.events.append(
                            UsageEvent(
                                event_type=item["event_type"],
                                name=item["name"],
                                success=item["success"],
                                user_rating=item.get("user_rating", 0.5),
                                latency_ms=item.get("latency_ms", 0),
                                tokens_used=item.get("tokens_used", 0),
                                timestamp=datetime.fromisoformat(item["timestamp"]),
                                metadata=item.get("metadata", {}),
                            )
                        )
            except:
                pass

    def _save_event(self, event: UsageEvent):
        """Save event to disk."""
        import os

        os.makedirs(self.data_dir, exist_ok=True)

        events_file = os.path.join(self.data_dir, "events.json")

        events_data = []
        if os.path.exists(events_file):
            try:
                with open(events_file, "r") as f:
                    events_data = json.load(f)
            except:
                events_data = []

        events_data.append(
            {
                "event_type": event.event_type,
                "name": event.name,
                "success": event.success,
                "user_rating": event.user_rating,
                "latency_ms": event.latency_ms,
                "tokens_used": event.tokens_used,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata,
            }
        )

        with open(events_file, "w") as f:
            json.dump(events_data, f)


def create_prompt_analytics(data_dir: str = "prompt_analytics_data") -> PromptAnalytics:
    """Factory function."""
    return PromptAnalytics(data_dir)
