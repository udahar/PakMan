#!/usr/bin/env python3
"""
Tool Use Mining - Discover Capabilities from Logs
PromptOS Module

Analyzes execution logs to discover new capabilities from tool combinations.
Frank teaches himself new skills by watching what works.

Features:
- Cross-session pattern analysis
- Model-specific patterns
- Time-based pattern analysis
- Skill generation with proper metadata
- Integration with skills registry
- Scheduled mining support
- Pattern confidence scoring
- Export/import capabilities
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum
import hashlib


class SkillSource(Enum):
    MANUAL = "manual"
    AUTO_DISCOVERED = "auto_discovered"
    TOOL_USE_MINER = "tool_use_miner"
    USER_CREATED = "user_created"


class PatternConfidence(Enum):
    HIGH = "high"  # >80% success, >5 occurrences
    MEDIUM = "medium"  # >60% success, >3 occurrences
    LOW = "low"  # Meets minimum thresholds


@dataclass
class LogEntry:
    """Single execution log entry"""

    session_id: str
    timestamp: str
    prompt: str
    tool_sequence: list[str]
    num_steps: int
    success: bool
    model_used: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class ToolPattern:
    """A discovered tool usage pattern"""

    pattern_id: str
    tool_sequence: list[str]
    occurrences: int = 0
    success_count: int = 0
    success_rate: float = 0.0
    avg_steps: float = 0.0
    avg_duration_ms: float = 0.0
    models: list[str] = field(default_factory=list)
    example_prompts: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    confidence: str = "low"


@dataclass
class DiscoveredSkill:
    """A skill generated from discovered patterns"""

    skill_id: str
    name: str
    description: str
    trigger_patterns: list[str]
    tool_sequence: list[str]
    success_rate: float
    discovery_count: int
    confidence: str
    created_at: str
    source: str = "tool_use_miner"
    metadata: dict = field(default_factory=dict)


class ToolUseMiner:
    """
    PromptOS Module: Tool Use Mining

    Discovers new skills from execution patterns.
    Integrates with PromptOS skills system.

    Features:
    - Cross-session pattern analysis
    - Model-specific pattern tracking
    - Time-based analysis
    - Confidence scoring
    - Scheduled mining
    """

    def __init__(
        self,
        log_file: str = "logs/tool_use.jsonl",
        min_support: int = 3,
        min_success_rate: float = 0.6,
        storage_path: str = "logs/miner",
    ):
        self.log_file = log_file
        self.min_support = min_support
        self.min_success_rate = min_success_rate
        self.storage_path = storage_path

        # Ensure storage exists
        os.makedirs(storage_path, exist_ok=True)

        # In-memory storage
        self.patterns: dict[str, ToolPattern] = {}
        self.discovered_skills: list[DiscoveredSkill] = []

        # Tracking
        self.total_patterns_found = 0
        self.total_sessions_analyzed = 0

        # Load existing patterns
        self._load_patterns()

    # =========================================================================
    # LOGGING
    # =========================================================================

    def log_session(
        self,
        session_id: str,
        prompt: str,
        tool_calls: list[dict],
        success: bool,
        model_used: str = "",
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ):
        """Log a new session for future mining"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        tool_sequence = []
        for tc in tool_calls:
            if isinstance(tc, dict):
                tool_sequence.append({"tool": tc.get("tool", "unknown")})
            else:
                tool_sequence.append({"tool": str(tc)})

        entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt[:300] if prompt else "",
            "tool_sequence": tool_sequence,
            "num_steps": len(tool_calls),
            "success": success,
            "model_used": model_used,
            "duration_ms": duration_ms,
            "error": error,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        self.total_sessions_analyzed += 1

    def load_logs(self) -> list[LogEntry]:
        """Load all logs from file"""
        logs = []

        try:
            with open(self.log_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        logs.append(
                            LogEntry(
                                session_id=data.get("session_id", ""),
                                timestamp=data.get("timestamp", ""),
                                prompt=data.get("prompt", ""),
                                tool_sequence=[
                                    t.get("tool", "unknown")
                                    for t in data.get("tool_sequence", [])
                                ],
                                num_steps=data.get("num_steps", 0),
                                success=data.get("success", False),
                                model_used=data.get("model_used", ""),
                                duration_ms=data.get("duration_ms", 0.0),
                                error=data.get("error"),
                            )
                        )
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return logs

    # =========================================================================
    # PATTERN MINING
    # =========================================================================

    def mine_patterns(self) -> dict[str, ToolPattern]:
        """Find recurring tool sequences and build patterns"""
        logs = self.load_logs()

        if not logs:
            return {}

        # Group by tool sequence
        sequence_data: dict = defaultdict(
            lambda: {
                "occurrences": 0,
                "successes": 0,
                "steps": [],
                "durations": [],
                "models": set(),
                "prompts": [],
                "first_seen": None,
                "last_seen": None,
            }
        )

        for log in logs:
            seq_key = tuple(log.tool_sequence)
            data = sequence_data[seq_key]

            data["occurrences"] += 1
            if log.success:
                data["successes"] += 1
            data["steps"].append(log.num_steps)
            data["durations"].append(log.duration_ms)
            if log.model_used:
                data["models"].add(log.model_used)
            if log.prompt:
                data["prompts"].append(log.prompt[:200])

            if not data["first_seen"] or log.timestamp < data["first_seen"]:
                data["first_seen"] = log.timestamp
            if not data["last_seen"] or log.timestamp > data["last_seen"]:
                data["last_seen"] = log.timestamp

        # Build patterns
        patterns = {}

        for seq_key, data in sequence_data.items():
            if data["occurrences"] < self.min_support:
                continue

            success_rate = data["successes"] / data["occurrences"]
            if success_rate < self.min_success_rate:
                continue

            pattern_id = self._generate_pattern_id(seq_key)

            # Determine confidence
            if success_rate > 0.8 and data["occurrences"] > 5:
                confidence = PatternConfidence.HIGH.value
            elif success_rate > 0.6 and data["occurrences"] > 3:
                confidence = PatternConfidence.MEDIUM.value
            else:
                confidence = PatternConfidence.LOW.value

            pattern = ToolPattern(
                pattern_id=pattern_id,
                tool_sequence=list(seq_key),
                occurrences=data["occurrences"],
                success_count=data["successes"],
                success_rate=success_rate,
                avg_steps=sum(data["steps"]) / len(data["steps"]),
                avg_duration_ms=sum(data["durations"]) / len(data["durations"])
                if data["durations"]
                else 0,
                models=list(data["models"]),
                example_prompts=data["prompts"][:5],
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                confidence=confidence,
            )

            patterns[pattern_id] = pattern

        self.patterns = patterns
        self.total_patterns_found = len(patterns)

        return patterns

    def _generate_pattern_id(self, sequence: tuple) -> str:
        """Generate a unique ID for a pattern"""
        seq_str = "_".join(sequence)
        return f"pattern_{hashlib.md5(seq_str.encode()).hexdigest()[:12]}"

    # =========================================================================
    # PATTERN ANALYSIS
    # =========================================================================

    def analyze_pattern(self, pattern_id: str) -> Optional[ToolPattern]:
        """Get detailed analysis of a specific pattern"""
        if pattern_id not in self.patterns:
            self.mine_patterns()
        return self.patterns.get(pattern_id)

    def get_patterns_by_model(self, model: str) -> list[ToolPattern]:
        """Get all patterns that work with a specific model"""
        return [p for p in self.patterns.values() if model in p.models]

    def get_patterns_by_confidence(self, confidence: str) -> list[ToolPattern]:
        """Get patterns by confidence level"""
        return [p for p in self.patterns.values() if p.confidence == confidence]

    def get_time_based_analysis(self, days: int = 7) -> dict:
        """Analyze patterns over time"""
        logs = self.load_logs()

        cutoff = datetime.now() - timedelta(days=days)
        recent_logs = [
            log for log in logs if datetime.fromisoformat(log.timestamp) > cutoff
        ]

        if not recent_logs:
            return {"period_days": days, "sessions": 0, "trends": {}}

        # Group by day
        daily_stats = defaultdict(lambda: {"total": 0, "success": 0})

        for log in recent_logs:
            day = log.timestamp[:10]  # YYYY-MM-DD
            daily_stats[day]["total"] += 1
            if log.success:
                daily_stats[day]["success"] += 1

        trends = {
            day: {
                "sessions": stats["total"],
                "success_rate": stats["success"] / stats["total"]
                if stats["total"] > 0
                else 0,
            }
            for day, stats in sorted(daily_stats.items())
        }

        return {
            "period_days": days,
            "sessions": len(recent_logs),
            "trends": trends,
            "avg_daily_sessions": len(recent_logs) / days if days > 0 else 0,
        }

    def get_pattern_evolution(self) -> dict:
        """See how patterns change over time"""
        logs = self.load_logs()

        if not logs:
            return {"new_patterns": [], "declining_patterns": [], "stable_patterns": []}

        # Sort by timestamp
        logs.sort(key=lambda x: x.timestamp)

        midpoint = len(logs) // 2
        first_half = logs[:midpoint]
        second_half = logs[midpoint:]

        # Get patterns for each half
        first_patterns = Counter(
            tuple(log.tool_sequence) for log in first_half if len(log.tool_sequence) > 0
        )
        second_patterns = Counter(
            tuple(log.tool_sequence)
            for log in second_half
            if len(log.tool_sequence) > 0
        )

        all_patterns = set(first_patterns.keys()) | set(second_patterns.keys())

        new_patterns = []
        declining_patterns = []
        stable_patterns = []

        for pattern in all_patterns:
            first_count = first_patterns.get(pattern, 0)
            second_count = second_patterns.get(pattern, 0)

            if first_count == 0 and second_count > 2:
                new_patterns.append(
                    {"pattern": list(pattern), "occurrences": second_count}
                )
            elif second_count < first_count * 0.5 and first_count > 3:
                declining_patterns.append(
                    {"pattern": list(pattern), "was": first_count, "now": second_count}
                )
            elif abs(first_count - second_count) < 2:
                stable_patterns.append(
                    {"pattern": list(pattern), "avg": (first_count + second_count) // 2}
                )

        return {
            "new_patterns": new_patterns[:5],
            "declining_patterns": declining_patterns[:5],
            "stable_patterns": stable_patterns[:5],
        }

    # =========================================================================
    # SKILL GENERATION
    # =========================================================================

    def create_skill(self, pattern: ToolPattern) -> DiscoveredSkill:
        """Convert a pattern into a skill for PromptOS"""
        skill_id = f"auto_mined_{len(self.discovered_skills) + 1}"

        skill = DiscoveredSkill(
            skill_id=skill_id,
            name=f"Auto: {' → '.join(pattern.tool_sequence[:3])}",
            description=f"Discovered pattern with {pattern.success_rate:.0%} success rate "
            f"across {pattern.occurrences} executions",
            trigger_patterns=pattern.example_prompts[:5],
            tool_sequence=pattern.tool_sequence,
            success_rate=pattern.success_rate,
            discovery_count=pattern.occurrences,
            confidence=pattern.confidence,
            created_at=datetime.now().isoformat(),
            source=SkillSource.TOOL_USE_MINER.value,
            metadata={
                "pattern_id": pattern.pattern_id,
                "avg_steps": pattern.avg_steps,
                "avg_duration_ms": pattern.avg_duration_ms,
                "models": pattern.models,
            },
        )

        self.discovered_skills.append(skill)

        # Save skill
        self._save_skill(skill)

        return skill

    def run_discovery(self, min_confidence: str = "low") -> list[DiscoveredSkill]:
        """Find all significant patterns and generate skills"""
        # Mine patterns first
        patterns = self.mine_patterns()

        # Filter by confidence
        confidence_order = ["low", "medium", "high"]
        min_idx = confidence_order.index(min_confidence)

        discovered = []

        for pattern_id, pattern in sorted(
            patterns.items(), key=lambda x: (-x[1].success_rate, -x[1].occurrences)
        ):
            if confidence_order.index(pattern.confidence) >= min_idx:
                # Check if we already have this skill
                existing = any(
                    s.metadata.get("pattern_id") == pattern_id
                    for s in self.discovered_skills
                )

                if not existing:
                    skill = self.create_skill(pattern)
                    discovered.append(skill)

        return discovered

    def get_skill_recommendations(self, task_description: str) -> list[DiscoveredSkill]:
        """Get skill recommendations based on task"""
        task_lower = task_description.lower()
        recommendations = []

        for skill in self.discovered_skills:
            # Check trigger patterns
            for trigger in skill.trigger_patterns:
                if any(word in trigger.lower() for word in task_lower.split()[:3]):
                    recommendations.append(skill)
                    break

        # Sort by success rate
        recommendations.sort(key=lambda s: s.success_rate, reverse=True)

        return recommendations[:5]

    # =========================================================================
    # STORAGE
    # =========================================================================

    def _save_skill(self, skill: DiscoveredSkill):
        """Save skill to disk"""
        filepath = os.path.join(self.storage_path, f"skill_{skill.skill_id}.json")

        with open(filepath, "w") as f:
            json.dump(asdict(skill), f, indent=2)

    def _load_patterns(self):
        """Load patterns from disk"""
        skills_dir = self.storage_path

        if not os.path.exists(skills_dir):
            return

        for filename in os.listdir(skills_dir):
            if filename.startswith("skill_") and filename.endswith(".json"):
                filepath = os.path.join(skills_dir, filename)
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                        self.discovered_skills.append(DiscoveredSkill(**data))
                except (json.JSONDecodeError, TypeError):
                    continue

    def export_patterns(self, filepath: str = "logs/miner/patterns_export.json"):
        """Export all patterns to file"""
        patterns_data = {
            pattern_id: asdict(pattern) for pattern_id, pattern in self.patterns.items()
        }

        with open(filepath, "w") as f:
            json.dump(patterns_data, f, indent=2)

        return filepath

    def import_patterns(self, filepath: str):
        """Import patterns from file"""
        with open(filepath) as f:
            data = json.load(f)

        for pattern_id, pattern_data in data.items():
            self.patterns[pattern_id] = ToolPattern(**pattern_data)

        self.total_patterns_found = len(self.patterns)

    # =========================================================================
    # STATS
    # =========================================================================

    def get_stats(self) -> dict:
        """Get comprehensive mining statistics"""
        self.mine_patterns()  # Refresh

        confidence_counts = Counter(p.confidence for p in self.patterns.values())

        return {
            "total_patterns": self.total_patterns_found,
            "total_skills_discovered": len(self.discovered_skills),
            "total_sessions_analyzed": self.total_sessions_analyzed,
            "min_support": self.min_support,
            "min_success_rate": self.min_success_rate,
            "patterns_by_confidence": dict(confidence_counts),
            "high_value_patterns": len(
                [p for p in self.patterns.values() if p.success_rate > 0.8]
            ),
            "recent_discoveries": [
                {"name": s.name, "success_rate": s.success_rate}
                for s in self.discovered_skills[-5:]
            ],
        }

    def get_pattern_leaderboard(self, limit: int = 10) -> list[dict]:
        """Get top patterns by various metrics"""
        patterns_list = list(self.patterns.values())

        # Sort by composite score
        scored = []
        for p in patterns_list:
            score = p.success_rate * 0.6 + min(p.occurrences / 10, 1) * 0.4
            scored.append(
                {
                    "pattern_id": p.pattern_id,
                    "tool_sequence": " → ".join(p.tool_sequence),
                    "success_rate": f"{p.success_rate:.0%}",
                    "occurrences": p.occurrences,
                    "confidence": p.confidence,
                    "score": round(score, 2),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]


class SkillRegistrar:
    """Register discovered skills with PromptOS skills system"""

    def __init__(self, miner: ToolUseMiner = None):
        self.miner = miner or ToolUseMiner()
        self.registered = []

    def register(self, skill: DiscoveredSkill) -> bool:
        """Register skill with PromptOS"""
        print(f"[SkillRegistrar] Registering: {skill.name}")
        print(f"  Tool sequence: {skill.tool_sequence}")
        print(f"  Success rate: {skill.success_rate:.0%}")
        print(f"  Confidence: {skill.confidence}")

        self.registered.append(asdict(skill))
        return True

    def auto_discover_and_register(self, min_confidence: str = "medium") -> dict:
        """Run discovery and register all new skills"""
        skills = self.miner.run_discovery(min_confidence=min_confidence)

        results = {"discovered": 0, "registered": 0, "skipped": 0}

        for skill in skills:
            results["discovered"] += 1
            if self.register(skill):
                results["registered"] += 1
            else:
                results["skipped"] += 1

        return results


def create_tool_use_miner(
    log_file: str = "logs/tool_use.jsonl",
    min_support: int = 3,
) -> ToolUseMiner:
    """Factory function for PromptOS integration"""
    return ToolUseMiner(
        log_file=log_file,
        min_support=min_support,
    )


# Demo
if __name__ == "__main__":
    miner = ToolUseMiner()

    # Log some sample sessions
    miner.log_session(
        session_id="demo_001",
        prompt="Fix the authentication bug",
        tool_calls=[
            {"tool": "bash", "input": "find . -name '*.py'", "success": True},
            {"tool": "read", "input": "auth.py", "success": True},
            {"tool": "edit", "input": "line 42", "success": True},
            {"tool": "bash", "input": "pytest", "success": True},
        ],
        success=True,
        model_used="qwen2.5:7b",
        duration_ms=5000.0,
    )

    miner.log_session(
        session_id="demo_002",
        prompt="Fix login issue",
        tool_calls=[
            {"tool": "bash", "input": "ls", "success": True},
            {"tool": "read", "input": "login.py", "success": True},
            {"tool": "edit", "input": "line 10", "success": True},
            {"tool": "bash", "input": "pytest", "success": True},
        ],
        success=True,
        model_used="qwen2.5:7b",
        duration_ms=4500.0,
    )

    # Run discovery
    patterns = miner.mine_patterns()
    print(f"Found {len(patterns)} patterns")

    skills = miner.run_discovery()
    print(f"\nDiscovered {len(skills)} skills:")
    for skill in skills:
        print(f"  - {skill.name}")
        print(f"    Success: {skill.success_rate:.0%}, Confidence: {skill.confidence}")

    print(f"\n=== STATS ===")
    print(miner.get_stats())

    print(f"\n=== LEADERBOARD ===")
    for p in miner.get_pattern_leaderboard():
        print(f"  {p['tool_sequence'][:50]} - {p['score']}")

    print(f"\n=== TIME ANALYSIS ===")
    print(miner.get_time_based_analysis(days=7))
