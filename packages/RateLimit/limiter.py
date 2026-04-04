# Updated-On: 2026-03-31
# Updated-By: Gordon
# PM-Ticket: UNTRACKED
# Central rate limiting logic. Replaces all custom implementations.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time
from typing import Dict, Tuple


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


@dataclass(frozen=True)
class RateLimitConfig:
    requests_per_second: float
    burst: int


def load_config(env_path: Path | None = None) -> RateLimitConfig:
    package_dir = Path(__file__).resolve().parent
    values = _parse_env_file(env_path or (package_dir / ".env"))
    requests_per_second = float(values.get("RATELIMIT_REQUESTS_PER_SECOND", "2"))
    burst = int(values.get("RATELIMIT_BURST", str(max(1, int(requests_per_second)))))
    if requests_per_second <= 0:
        raise ValueError("RATELIMIT_REQUESTS_PER_SECOND must be > 0")
    if burst <= 0:
        raise ValueError("RATELIMIT_BURST must be > 0")
    return RateLimitConfig(requests_per_second=requests_per_second, burst=burst)


class RateLimiter:
    """Token-bucket rate limiter with optional per-vendor sliding window limits.
    
    Supports two modes:
    1. Token bucket (global): configure via RateLimitConfig for constant throughput
    2. Per-vendor sliding window: add vendors with add_vendor() and check_vendor()
    """
    
    def __init__(self, config: RateLimitConfig | None = None, env_path: Path | None = None) -> None:
        self._config = config or load_config(env_path)
        self._lock = threading.Lock()
        self._tokens = float(self._config.burst)
        self._updated_at = time.monotonic()
        # Per-vendor sliding window limits (RPM): {vendor_name: (rpm_limit, list of timestamps)}
        self._vendor_windows: Dict[str, Tuple[int, list]] = {}
        self._window_duration = 60.0

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _refill(self, now: float) -> None:
        """Refill tokens based on elapsed time."""
        elapsed = max(0.0, now - self._updated_at)
        replenished = elapsed * self._config.requests_per_second
        self._tokens = min(float(self._config.burst), self._tokens + replenished)
        self._updated_at = now

    def add_vendor(self, vendor: str, rpm_limit: int) -> None:
        """Add per-vendor sliding window rate limit (requests per minute)."""
        with self._lock:
            self._vendor_windows[vendor] = (rpm_limit, [])

    def check_vendor(self, vendor: str) -> Tuple[bool, float]:
        """Check if vendor request is allowed. Returns (allowed, retry_after_seconds).
        
        Args:
            vendor: Vendor name (must be registered via add_vendor)
            
        Returns:
            (True, 0.0) if allowed
            (False, seconds_to_wait) if rate limited
        """
        if vendor not in self._vendor_windows:
            # Unregistered vendor — allow (no per-vendor limit)
            return True, 0.0
            
        with self._lock:
            rpm_limit, timestamps = self._vendor_windows[vendor]
            now = time.time()
            
            # Remove timestamps outside the window
            cutoff = now - self._window_duration
            self._vendor_windows[vendor] = (
                rpm_limit,
                [ts for ts in timestamps if ts > cutoff]
            )
            
            rpm_limit, timestamps = self._vendor_windows[vendor]
            if len(timestamps) >= rpm_limit:
                # At limit; return time until oldest request expires
                retry_after = max(0.0, (timestamps[0] + self._window_duration) - now)
                return False, retry_after
            
            # Consume slot
            self._vendor_windows[vendor][1].append(now)
            return True, 0.0

    def acquire(self) -> float:
        """Blocking acquire: wait until a token is available, then consume and return."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._refill(now)
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return 0.0
                deficit = 1.0 - self._tokens
                wait_seconds = deficit / self._config.requests_per_second
            time.sleep(wait_seconds)

    def try_acquire(self) -> bool:
        """Non-blocking acquire: return True if token available, False otherwise."""
        with self._lock:
            now = time.monotonic()
            self._refill(now)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    def wait_time_seconds(self) -> float:
        """Return seconds to wait before next token available (0 if available now)."""
        with self._lock:
            now = time.monotonic()
            self._refill(now)
            if self._tokens >= 1.0:
                return 0.0
            deficit = 1.0 - self._tokens
            return deficit / self._config.requests_per_second

    def vendor_status(self) -> Dict[str, Dict]:
        """Return current usage per vendor for monitoring/health checks."""
        with self._lock:
            now = time.time()
            status = {}
            for vendor, (rpm_limit, timestamps) in self._vendor_windows.items():
                # Remove expired timestamps
                cutoff = now - self._window_duration
                active = [ts for ts in timestamps if ts > cutoff]
                status[vendor] = {
                    "used": len(active),
                    "limit": rpm_limit,
                    "window_s": int(self._window_duration),
                }
            return status
