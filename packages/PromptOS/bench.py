#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Bench Integration for PromptOS

Handles scoring against answer keys, ticket tracking, and failure mode detection.
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path


class BenchIntegration:
    """
    Integrates PromptOS with Bench scoring system.

    Features:
    - Answer key comparison
    - Ticket success/failure tracking
    - Failure mode detection
    - Score normalization

    Usage:
        bench = BenchIntegration(answer_key_path="bench/answer_keys.json")

        # Score a response
        score = bench.score_response(response, ticket_id="ticket_174")

        # Record ticket result
        bench.record_ticket(
            ticket_id="ticket_174",
            success=True,
            score=0.95,
            strategy_stack=["scratchpad", "verify"]
        )
    """

    def __init__(
        self,
        answer_key_path: Optional[str] = None,
        scoring_callback: Optional[Callable] = None,
    ):
        """
        Initialize Bench integration.

        Args:
            answer_key_path: Path to answer keys JSON file
            scoring_callback: Custom scoring function (overrides answer key)
        """
        self.answer_key_path = answer_key_path
        self.scoring_callback = scoring_callback
        self.answer_keys: Dict[str, Any] = {}
        self.ticket_history: List[Dict] = []
        self.db_only = str(os.getenv("PROMPTOS_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # Load answer keys if provided
        if answer_key_path:
            self.load_answer_keys(answer_key_path)

        # Failure mode categories
        self.failure_modes = {
            "hallucination": ["incorrect fact", "made up", "doesn't exist"],
            "incomplete": ["missing", "incomplete", "partial"],
            "wrong_format": ["format", "structure", "expected"],
            "logic_error": ["logic", "reasoning", "incorrect conclusion"],
            "syntax_error": ["syntax", "compilation", "parse error"],
            "timeout": ["timeout", "too long", "exceeded"],
        }

    def load_answer_keys(self, path: str):
        """
        Load answer keys from JSON file.

        Expected format:
        {
            "ticket_174": {
                "expected_output": "...",
                "test_cases": [...],
                "scoring rubric": {...}
            }
        }
        """
        try:
            with open(path, "r") as f:
                self.answer_keys = json.load(f)
            print(f"[Bench] Loaded {len(self.answer_keys)} answer keys")
        except Exception as e:
            print(f"[Bench] Failed to load answer keys: {e}")

    def score_response(
        self,
        response: str,
        ticket_id: Optional[str] = None,
        expected_output: Optional[str] = None,
        test_cases: Optional[List[Dict]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Score a response against answer key or test cases.

        Args:
            response: Model's response
            ticket_id: Ticket ID to lookup answer key
            expected_output: Expected output (if not using ticket_id)
            test_cases: Test cases to run (for coding tasks)

        Returns:
            (score, details) tuple
            - score: 0.0 to 1.0
            - details: Scoring breakdown
        """
        # Use custom scoring callback if provided
        if self.scoring_callback:
            score = self.scoring_callback(response, ticket_id, expected_output)
            return score, {"method": "custom"}

        # Get answer key for ticket
        if ticket_id and ticket_id in self.answer_keys:
            answer_key = self.answer_keys[ticket_id]
            expected_output = expected_output or answer_key.get("expected_output")
            test_cases = test_cases or answer_key.get("test_cases", [])

        # Score based on what's available
        if test_cases:
            return self._score_with_tests(response, test_cases)
        elif expected_output:
            return self._score_exact_match(response, expected_output)
        else:
            # No answer key - return neutral score
            return 0.5, {"method": "no_answer_key"}

    def _score_exact_match(
        self, response: str, expected: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Score based on exact/partial match with expected output."""
        from difflib import SequenceMatcher

        # Normalize
        response_norm = response.lower().strip()
        expected_norm = expected.lower().strip()

        # Exact match
        if response_norm == expected_norm:
            return 1.0, {"method": "exact_match", "match": "exact"}

        # Partial match
        similarity = SequenceMatcher(None, response_norm, expected_norm).ratio()

        details = {
            "method": "similarity",
            "similarity": similarity,
            "match": "partial" if similarity > 0.7 else "poor",
        }

        return similarity, details

    def _score_with_tests(
        self, response: str, test_cases: List[Dict]
    ) -> Tuple[float, Dict[str, Any]]:
        """Score by running test cases (for coding tasks)."""
        passed = 0
        failed = 0
        errors = []

        for i, test in enumerate(test_cases):
            # Extract code from response if needed
            code = self._extract_code(response)

            # Run test (simplified - real implementation would execute safely)
            try:
                # This is where you'd integrate with actual test runner
                # For now, simple string matching
                if test.get("expected") in code:
                    passed += 1
                else:
                    failed += 1
                    errors.append(f"Test {i + 1} failed")
            except Exception as e:
                failed += 1
                errors.append(str(e))

        total = passed + failed
        score = passed / total if total > 0 else 0.0

        details = {
            "method": "test_cases",
            "passed": passed,
            "failed": failed,
            "total": total,
            "errors": errors[:5],  # Limit error details
        }

        return score, details

    def _extract_code(self, response: str) -> str:
        """Extract code blocks from response."""
        import re

        # Look for code blocks
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)

        if code_blocks:
            return "\n".join(code_blocks)

        return response

    def detect_failure_mode(self, response: str, score: float) -> Optional[str]:
        """
        Detect the failure mode for a low-scoring response.

        Args:
            response: Model's response
            score: Score (should be low)

        Returns:
            Failure mode category or None
        """
        if score >= 0.7:
            return None  # Not a failure

        response_lower = response.lower()

        for mode, keywords in self.failure_modes.items():
            if any(kw in response_lower for kw in keywords):
                return mode

        return "unknown"

    def record_ticket(
        self,
        ticket_id: str,
        success: bool,
        score: float,
        strategy_stack: List[str],
        model: str,
        task_type: str,
        failure_mode: Optional[str] = None,
        tokens_used: int = 0,
        status: Optional[str] = None,
    ):
        """
        Record ticket result for strategy evolution.

        Args:
            ticket_id: Ticket identifier
            success: Whether ticket was successful
            score: Bench score (-1 indicates connection failure - skip recording)
            strategy_stack: Strategy modules used
            model: Model used
            task_type: Task type
            failure_mode: Detected failure mode
            tokens_used: Token count
            status: Explicit status - "success", "failure", or "unavailable" (connection issues)
        """
        record = {
            "ticket_id": ticket_id,
            "success": success,
            "score": score,
            "status": status,
            "strategy_stack": strategy_stack,
            "model": model,
            "task_type": task_type,
            "failure_mode": failure_mode,
            "tokens_used": tokens_used,
            "timestamp": datetime.now().isoformat(),
        }

        self.ticket_history.append(record)

        # Auto-save ticket history
        self.save_ticket_history()

    def save_ticket_history(self, path: Optional[str] = None):
        """Save ticket history to JSON file."""
        if self.db_only:
            return
        if path is None:
            path = "PromptOS/ticket_history.json"

        try:
            with open(path, "w") as f:
                json.dump(self.ticket_history, f, indent=2, default=str)
        except Exception as e:
            print(f"[Bench] Failed to save ticket history: {e}")

    def load_ticket_history(self, path: Optional[str] = None) -> int:
        """Load ticket history from JSON file."""
        if self.db_only:
            return 0
        if path is None:
            path = "PromptOS/ticket_history.json"

        try:
            with open(path, "r") as f:
                self.ticket_history = json.load(f)
            print(f"[Bench] Loaded {len(self.ticket_history)} ticket records")
            return len(self.ticket_history)
        except Exception as e:
            print(f"[Bench] Failed to load ticket history: {e}")
            return 0

    def get_strategy_performance(
        self,
        model: str,
        task_type: str,
    ) -> Dict[str, float]:
        """
        Get average performance per strategy for a model/task.

        Args:
            model: Model name
            task_type: Task type

        Returns:
            Dict mapping strategy_stack → average score
        """
        # Filter relevant tickets
        relevant = [
            t
            for t in self.ticket_history
            if t.get("model") == model and t.get("task_type") == task_type
        ]

        # Group by strategy stack
        strategy_scores: Dict[str, List[float]] = {}

        for ticket in relevant:
            stack = tuple(sorted(ticket.get("strategy_stack", [])))
            stack_key = ",".join(stack)

            if stack_key not in strategy_scores:
                strategy_scores[stack_key] = []
            strategy_scores[stack_key].append(ticket.get("score", 0))

        # Calculate averages
        averages = {}
        for stack, scores in strategy_scores.items():
            averages[stack] = sum(scores) / len(scores) if scores else 0.0

        return averages
