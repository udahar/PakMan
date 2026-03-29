# Updated-On: 2026-03-29
# Updated-By: Codex
# PM-Ticket: UNTRACKED
from __future__ import annotations

import argparse
import json
import time

try:
    from .limiter import RateLimiter
except Exception:
    from limiter import RateLimiter


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple token-bucket rate limiter for PakMan")
    parser.add_argument("--count", type=int, default=5, help="How many permits to acquire")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    limiter = RateLimiter()
    events = []
    for index in range(1, max(1, args.count) + 1):
        started_at = time.monotonic()
        limiter.acquire()
        granted_at = time.time()
        events.append(
            {
                "permit": index,
                "granted_at": granted_at,
                "waited_seconds": round(time.monotonic() - started_at, 4),
            }
        )

    if args.json:
        print(
            json.dumps(
                {
                    "requests_per_second": limiter.config.requests_per_second,
                    "burst": limiter.config.burst,
                    "count": len(events),
                    "events": events,
                },
                indent=2,
            )
        )
        return 0

    print(
        f"RateLimit granted {len(events)} permit(s) at "
        f"{limiter.config.requests_per_second}/sec with burst {limiter.config.burst}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
