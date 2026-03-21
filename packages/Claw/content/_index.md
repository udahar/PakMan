# Claw

Claw is a thin CLI wrapper for the Alfred AI platform that provides simple commands to interact with Alfred's powerful AI capabilities without building another complex agent framework.

## Overview

Instead of duplicating Alfred's intelligence, Claw acts as a lightweight interface that sends tasks to Alfred's queue and waits for results. This approach leverages Alfred's existing capabilities:

- Model routing and selection
- Benchmarking and performance testing
- Memory and context management
- Tool orchestration

## Installation

```bash
# Install from local source
pip install ./path/to/claw

# Or install via pip (when published)
pip install claw
```

## Usage

### Command-Line Interface

```bash
# Ask a question using Alfred's best model
claw ask "optimize this sql query"

# Benchmark a specific model
claw bench deepseek-coder

# See available models
claw models

# Run task across multiple models for comparison
claw arena "write postgres migration"

# Get current model rankings
claw crown
```

### Python Library

```python
from claw import ClawClient, claw_ask

# Using the client class
client = ClawClient()
result = client.ask("explain quantum computing")

# Using convenience functions
result = claw_ask("what is the capital of france?")
```

## Features

- Simple, intuitive CLI interface
- Python library with convenient functions
- Leverages Alfred's existing AI capabilities
- Supports arena comparisons for model evaluation
- MIT licensed
- Well tested and documented

## Documentation

For detailed documentation, see the source code or generate documentation with ZolaPress.

## License

MIT License