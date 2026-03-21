# Scheduler

Task scheduling and cron-like functionality.

## Usage

```python
from scheduler import Scheduler

sched = Scheduler()
sched.every(60).seconds.do(task)
sched.run()
```
