# Skill: Retry with Exponential Backoff

**skill_id:** `retry_backoff_001`  
**name:** retry_with_exponential_backoff  
**category:** engineering  
**version:** 1.0  

## Description

Reliably handles transient failures by retrying operations with exponentially increasing delays between attempts.

## Primitive Tags

- retry_loop
- exponential_backoff
- jitter
- transient_failure
- timeout_handling
- max_attempts

## Prompt Strategy

```
For retry with backoff:

1. DEFINE PARAMETERS
   - max_attempts: Maximum retry count (default: 5)
   - base_delay: Initial delay in seconds (default: 1.0)
   - max_delay: Ceiling delay (default: 60.0)
   - exponential_base: Multiplier (default: 2.0)
   - jitter: Random variance to prevent thundering herd

2. IMPLEMENT RETRY LOOP
   - Attempt operation
   - On success: return immediately
   - On failure: check if retryable
   - Calculate delay: base_delay * (exponential_base ^ attempt)
   - Add jitter: delay * random(0.5, 1.5)
   - Sleep and retry

3. CLASSIFY ERRORS
   - Retryable: timeout, 503, connection reset, rate limit
   - Non-retryable: 400, 401, 403, 404, validation errors

4. FINAL FAILURE
   - After max_attempts: raise with all errors collected
```

## Solution Summary

```python
import asyncio
import random
from typing import TypeVar, Callable, Optional, Tuple

T = TypeVar('T')

async def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple = (Exception,)
) -> T:
    """
    Retry an operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay ceiling
        exponential_base: Base for exponential calculation
        jitter: Add randomness to prevent thundering herd
        retryable_exceptions: Tuple of exceptions to retry
    
    Returns:
        Result from successful operation
    
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                break
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            # Add jitter to prevent synchronized retries
            if jitter:
                delay *= random.uniform(0.5, 1.5)
            
            await asyncio.sleep(delay)
    
    raise last_exception
```

## Tests Passed

- [x] Succeeds on first attempt when operation works
- [x] Retries on transient failure
- [x] Exponential delay increases correctly (1s, 2s, 4s, 8s...)
- [x] Respects max_delay ceiling
- [x] Jitter adds variance to delays
- [x] Stops after max_attempts
- [x] Raises last exception on final failure
- [x] Only retries specified exception types

## Benchmark Score

Pending evaluation

## Failure Modes

- **Infinite retry**: max_attempts set too high
  - Mitigation: Default to 5, document trade-offs
- **Too aggressive**: base_delay too short
  - Mitigation: Default 1.0s, adjust based on operation
- **Non-retryable errors retried**: Wrong exception classification
  - Mitigation: Carefully define retryable_exceptions tuple

## Created From Task

Initial skill library creation

## Related Skills

- `circuit_breaker_001` - Prevent cascading failures
- `timeout_handler_001` - Prevent hanging operations
- `rate_limiter_001` - Respect API rate limits

## Timestamp

2026-03-08
