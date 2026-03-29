# RateLimit

> **Status:** BETA | **Tags:** infrastructure, throttling, rate-limit

## Overview
Standalone PakMan package that exposes a small token-bucket rate limiter with package-local configuration.

The package reads its defaults from the hidden file [`.env`](/C:/Users/Richard/clawd/PakMan/packages/RateLimit/.env) that lives beside the package code:

```dotenv
RATELIMIT_REQUESTS_PER_SECOND=2
RATELIMIT_BURST=2
```

## Installation
```bash
pakman install RateLimit
```

## Usage
```python
from RateLimit import RateLimiter

limiter = RateLimiter()
limiter.acquire()
```

You can change the package-local default by editing [`.env`](/C:/Users/Richard/clawd/PakMan/packages/RateLimit/.env).
