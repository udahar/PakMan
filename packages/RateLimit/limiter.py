# Updated-On: 2026-03-29
# Updated-By: Codex
# PM-Ticket: UNTRACKED
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time
from typing import Dict


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
    def __init__(self, config: RateLimitConfig | None = None, env_path: Path | None = None) -> None:
        self._config = config or load_config(env_path)
        self._lock = threading.Lock()
        self._tokens = float(self._config.burst)
        self._updated_at = time.monotonic()

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self._updated_at)
        replenished = elapsed * self._config.requests_per_second
        self._tokens = min(float(self._config.burst), self._tokens + replenished)
        self._updated_at = now

    def acquire(self) -> float:
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
        with self._lock:
            now = time.monotonic()
            self._refill(now)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    def wait_time_seconds(self) -> float:
        with self._lock:
            now = time.monotonic()
            self._refill(now)
            if self._tokens >= 1.0:
                return 0.0
            deficit = 1.0 - self._tokens
            return deficit / self._config.requests_per_second
