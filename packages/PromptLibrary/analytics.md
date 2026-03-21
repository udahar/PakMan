# Prompt Analytics - Usage Tracking and Analysis

Track usage across all prompt systems.

## Usage

```python
from prompt_library import PromptAnalytics

analytics = PromptAnalytics()

# Track usage
analytics.track("blueprint_used", "streetpunk", success=True, user_rating=0.9)
analytics.track("skill_used", "humble_inquiry", success=True)

# Get stats
stats = analytics.get_stats(period="week")
print(f"Most used: {stats['top_blueprint']}")
print(f"Best success: {stats['best_skill']}")
```

## Features

- **Usage Tracking** - Auto-log every prompt use
- **Trend Analysis** - See patterns over time
- **Success Metrics** - What leads to good outcomes?

## Status

✅ Production Ready
