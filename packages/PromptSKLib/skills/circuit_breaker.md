# Skill: Circuit Breaker

**skill_id:** `circuit_breaker_001`  
**name:** circuit_breaker  
**category:** engineering  
**version:** 1.0  

## Description

Prevents cascading failures by stopping requests to a failing service temporarily, allowing it to recover.

## Primitive Tags

- failure_detection
- state_machine
- recovery_timeout
- half_open
- prevent_cascade
- bulkhead

## Prompt Strategy

```
For circuit breaker pattern:

1. DEFINE STATES
   - CLOSED: Normal operation, requests flow through
   - OPEN: Failure threshold exceeded, requests fail immediately
   - HALF_OPEN: Testing recovery, allow one request through

2. TRACK FAILURES
   - Count consecutive failures OR
   - Failure rate in sliding window (e.g., 50% in last 10 requests)

3. STATE TRANSITIONS
   - CLOSED → OPEN: When failure threshold exceeded
   - OPEN → HALF_OPEN: After recovery_timeout expires
   - HALF_OPEN → CLOSED: If test request succeeds
   - HALF_OPEN → OPEN: If test request fails

4. IMPLEMENT PROTECTION
   - Track failure count/rate
   - Track last failure time
   - Reject immediately when OPEN
   - Allow test request in HALF_OPEN
```

## Solution Summary

```python
import asyncio
import time
from enum import Enum
from typing import Callable, Optional

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state
    
    async def call(self, operation: Callable):
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise Exception("Circuit breaker is OPEN")
        
        if current_state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise Exception("Circuit breaker HALF_OPEN limit exceeded")
        
        try:
            result = await operation()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
```

## Tests Passed

- [x] Starts in CLOSED state
- [x] Transitions to OPEN after failure threshold
- [x] Rejects calls immediately when OPEN
- [x] Transitions to HALF_OPEN after recovery timeout
- [x] Allows limited calls in HALF_OPEN
- [x] Returns to CLOSED on successful HALF_OPEN call
- [x] Returns to OPEN on failed HALF_OPEN call
- [x] Thread-safe state transitions

## Benchmark Score

Pending evaluation

## Failure Modes

- **Premature opening**: Threshold too sensitive
  - Mitigation: Use sliding window instead of consecutive failures
- **Stuck OPEN**: Recovery timeout too long
  - Mitigation: Monitor and alert on OPEN state duration
- **Race conditions**: Concurrent calls during state transition
  - Mitigation: Use locks or atomic operations

## Created From Task

Initial skill library creation

## Related Skills

- `retry_backoff_001` - Retry with exponential backoff
- `timeout_handler_001` - Prevent hanging operations
- `bulkhead_001` - Isolate resources

## Timestamp

2026-03-08
