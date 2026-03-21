# AutoCode

AutoCode is an AI-powered code generation assistant that helps developers generate, review, and test code using multiple specialized AI agents.

## Features

- Multi-agent collaboration (Architect, Coder, Reviewer, Tester)
- Message-based communication between agents
- Workflow engine for complex code generation tasks
- Extensible tool system for integrating with external services
- ZooKeeper for managing agent lifecycles

## Usage

```python
from autocode import WorkflowEngine, ZooKeeper

# Initialize the system
zk = ZooKeeper()
engine = WorkflowEngine(zk)

# Define and run a workflow
# ... see documentation for details
```

## API Reference

See the API documentation in the source code or generate documentation with ZolaPress.