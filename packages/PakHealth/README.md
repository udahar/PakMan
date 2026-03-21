# Health Monitor - System Wellness Dashboard

Monitor package health across all systems.

## Usage

```python
from health_monitor import Monitor

monitor = Monitor()

# Check all systems
health = monitor.check_all()

print(f"StockAI: {health['StockAI']['status']}")
print(f"PkgMan: {health['PkgMan']['status']}")

# Check specific system
result = monitor.check_import("StockAI")
print(f"Import OK: {result['ok']}")
```

## Features

- **Import Checks** - Verify packages can be imported
- **Port Checks** - Verify services are running (postgres, qdrant, redis)
- **Dependency Checks** - Verify required dependencies
- **API Smoke Tests** - Test basic functionality

## Status

✅ Production Ready
