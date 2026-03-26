#!/usr/bin/env python3
"""
Safety Sentry - Output Guardrail System
PromptOS Module

A modular pipeline that intercepts all outputs through multiple filters.
Pluggable guards for PII, harmful content, secrets, injection, and more.

Features:
- Multi-stage filtering (input → LLM → output)
- Custom filter plugins
- Audit logging with full traceability
- Filter chaining and routing
- Rate limiting
- Dashboard and reporting
- Integration with PromptOS
"""

import json
import re
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Callable
from enum import Enum
from collections import defaultdict
import hashlib


class Action(Enum):
    PASS = "pass"
    BLOCK = "block"
    MODIFY = "modify"
    FLAG = "flag"  # Pass but log for review


class FilterType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    BOTH = "both"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FilterResult:
    """Result of a filter check"""

    passed: bool
    action: Action
    filter_name: str
    severity: str = "low"
    matched_content: list = field(default_factory=list)
    reason: Optional[str] = None
    replacement: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AuditEvent:
    """Complete audit trail entry"""

    event_id: str
    direction: str  # input or output
    session_id: str
    original_content: str
    filter_results: list
    final_action: str
    final_content: str
    blocked: bool
    timestamp: str
    user_id: Optional[str] = None
    model: Optional[str] = None
    tokens_processed: int = 0


from collections.abc import Callable
from abc import ABC, abstractmethod


class Filter:
    """Base filter class"""

    # type: ignore  # ABC issues with type checker

    name: str = "BaseFilter"
    filter_type: FilterType = FilterType.OUTPUT
    severity: str = "medium"
    enabled: bool = True

    def __init__(self, **config):
        self.config = config
        self.stats = {"checked": 0, "blocked": 0, "modified": 0, "flagged": 0}

    def check(self, text: str) -> FilterResult:
        """Check text and return result"""
        raise NotImplementedError

    def __call__(self, text: str) -> FilterResult:
        self.stats["checked"] += 1
        result = self.check(text)

        if result.action == Action.BLOCK:
            self.stats["blocked"] += 1
        elif result.action == Action.MODIFY:
            self.stats["modified"] += 1
        elif result.action == Action.FLAG:
            self.stats["flagged"] += 1

        return result

    def get_stats(self) -> dict:
        return {self.name: self.stats}


