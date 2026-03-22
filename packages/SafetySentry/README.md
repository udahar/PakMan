# Safety Sentry - Output Guardrail System

## The Concept

A modular pipeline that intercepts all outputs through multiple filters before returning to the user. Pluggable guards for:

- 🔒 **PII Detection** - Names, emails, phone numbers, SSNs
- ⚠️ **Harmful Content** - Violence, hate speech, self-harm
- 🐛 **Code Injection** - Malicious scripts, SQL injection
- 🔑 **Secrets Exposure** - API keys, passwords, tokens
- 📝 **Output Validation** - Format correctness, length limits

```
┌─────────────────────────────────────────────────────────────┐
│                    Safety Sentry                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Prompt                                                 │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Input Guard (Pre-LLM)                   │   │
│  │  - Check for injection attempts                    │   │
│  │  - Validate input format                            │   │
│  │  - Rate limiting                                    │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                          │                                    │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LLM Processing                         │   │
│  │  (Frank does his thing)                            │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                          │                                    │
│       ┌──────────────────┴──────────────────┐               │
│       ▼                                      ▼               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │  Filter Chain    │              │  Audit Log       │     │
│  │                  │              │                  │     │
│  │ [PII Detector]  │              │ - What blocked  │     │
│  │ [Harmful Check] │              │ - When           │     │
│  │ [Secrets Scan]  │              │ - Why            │     │
│  │ [Format Valid.] │              │ - Who            │     │
│  └────────┬─────────┘              └──────────────────┘     │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Response Handler                        │   │
│  │                                                      │   │
│  │  If clean: Pass through                             │   │
│  │  If blocked: Return safe response + log            │   │
│  │  If modified: Return modified + explain            │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                    │
│                          ▼                                    │
│                    User Output                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Work / Integration Guide

### Step 1: Create Filter Interface

```python
# filters/base.py
from abc import ABC, abstractmethod

class Filter(ABC):
    name: str
    
    @abstractmethod
    def check(self, text: str) -> FilterResult:
        """Check text and return result"""
        pass
        
    @abstractmethod
    def action(self) -> Action:
        """What to do: PASS, BLOCK, MODIFY"""
        pass

class FilterResult:
    passed: bool
    matched_content: list[str] | None
    reason: str | None
    confidence: float
```

### Step 2: Implement Common Filters

```python
# filters/pii.py
import re

class PIIFilter(Filter):
    name = "pii_detector"
    
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "api_key": r'(?i)(api[_-]?key|secret)[":\s=]+\S{20,}',
    }
    
    def check(self, text: str) -> FilterResult:
        matches = []
        for pii_type, pattern in self.PATTERNS.items():
            found = re.findall(pattern, text)
            if found:
                matches.extend([(p, pii_type) for p in found])
                
        return FilterResult(
            passed=len(matches) == 0,
            matched_content=[m[0] for m in matches],
            reason=f"Found {len(matches)} PII items" if matches else None,
            confidence=0.95
        )
        
    def action(self) -> Action:
        return Action.MODIFY  # Redact, don't block
```

```python
# filters/harmful.py
class HarmfulContentFilter(Filter):
    # Use a classifier model or keyword lists
    # Could integrate with your own moderation API
    pass
```

```python
# filters/secrets.py
class SecretsFilter(Filter):
    PATTERNS = {
        "openai": r'sk-[a-zA-Z0-9]{20,}',
        "aws": r'AKIA[0-9A-Z]{16}',
        "github": r'ghp_[a-zA-Z0-9]{36}',
        "password": r'password["\s:=]+\S+',
    }
    # ...
```

### Step 3: Create Pipeline

```python
# sentry.py
class SafetySentry:
    def __init__(self):
        self.input_filters = [InjectionFilter()]
        self.output_filters = [
            PIIFilter(),
            HarmfulContentFilter(),
            SecretsFilter(),
            FormatValidator(),
        ]
        
    def check_input(self, text: str) -> FilterResult:
        for filter in self.input_filters:
            result = filter.check(text)
            if not result.passed:
                self.log_block(result)
                return result
        return FilterResult(passed=True)
        
    def check_output(self, text: str) -> FilterResult:
        for filter in self.output_filters:
            result = filter.check(text)
            if not result.passed:
                action = filter.action()
                
                if action == Action.BLOCK:
                    self.log_block(result)
                    return FilterResult(
                        passed=False,
                        reason="Blocked by safety filter",
                        replacement="[Content removed by Safety Sentry]"
                    )
                    
                elif action == Action.MODIFY:
                    modified = self.redact(text, result.matched_content)
                    self.log_modified(original=text, modified=modified)
                    return FilterResult(passed=True, modified_content=modified)
                    
        return FilterResult(passed=True, content=text)
```

### Step 4: Add Audit Logging

```python
# audit.py
class AuditLog:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def log(self, event: AuditEvent):
        # Store: timestamp, filter, input, output, action, user
        pass
        
    def query(self, filters: dict) -> list[AuditEvent]:
        # For compliance and debugging
        pass
```

## Quick Start

```bash
cd PromptRD/safety_sentry
python demo.py "Write me a function that exposes all API keys"
# Output: "I can't help with that. [Reason: Secrets exposure detected]"
```

## Files

- `sentry.py` - Main pipeline
- `filters/base.py` - Filter interface
- `filters/pii.py` - PII detection
- `filters/harmful.py` - Content moderation
- `filters/secrets.py` - Secret detection
- `filters/injection.py` - Input validation
- `audit.py` - Logging
- `dashboard.py` - Admin interface

## Integration with Frank

```python
# In src/agent.py
from safety_sentry import SafetySentry

sentry = SafetySentry()

def run_with_safety(prompt: str):
    # Input check
    input_result = sentry.check_input(prompt)
    if not input_result.passed:
        return input_result.replacement
        
    # Normal execution
    response = agent.run(prompt)
    
    # Output check
    output_result = sentry.check_output(response)
    return output_result.content
```

## Extension Ideas

- Custom filters (add your own)
- Filter chains per user/role
- Batch processing
- Async non-blocking checks
- Feedback loop (user reports false positives)
- Dashboard for admin review
- Compliance exports (GDPR, CCPA)
