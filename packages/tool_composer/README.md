# Tool Composer - Visual AI Workflow Builder

A drag-and-drop interface for building AI pipelines by connecting nodes. No code required - just draw wires between components.

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Composer UI                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│   │  LLM    │──────│ Search  │──────│  Code   │           │
│   │ Node    │      │ Node    │      │ Node    │           │
│   └─────────┘      └─────────┘      └─────┬───┘           │
│        │                                   │                │
│        │            ┌─────────┐           │                │
│        └────────────│ Filter  │───────────┘                │
│                     │ Node    │                             │
│                     └─────────┘                             │
│                                                              │
│   [▶ Run]  [Save Pipeline]  [Export JSON]                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd C:\Users\Richard\clawd\Frank\PromptRD\tool_composer
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- Ollama running locally (http://127.0.0.1:11434)
- Streamlit (for UI)
- langchain-ollama (for LLM nodes)
- requests (for HTTP nodes)

## Quick Start

### Launch the UI

```bash
streamlit run toolcomposer/ui.py
```

### CLI Usage

```bash
# Run a pipeline
python -m toolcomposer.cli run my_pipeline.json

# Validate a pipeline
python -m toolcomposer.cli validate my_pipeline.json

# List available nodes
python -m toolcomposer.cli list

# Create a new pipeline
python -m toolcomposer.cli create --name "My Pipeline" --output pipeline.json

# Show pipeline info
python -m toolcomposer.cli info my_pipeline.json
```

### Run Demo

```bash
python demo.py
```

## Architecture

### Core Modules

| Module | Description | Lines |
|--------|-------------|-------|
| `models.py` | Data classes (Node, Edge, Pipeline) | ~200 |
| `base_node.py` | Abstract base class for nodes | ~150 |
| `node_registry.py` | Node registration system | ~120 |
| `flow_engine.py` | Pipeline execution engine | ~200 |
| `serializer.py` | JSON import/export | ~150 |
| `ui.py` | Streamlit UI | ~250 |
| `cli.py` | Command-line interface | ~200 |

### Node Modules

| Node | Category | File |
|------|----------|------|
| LLM | llm | `nodes/llm_node.py` |
| Bash | tool | `nodes/tool_nodes.py` |
| File Read/Write | tool | `nodes/tool_nodes.py` |
| HTTP | tool | `nodes/tool_nodes.py` |
| Filter | logic | `nodes/logic_nodes.py` |
| Transform | logic | `nodes/logic_nodes.py` |
| Merge | logic | `nodes/logic_nodes.py` |
| Condition | logic | `nodes/logic_nodes.py` |
| Input/Output | io | `nodes/input_output.py` |

## Node Types

### LLM Nodes

**LLM** - Interact with Ollama models

- Inputs: `prompt`
- Outputs: `response`
- Parameters: `model`, `base_url`, `temperature`, `system_prompt`

```json
{
  "type": "llm",
  "parameters": {
    "model": "qwen2.5:7b",
    "system_prompt": "You are a helpful assistant"
  }
}
```

### Tool Nodes

**Bash** - Execute shell commands

- Inputs: `command`
- Outputs: `output`, `stdout`, `stderr`, `returncode`
- Parameters: `timeout`, `shell`

**File Read** - Read file contents

- Inputs: `path`
- Outputs: `content`, `lines`
- Parameters: `encoding`, `base_dir`

**File Write** - Write content to file

- Inputs: `path`, `content`
- Outputs: `success`, `path`, `bytes`
- Parameters: `encoding`, `base_dir`, `append`

**HTTP** - Make HTTP requests

- Inputs: `url`, `method`, `body`
- Outputs: `response`, `status_code`, `headers`
- Parameters: `timeout`, `headers`

### Logic Nodes

**Filter** - Filter data based on conditions

- Inputs: `data`
- Outputs: `filtered`, `passed`
- Parameters: `condition`, `filter_type` (python/regex/contains)

**Transform** - Transform data

- Inputs: `data`
- Outputs: `result`
- Parameters: `transform`, `format`

**Merge** - Combine multiple inputs

- Inputs: `input1`, `input2`
- Outputs: `merged`
- Parameters: `merge_type`, `separator`, `template`

**Condition** - Conditional branching

- Inputs: `data`
- Outputs: `true_output`, `false_output`, `result`
- Parameters: `condition`, `true_value`, `false_value`

### I/O Nodes

**Input** - Provide initial input

- Inputs: (none)
- Outputs: `output`
- Parameters: `default`, `type` (text/json/number/boolean)

**Output** - Capture final output

- Inputs: `input`
- Outputs: `output`, `formatted`
- Parameters: `format`, `prefix`, `suffix`

## Pipeline JSON Format

```json
{
  "id": "my_pipeline",
  "name": "My Pipeline",
  "description": "Pipeline description",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "node_1",
      "type": "input",
      "name": "Input Node",
      "parameters": {
        "default": "Hello"
      }
    },
    {
      "id": "node_2",
      "type": "llm",
      "name": "LLM Node",
      "parameters": {
        "model": "qwen2.5:7b"
      }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "source_output": "output",
      "target_input": "prompt"
    }
  ],
  "variables": {}
}
```

## Examples

### Example 1: Simple LLM Query

```json
{
  "id": "simple_llm",
  "name": "Simple LLM",
  "nodes": [
    {"id": "input", "type": "input", "parameters": {"default": "Hello"}},
    {"id": "llm", "type": "llm", "parameters": {"model": "qwen2.5:7b"}},
    {"id": "output", "type": "output"}
  ],
  "edges": [
    {"source": "input", "target": "llm"},
    {"source": "llm", "target": "output"}
  ]
}
```

Run with:
```bash
python -m toolcomposer.cli run examples/simple_llm.json
```

### Example 2: Code Review Pipeline

```bash
python -m toolcomposer.cli run examples/code_review.json
```

### Example 3: Data Processing Pipeline

```bash
python -m toolcomposer.cli run examples/data_pipeline.json
```

## Python API

### Create Pipeline Programmatically

```python
from toolcomposer.models import PipelineConfig, NodeConfig, EdgeConfig
from toolcomposer.flow_engine import FlowEngine
from toolcomposer.serializer import PipelineSerializer

# Create pipeline
pipeline = PipelineConfig(
    id="my_pipeline",
    name="My Pipeline",
)

# Add nodes
pipeline.add_node(NodeConfig(
    id="input",
    type="input",
    parameters={"default": "Hello"},
))

pipeline.add_node(NodeConfig(
    id="llm",
    type="llm",
    parameters={"model": "qwen2.5:7b"},
))

# Add edges
pipeline.add_edge(EdgeConfig(
    id="e1",
    source_node="input",
    target_node="llm",
))

# Execute
engine = FlowEngine(pipeline)
result = engine.execute({"prompt": "Say hello"})

print(result.final_output)
```

### Load and Run Pipeline

```python
from toolcomposer.serializer import load_pipeline
from toolcomposer.flow_engine import FlowEngine

pipeline = load_pipeline("my_pipeline.json")
engine = FlowEngine(pipeline)
result = engine.execute({"initial": "data"})

print(f"Success: {result.success}")
print(f"Duration: {result.duration_ms}ms")
```

### Validate Pipeline

```python
from toolcomposer.serializer import PipelineSerializer

serializer = PipelineSerializer()
pipeline = load_pipeline("my_pipeline.json")

is_valid, errors = serializer.validate(pipeline)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

## Creating Custom Nodes

```python
from toolcomposer.base_node import BaseNode
from toolcomposer.node_registry import register_node


class CustomNode(BaseNode):
    node_type = "custom"
    category = "custom"
    inputs = ["input_data"]
    outputs = ["output_data"]
    description = "Custom processing node"

    def process(self, inputs: dict) -> dict:
        data = inputs.get("input_data")
        # Your custom logic here
        result = str(data).upper()
        return {"output_data": result}


# Register the node
register_node(CustomNode)
```

## File Structure

```
tool_composer/
├── toolcomposer/
│   ├── __init__.py           # Package exports
│   ├── models.py             # Core data models
│   ├── base_node.py          # Base node class
│   ├── node_registry.py      # Node registration
│   ├── flow_engine.py        # Execution engine
│   ├── serializer.py         # JSON import/export
│   ├── ui.py                 # Streamlit UI
│   ├── cli.py                # CLI interface
│   └── nodes/
│       ├── __init__.py
│       ├── llm_node.py       # LLM node
│       ├── tool_nodes.py     # Bash, File, HTTP nodes
│       ├── logic_nodes.py    # Filter, Transform, etc.
│       └── input_output.py   # Input/Output nodes
├── examples/
│   ├── simple_llm.json
│   ├── code_review.json
│   └── data_pipeline.json
├── demo.py                   # Demo script
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## Integration with Frank

Tool Composer integrates with Frank's tool system:

```python
from toolcomposer import FlowEngine, load_pipeline

# Load Frank's pipeline
pipeline = load_pipeline("frank_workflows/code_review.json")

# Execute with Frank's context
engine = FlowEngine(pipeline)
result = engine.execute({"code": frank_current_file()})
```

## Troubleshooting

### Ollama Connection Error

```
Error: LLM not available
```

**Solution:** Start Ollama server:
```bash
ollama serve
```

### Streamlit Not Found

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Pipeline Validation Failed

```
✗ Pipeline validation failed:
  - Edge references unknown source node: node_1
```

**Solution:** Check that all edge references point to existing node IDs.

## Best Practices

1. **Start Simple:** Begin with 2-3 nodes, then expand
2. **Validate Often:** Use `validate` command before running
3. **Use Descriptive Names:** Name nodes clearly (e.g., "fetch_api" not "node_1")
4. **Test Incrementally:** Test each node individually before connecting
5. **Save Versions:** Export working pipelines as JSON templates

## Future Enhancements

- [ ] Visual node editor (drag-and-drop canvas)
- [ ] Loop and iteration support
- [ ] Sub-pipelines (nested flows)
- [ ] Parallel node execution
- [ ] Visual debugging (highlight active nodes)
- [ ] Node versioning
- [ ] Pipeline templates library
- [ ] Error recovery strategies
- [ ] Performance profiling
- [ ] More node types (database, queue, email)

## License

Internal use - PromptRD Project
