#!/usr/bin/env python3
"""
Reflection Loop - Self-Critique Agent
PromptOS Module

This module watches Frank execute tasks and provides real-time feedback.
Self-improvement through observation, complementing DSPy's training.

Features:
- Multiple reflection modes (immediate, periodic, end-of-session)
- Pattern detection across sessions
- Confidence scoring
- Integration with PromptOS genome/planner
- Strategy effectiveness tracking
- Historical analysis
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from collections import Counter, defaultdict
from enum import Enum


class ReflectionMode(Enum):
    IMMEDIATE = "immediate"  # After every tool call
    PERIODIC = "periodic"  # Every N steps
    END_OF_SESSION = "end"  # At session end
    ON_FAILURE = "on_failure"  # When task fails


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExecutionStep:
    """Represents a single step in agent execution"""

    round: int
    tool: str
    input_summary: str
    output_summary: str
    success: bool = True
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Critique:
    """Reflection critique result"""

    critique: str
    suggestions: list[str]
    efficiency_score: int
    was_successful: bool
    timestamp: str
    confidence: str = "medium"
    mode: str = "periodic"
    patterns_found: list[str] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)


@dataclass
class StrategyEffectiveness:
    """Tracks effectiveness of different strategies"""

    strategy_name: str
    total_attempts: int = 0
    successful: int = 0
    avg_steps: float = 0.0
    avg_time_ms: float = 0.0
    critique_scores: list[int] = field(default_factory=list)


@dataclass
class ReflectionSession:
    """Complete reflection data for a session"""

    session_id: str
    task: str
    initial_prompt: str
    steps: list[ExecutionStep] = field(default_factory=list)
    critiques: list[Critique] = field(default_factory=list)
    final_outcome: str = "unknown"
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    model_used: str = ""
    total_cost: float = 0.0


class ReflectionLoop:
    """
    PromptOS Module: Reflection Loop

    Watches agent execution and provides real-time critique.
    Integrates with PromptOS meta-learning system.

    Features:
    - Multiple reflection modes
    - Pattern detection across sessions
    - Strategy effectiveness tracking
    - Integration with genome/planner
    """

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        enabled: bool = True,
        interval: int = 3,
        mode: ReflectionMode = ReflectionMode.PERIODIC,
        storage_path: str = "logs/reflections",
    ):
        from langchain_ollama import ChatOllama

        self.llm = ChatOllama(model=model)
        self.enabled = enabled
        self.interval = interval
        self.mode = mode
        self.storage_path = storage_path

        # Ensure storage exists
        os.makedirs(storage_path, exist_ok=True)

        # In-memory storage
        self.current_session: Optional[ReflectionSession] = None
        self.sessions: list[ReflectionSession] = []

        # Tracking
        self.total_reflections = 0
        self.strategy_effectiveness: dict[str, StrategyEffectiveness] = defaultdict(
            lambda: StrategyEffectiveness(strategy_name="unknown")
        )

        # Configuration
        self.max_sessions_in_memory = 100
        self.auto_save = True

    # =========================================================================
    # CORE REFLECTION METHODS
    # =========================================================================

    def start_session(
        self, session_id: str, task: str, initial_prompt: str = "", model: str = ""
    ) -> ReflectionSession:
        """Start tracking a new execution session"""
        self.current_session = ReflectionSession(
            session_id=session_id,
            task=task,
            initial_prompt=initial_prompt,
            model_used=model or self.llm.model,
            start_time=datetime.now().isoformat(),
        )
        return self.current_session

    def add_step(
        self,
        tool: str,
        input_summary: str,
        output_summary: str,
        success: bool = True,
        duration_ms: float = 0.0,
    ) -> Optional["Critique"]:
        """Add an execution step to current session, returns Critique if reflection triggered"""
        if not self.current_session:
            return None

        step = ExecutionStep(
            round=len(self.current_session.steps) + 1,
            tool=tool,
            input_summary=input_summary[:200],  # Truncate for storage
            output_summary=output_summary[:200],
            success=success,
            duration_ms=duration_ms,
        )

        self.current_session.steps.append(step)

        # Check if we should reflect
        should_reflect = self._should_reflect()

        if should_reflect:
            critique = self._generate_critique(self.current_session.steps)
            if critique:
                self.current_session.critiques.append(critique)
                self.total_reflections += 1

                if self.auto_save:
                    self._save_session()

                return critique

        return None

    def end_session(self, outcome: str = "completed") -> Optional[Critique]:
        """End the current session and generate final reflection"""
        if not self.current_session:
            return None

        self.current_session.final_outcome = outcome
        self.current_session.end_time = datetime.now().isoformat()

        # Generate end-of-session critique
        if (
            self.mode == ReflectionMode.END_OF_SESSION
            or self.mode == ReflectionMode.PERIODIC
        ):
            critique = self._generate_critique(
                self.current_session.steps, mode=ReflectionMode.END_OF_SESSION.value
            )
            if critique:
                self.current_session.critiques.append(critique)

        # Update strategy effectiveness
        self._update_effectiveness()

        # Save session
        if self.auto_save:
            self._save_session()

        # Archive to sessions list
        self.sessions.append(self.current_session)

        # Trim old sessions if needed
        if len(self.sessions) > self.max_sessions_in_memory:
            self.sessions = self.sessions[-self.max_sessions_in_memory :]

        final_critique = (
            self.current_session.critiques[-1]
            if self.current_session.critiques
            else None
        )
        self.current_session = None

        return final_critique

    def _should_reflect(self) -> bool:
        """Determine if we should generate a critique now"""
        if not self.current_session or not self.enabled:
            return False

        steps = len(self.current_session.steps)

        if self.mode == ReflectionMode.IMMEDIATE:
            return True
        elif self.mode == ReflectionMode.PERIODIC:
            return steps % self.interval == 0
        elif self.mode == ReflectionMode.ON_FAILURE:
            return (
                not self.current_session.steps[-1].success
                if self.current_session.steps
                else False
            )

        return False

    def _generate_critique(
        self, steps: list[ExecutionStep], mode: Optional[str] = None
    ) -> Optional[Critique]:
        """Generate a critique for the current execution trace"""
        if not steps:
            return None

        trace_text = self._format_trace(steps)

        prompt = f"""You are the Reflection Agent. Watch the execution trace and provide critique.

