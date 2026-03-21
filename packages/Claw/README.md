# Claw

Thin CLI wrapper for the Alfred AI platform. Gives any PakMan-aware app a command-line interface to Alfred's multi-agent orchestration, benchmarking, and model management.

## Install

```bash
pakman install Claw
```

## Usage

```bash
# Ask Alfred a question
claw ask "summarize this week's benchmark results"

# List available models
claw models

# Trigger a benchmark run
claw bench --suite code

# Model election (King Gate)
claw crown
```

## API

```python
from Claw import ClawClient

client = ClawClient(alfred_url="http://localhost:5001")
task_id = client.submit_task("ask", {"prompt": "Hello"})
result = client.wait_for_result(task_id)
```

## Requirements

- Alfred running on `http://localhost:5001`
- Python 3.8+
- `requests`
