# AutoCode - Multi-Agent Code Generation Framework

A collaborative AI system where specialized agents work together to design, implement, review, and test software.

## Overview

AutoCode implements a "Matrix for code review" - multiple AI agents with distinct personalities and expertise collaborate on software tasks, debating and iterating to produce high-quality results.

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Zoo                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Architect │  │  Coder   │  │ Reviewer │  │  Tester  │   │
│  │          │  │          │  │          │  │          │   │
│  │ - Design │  │ - Write  │  │ - Check  │  │ - Verify │   │
│  │ - Plan   │  │ - Impl   │  │ - Critique│ │ - Test   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │            │            │            │           │
│       └────────────┴────────────┴────────────┘           │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              │   Message Bus       │                       │
│              │   (async comm)      │                       │
│              └─────────────────────┘                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Zoo Keeper - Orchestrator                            │  │
│  │  - Spawns agents                                      │  │
│  │  - Manages workflow                                   │  │
│  │  - Resolves conflicts                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd C:\Users\Richard\clawd\Frank\PromptRD\AutoCode
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- Ollama running locally (http://127.0.0.1:11434)
- Required models: `qwen2.5:7b` (or configure custom model)

## Quick Start

### CLI Usage

```bash
# Basic usage
python -m autocode.cli "Build a REST API for todo list"

# With custom workflow
python -m autocode.cli --workflow iterative "Create a calculator"

# With custom model
python -m autocode.cli --model llama3.2 "Build a web scraper"

# Show statistics
python -m autocode.cli --stats

# List agents
python -m autocode.cli --agents

# Save results to directory
python -m autocode.cli -o json --output-dir results "Create auth module"
```

### Python API

```python
from autocode import ZooKeeper, ZooConfig

# Basic usage
zoo = ZooKeeper()
result = zoo.collaborate("Build a REST API for todo list")

print(result["design"])
print(result["implementation"])
print(result["review"])
print(result["tests"])

# Custom configuration
config = ZooConfig(
    model="llama3.2",
    workflow_type="iterative",
    log_level="DEBUG",
)
zoo = ZooKeeper(config)
result = zoo.collaborate("Create a calculator class")
```

### Run Demo

```bash
python demo.py
```

## Architecture

### Core Modules

| Module | Description | Lines |
|--------|-------------|-------|
| `models.py` | Data classes, enums, shared types | ~150 |
| `agent_base.py` | Abstract base class for all agents | ~150 |
| `message_bus.py` | Inter-agent communication | ~200 |
| `workflow_engine.py` | Workflow definitions and execution | ~250 |
| `zoo_keeper.py` | Main orchestrator | ~200 |
| `tools.py` | External tool integration | ~200 |
| `cli.py` | Command-line interface | ~200 |

### Agent Modules

| Agent | Role | File |
|-------|------|------|
| Architect | System design | `agents/architect.py` |
| Coder | Implementation | `agents/coder.py` |
| Reviewer | Code review | `agents/reviewer.py` |
| Tester | Test creation | `agents/tester.py` |

## Agents

### Architect

**Role:** System design and architecture

**Strengths:**
- Thinking in systems, patterns, and tradeoffs
- Designing maintainable, scalable solutions
- Technology choices and tradeoffs

**Prompt Focus:** "What's the best way to structure this?"

### Coder

**Role:** Code implementation

**Strengths:**
- Writing clean, efficient code
- Following best practices
- Error handling and edge cases

**Prompt Focus:** "How do I implement this correctly?"

### Reviewer

**Role:** Code quality assurance

**Strengths:**
- Finding bugs and security issues
- Identifying performance problems
- Suggesting improvements

**Prompt Focus:** "What could go wrong here?"

### Tester

**Role:** Quality assurance

**Strengths:**
- Writing comprehensive test suites
- Finding edge cases
- Breaking things to find bugs

**Prompt Focus:** "What could break?"

## Workflows

### Linear Workflow

Simple sequential flow:

```
Architect -> Coder -> Reviewer -> Tester
```

Each agent completes their task and passes results to the next.

### Iterative Workflow

Review-feedback-fix cycles:

```
Architect -> Coder -> Reviewer -> [if issues] Coder -> Reviewer -> Tester
```

Automatically iterates when critical issues are found.

## Message Bus

Agents communicate via structured messages:

```python
from autocode import AgentMessage, MessagePriority

message = AgentMessage(
    from_agent="architect",
    to_agent="coder",
    content="Here's the design specification...",
    thread_id="task_001",
    priority=MessagePriority.NORMAL,
)
```

### Message Priority Levels

- `LOW` - Background tasks
- `NORMAL` - Standard communication
- `HIGH` - Important updates
- `URGENT` - Critical issues

## Tool Integration

Agents can access external tools:

```python
from autocode.tools import create_frank_tools

tools = create_frank_tools(base_dir="/path/to/project")

# Available tools:
# - read_file
# - write_file
# - list_dir
# - file_exists
# - run_command
# - execute_python
```

## Examples

### Example 1: Simple Function

```python
from autocode import ZooKeeper

zoo = ZooKeeper()
result = zoo.collaborate("Create a function to validate email addresses")

print(result["implementation"])
```

### Example 2: Full Module

```python
zoo = ZooKeeper(workflow_type="iterative")
result = zoo.collaborate("""
Build a complete authentication module with:
- User registration
- Login/logout
- Password hashing
- JWT token generation
""")

# Save outputs
with open("design.md", "w") as f:
    f.write(result["design"])
with open("auth.py", "w") as f:
    f.write(result["implementation"])
```

### Example 3: Custom Model

```python
from autocode import ZooKeeper, ZooConfig

config = ZooConfig(
    model="llama3.2",
    base_url="http://localhost:11434",
    workflow_type="linear",
)

zoo = ZooKeeper(config)
result = zoo.collaborate("Build a data scraper")
```

## Configuration

### ZooConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | str | qwen2.5:7b | Ollama model name |
| `base_url` | str | http://127.0.0.1:11434 | Ollama server URL |
| `workflow_type` | str | linear | Workflow type |
| `log_level` | str | INFO | Logging level |
| `enable_logging` | bool | True | Enable logging |

## Output Format

```python
{
    "design": "...",           # Architect's design
    "implementation": "...",   # Coder's code
    "review": "...",           # Reviewer's feedback
    "tests": "...",            # Tester's test cases
    "summary": {
        "architect": {"success": True, "duration": 2.5},
        "coder": {"success": True, "duration": 3.2},
        "reviewer": {"success": True, "duration": 1.8},
        "tester": {"success": True, "duration": 2.1},
        "total_agents": 4,
        "successful": 4,
    }
}
```

## Statistics

```python
zoo = ZooKeeper()

# Agent statistics
agent_stats = zoo.get_agent_stats()

# Message bus statistics
msg_stats = zoo.get_message_stats()

# Workflow statistics
wf_stats = zoo.get_workflow_stats()

# All statistics
full_stats = zoo.get_full_stats()
```

## File Structure

```
AutoCode/
├── autocode/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Core data models
│   ├── agent_base.py        # Base agent class
│   ├── message_bus.py       # Communication system
│   ├── workflow_engine.py   # Workflow management
│   ├── zoo_keeper.py        # Main orchestrator
│   ├── tools.py             # Tool integration
│   ├── cli.py               # CLI interface
│   └── agents/
│       ├── __init__.py
│       ├── architect.py     # Architect agent
│       ├── coder.py         # Coder agent
│       ├── reviewer.py      # Reviewer agent
│       └── tester.py        # Tester agent
├── workflows/               # Custom workflow definitions
├── demo.py                  # Demo script
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Extending the System

### Adding a New Agent

```python
# agents/security.py
from autocode.agent_base import BaseAgent
from autocode.models import AgentConfig, AgentRole

SECURITY_PROMPT = """You are a security expert..."""

class SecurityAgent(BaseAgent):
    def __init__(self, model: str = "qwen2.5:7b"):
        config = AgentConfig(
            name="Security",
            role=AgentRole.ORCHESTRATOR,  # Or create custom role
            system_prompt=SECURITY_PROMPT,
            model=model,
        )
        super().__init__(config)

    def process_task(self, task: str, context: dict = None) -> str:
        # Implement security analysis logic
        return self.think(f"Analyze security: {task}")
```

### Adding a New Workflow

```python
from autocode.workflow_engine import BaseWorkflow

class SecurityWorkflow(BaseWorkflow):
    def get_total_steps(self) -> int:
        return 5  # Architect -> Coder -> Security -> Reviewer -> Tester

    def execute(self, message_bus, context=None):
        # Implement custom workflow logic
        pass
```

## Integration with Frank

AutoCode is designed to integrate with Frank's existing tool system:

```python
from autocode import ZooKeeper
from tools_enhanced import create_frank_tools

zoo = ZooKeeper()

# Access Frank's tools
tools = create_frank_tools()

# Use in agent context
result = tools.execute("read_file", path="existing_code.py")
```

## Troubleshooting

### Ollama Connection Error

```
Error: Connection refused to http://127.0.0.1:11434
```

**Solution:** Start Ollama server:
```bash
ollama serve
```

### Model Not Found

```
Error: Model qwen2.5:7b not found
```

**Solution:** Pull the model:
```bash
ollama pull qwen2.5:7b
```

### Import Errors

```
ModuleNotFoundError: No module named 'langchain_ollama'
```

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

## Best Practices

1. **Be Specific in Tasks:** Clear task descriptions produce better results
2. **Use Iterative for Complex Tasks:** More review cycles catch more issues
3. **Review Agent Outputs:** Always review before using generated code
4. **Save Results:** Use `--output-dir` to persist agent outputs
5. **Monitor Statistics:** Check `--stats` to understand system performance

## Future Enhancements

- [ ] Add debate mode (agents argue about approaches)
- [ ] Add voting (majority decides on conflicts)
- [ ] Add time pressure (agents respond in N seconds)
- [ ] Add memory (agents remember past collaborations)
- [ ] Add more specialized agents (DevOps, Database, UI/UX)
- [ ] Add parallel agent execution
- [ ] Add confidence scoring for outputs

## License

Internal use - PromptRD Project