Evaluate:
1. EFFICIENCY - Could this be done in fewer steps?
2. REASONING - Any logical gaps in the approach?
3. SCALABILITY - Will this work on larger inputs?
4. PATTERNS - What repeats across attempts?
5. TOOL SELECTION - Are the right tools being used?

{trace_text}

Respond in JSON:
{{
  "critique": "detailed critique...",
  "suggestions": ["suggestion 1", "suggestion 2"],
  "efficiency_score": 0-10,
  "was_successful": true/false,
  "confidence": "high/medium/low",
  "patterns_found": ["pattern1", "pattern2"],
  "improvement_areas": ["area1", "area2"]
}}
"""
        try:
            response = self.llm.invoke(prompt)
            response_text = str(response.content) if response.content else ""

            # Parse JSON response
            try:
                data = json.loads(response_text)
                critique = Critique(
                    critique=data.get("critique", ""),
                    suggestions=data.get("suggestions", []),
                    efficiency_score=int(data.get("efficiency_score", 5)),
                    was_successful=data.get("was_successful", True),
                    timestamp=datetime.now().isoformat(),
                    confidence=data.get("confidence", "medium"),
                    mode=mode or self.mode.value,
                    patterns_found=data.get("patterns_found", []),
                    improvement_areas=data.get("improvement_areas", []),
                )
            except (json.JSONDecodeError, ValueError):
                # Fallback
                critique = Critique(
                    critique=response_text[:300] if response_text else "No response",
                    suggestions=[],
                    efficiency_score=5,
                    was_successful=True,
                    timestamp=datetime.now().isoformat(),
                    confidence="low",
                    mode=mode or self.mode.value,
                )

            return critique

        except Exception as e:
            print(f"Reflection error: {e}")
            return None

    def _format_trace(self, steps: list[ExecutionStep]) -> str:
        """Format execution steps for the LLM"""
        lines = []
        for step in steps:
            status = "✓" if step.success else "✗"
            lines.append(f"[{step.round}] {status} {step.tool}")
            lines.append(f"    Input: {step.input_summary[:150]}")
            lines.append(f"    Output: {step.output_summary[:150]}")
            if step.duration_ms > 0:
                lines.append(f"    Duration: {step.duration_ms:.0f}ms")
            lines.append("")
        return "\n".join(lines)

    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================

    def detect_patterns(self) -> dict:
        """Analyze all sessions for recurring patterns"""
        if not self.sessions:
            return {"patterns": [], "insights": []}

        # Collect all critiques
        all_critiques = []
        for session in self.sessions:
            all_critiques.extend(session.critiques)

        if not all_critiques:
            return {"patterns": [], "insights": []}

        # Find common suggestions
        all_suggestions = []
        for c in all_critiques:
            all_suggestions.extend(c.suggestions)

        suggestion_counts = defaultdict(int)
        for s in all_suggestions:
            suggestion_counts[s] += 1

        top_suggestions = sorted(suggestion_counts.items(), key=lambda x: -x[1])[:5]

        # Calculate average scores over time
        score_trend = []
        for i, session in enumerate(self.sessions[-20:]):
            if session.critiques:
                avg_score = sum(c.efficiency_score for c in session.critiques) / len(
                    session.critiques
                )
                score_trend.append({"session": i, "avg_score": avg_score})

        # Find failure patterns
        failed_sessions = [s for s in self.sessions if s.final_outcome == "failed"]
        if failed_sessions:
            failed_tools = []
            for session in failed_sessions:
                for step in session.steps:
                    if not step.success:
                        failed_tools.append(step.tool)
            common_failures = Counter(failed_tools).most_common(3)
        else:
            common_failures = []

        return {
            "patterns": [{"suggestion": s, "count": c} for s, c in top_suggestions],
            "score_trend": score_trend,
            "common_failures": common_failures,
            "total_sessions": len(self.sessions),
            "total_reflections": self.total_reflections,
        }

    def get_improvement_recommendations(self) -> list[str]:
        """Generate improvement recommendations based on patterns"""
        patterns = self.detect_patterns()
        recommendations = []

        # Check score trend
        if patterns.get("score_trend"):
            recent_scores = [p["avg_score"] for p in patterns["score_trend"][-5:]]
            if recent_scores and sum(recent_scores) / len(recent_scores) < 5:
                recommendations.append(
                    "Efficiency scores are declining. Consider reviewing strategy selection."
                )

        # Check failure patterns
        if patterns.get("common_failures"):
            for tool, count in patterns["common_failures"]:
                recommendations.append(
                    f"Tool '{tool}' is failing frequently ({count} times). Review usage patterns."
                )

        # Check suggestions
        if patterns.get("patterns"):
            top_pattern = patterns["patterns"][0]
            if top_pattern["count"] > 3:
                recommendations.append(f" recurring issue: {top_pattern['suggestion']}")

        return recommendations

    # =========================================================================
    # STRATEGY EFFECTIVENESS TRACKING
    # =========================================================================

    def track_strategy(self, strategy_name: str):
        """Start tracking a strategy"""
        if strategy_name not in self.strategy_effectiveness:
            self.strategy_effectiveness[strategy_name] = StrategyEffectiveness(
                strategy_name=strategy_name
            )

    def _update_effectiveness(self):
        """Update strategy effectiveness from current session"""
        if not self.current_session:
            return

        strategy = "default"
        self.strategy_effectiveness[strategy].total_attempts += 1

        if self.current_session.final_outcome == "completed":
            self.strategy_effectiveness[strategy].successful += 1

        if self.current_session.steps:
            avg_steps = len(self.current_session.steps)
            self.strategy_effectiveness[strategy].avg_steps = (
                self.strategy_effectiveness[strategy].avg_steps
                * (self.strategy_effectiveness[strategy].total_attempts - 1)
                + avg_steps
            ) / self.strategy_effectiveness[strategy].total_attempts

        for critique in self.current_session.critiques:
            self.strategy_effectiveness[strategy].critique_scores.append(
                critique.efficiency_score
            )

    def get_strategy_report(self) -> dict:
        """Get effectiveness report for all strategies"""
        report = {}
        for name, stats in self.strategy_effectiveness.items():
            avg_score = (
                sum(stats.critique_scores) / len(stats.critique_scores)
                if stats.critique_scores
                else 0
            )
            success_rate = (
                stats.successful / stats.total_attempts
                if stats.total_attempts > 0
                else 0
            )

            report[name] = {
                "total_attempts": stats.total_attempts,
                "successful": stats.successful,
                "success_rate": f"{success_rate:.1%}",
                "avg_steps": f"{stats.avg_steps:.1f}",
                "avg_critique_score": f"{avg_score:.1f}/10",
            }
        return report

    # =========================================================================
    # STORAGE
    # =========================================================================

    def _save_session(self):
        """Save current session to disk"""
        if not self.current_session:
            return

        filepath = os.path.join(
            self.storage_path, f"session_{self.current_session.session_id}.json"
        )

        with open(filepath, "w") as f:
            json.dump(asdict(self.current_session), f, indent=2)

    def load_session(self, session_id: str) -> Optional[ReflectionSession]:
        """Load a session from disk"""
        filepath = os.path.join(self.storage_path, f"session_{session_id}.json")

        if not os.path.exists(filepath):
            return None

        with open(filepath) as f:
            data = json.load(f)
            return ReflectionSession(**data)

    def load_all_sessions(self) -> list[ReflectionSession]:
        """Load all sessions from storage"""
        sessions = []

        for filename in os.listdir(self.storage_path):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[8:-5]
                session = self.load_session(session_id)
                if session:
                    sessions.append(session)

        return sorted(sessions, key=lambda s: s.start_time)

    # =========================================================================
    # STATS & REPORTING
    # =========================================================================

    def get_stats(self) -> dict:
        """Get comprehensive reflection statistics"""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_reflections": self.total_reflections,
                "avg_efficiency": 0,
                "success_rate": 0,
            }

        all_critiques = []
        for session in self.sessions:
            all_critiques.extend(session.critiques)

        if not all_critiques:
            return {
                "total_sessions": len(self.sessions),
                "total_reflections": self.total_reflections,
            }

        total_score = sum(c.efficiency_score for c in all_critiques)
        success_count = sum(1 for c in all_critiques if c.was_successful)

        completed = sum(1 for s in self.sessions if s.final_outcome == "completed")

        return {
            "total_sessions": len(self.sessions),
            "total_reflections": self.total_reflections,
            "avg_efficiency_score": total_score / len(all_critiques),
            "success_rate": success_count / len(all_critiques),
            "session_completion_rate": completed / len(self.sessions),
            "patterns_detected": len(self.detect_patterns().get("patterns", [])),
        }

    def inject_suggestion(self) -> Optional[str]:
        """Get the most impactful suggestion to inject"""
        if not self.current_session or not self.current_session.critiques:
            return None

        # Get most recent critique with highest impact
        for critique in reversed(self.current_session.critiques):
            if critique.suggestions and critique.confidence in ["high", "medium"]:
                return f"Reflection: {critique.suggestions[0]}"

        return None

    # =========================================================================
    # INTEGRATION WITH PROMPTOS
    # =========================================================================

    def export_for_genome(self) -> dict:
        """Export reflection data for PromptOS genome"""
        return {
            "patterns": self.detect_patterns(),
            "strategy_effectiveness": self.get_strategy_report(),
            "recommendations": self.get_improvement_recommendations(),
            "stats": self.get_stats(),
        }


def create_reflection_loop(
    model: str = "qwen2.5:7b",
    enabled: bool = True,
    mode: ReflectionMode = ReflectionMode.PERIODIC,
) -> ReflectionLoop:
    """Factory function for PromptOS integration"""
    return ReflectionLoop(model=model, enabled=enabled, mode=mode)


# Demo
if __name__ == "__main__":
    reflection = ReflectionLoop(mode=ReflectionMode.PERIODIC)

    # Start a session
    session = reflection.start_session(
        session_id="demo_001",
        task="Fix authentication bug",
        initial_prompt="Fix the login issue",
    )

    # Simulate steps
    reflection.add_step("bash", "find . -name 'auth*.py'", "Found 3 files", True, 50.0)
    reflection.add_step("read", "src/auth.py", "Found bug at line 42", True, 120.0)
    reflection.add_step("edit", "line 42", "Fixed condition", True, 30.0)
    reflection.add_step("bash", "python -m pytest", "All tests pass", True, 5000.0)

    # End session
    critique = reflection.end_session("completed")

    if critique:
        print("=== CRITIQUE ===")
        print(f"Score: {critique.efficiency_score}/10")
        print(f"Confidence: {critique.confidence}")
        print(f"Critique: {critique.critique}")
        print(f"Suggestions: {critique.suggestions}")

    print(f"\n=== STATS ===")
    print(reflection.get_stats())

    print(f"\n=== PATTERNS ===")
    print(reflection.detect_patterns())

    print(f"\n=== RECOMMENDATIONS ===")
    for rec in reflection.get_improvement_recommendations():
        print(f"  - {rec}")
