# AI Tool Integration Guide

Complete guide for integrating Rust utilities with AI agents.

## Overview

This utility bank provides three levels of AI integration:

```
Level 1: Direct subprocess calls
Level 2: MCP Server (JSON-RPC protocol)
Level 3: Schema auto-discovery + Pipelines
```

---

## Level 1: Direct Subprocess Calls

Simplest integration - call tools directly from Python:

```python
import subprocess
import json

def run_tool(tool_name, **kwargs):
    """Run a Rust utility and return result."""
    args = [tool_name]
    for key, value in kwargs.items():
        if isinstance(value, bool):
            if value:
                args.append(f"--{key}")
        else:
            args.append(f"--{key}={value}")
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    if "--json" in args or "--jsonl" in args:
        return json.loads(result.stdout)
    return result.stdout

# Examples
files = run_tool("fs_scan", "./project", json=True)
print(f"Found {files['data']['total_files']} files")

index = run_tool("repo_index", "./src", json=True, hash=True)
for entry in index["data"]["entries"]:
    print(f"  {entry['relative_path']} - {entry['language']}")
```

---

## Level 2: MCP Server

Production-ready JSON-RPC protocol for AI agents:

### Starting the Server

```bash
cargo run -p mcp_server
```

### Protocol

**Server → Client:** Tool manifest on startup

```json
{
  "type": "tool_list",
  "tools": [
    {
      "name": "fs_scan",
      "description": "Scan filesystem and output JSON structure",
      "input_schema": {...}
    }
  ]
}
```

**Client → Server:** Tool execution request

```json
{
  "tool": "fs_scan",
  "args": ["./project", "--json"],
  "id": "req-1"
}
```

**Server → Client:** Response

```json
{
  "id": "req-1",
  "success": true,
  "output": "{...tool output...}"
}
```

### Python Client

```python
import subprocess
import json

class MCPClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        # Read tool manifest
        self.manifest = json.loads(self.proc.stdout.readline())
    
    def list_tools(self):
        return [t["name"] for t in self.manifest["tools"]]
    
    def call(self, tool_name, **kwargs):
        args = []
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    args.append(f"--{key}")
            else:
                args.append(f"--{key}={value}")
        
        request = {
            "tool": tool_name,
            "args": args,
            "id": f"req-{tool_name}"
        }
        
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        
        return json.loads(self.proc.stdout.readline())

# Usage
client = MCPClient()
print("Available tools:", client.list_tools())

result = client.call("fs_scan", path="./project", json=True)
print("Files:", result["output"])
```

---

## Level 3: Schema Auto-Discovery

Get machine-readable schemas for all tools:

### Get All Tool Schemas

```bash
rustutils schema
# or
rustutils manifest
```

Output:
```json
{
  "version": "0.1.0",
  "tools": [
    {
      "name": "fs_scan",
      "description": "Scan filesystem and output JSON structure",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Directory to scan",
            "default": "."
          },
          "json": {
            "type": "boolean",
            "description": "Output as JSON",
            "default": false
          },
          "max-depth": {
            "type": "integer",
            "description": "Max directory depth",
            "default": 0
          }
        },
        "required": []
      }
    }
  ]
}
```

### Get Single Tool Schema

```bash
rustutils schema fs_scan
rustutils schema repo_index
rustutils schema prompt_fmt
```

### AI System Prompt

```
You have access to these tools:

{tool_manifest}

To use a tool, respond with:
```json
{
  "tool": "tool_name",
  "args": {
    "arg_name": "value"
  }
}
```

The system will execute the tool and return the result.

Available tools:
- fs_scan: Scan filesystem
- repo_index: Index repository for AI embeddings
- json_fmt: Format JSON
- proc_list: List processes
- port_check: Check ports
- file_hash: Generate file hashes
- file_watch: Watch for file changes
- queue_processor: Process task queues
- prompt_fmt: Format prompts for LLMs
- git_status: Check git repository status
- password_check: Check password strength
- http_get: HTTP GET client
- dns_lookup: DNS lookup
- clipboard: Clipboard operations
```

---

## Tool Pipelines

Chain multiple tools together:

### Pipeline JSON Format

```json
{
  "steps": [
    {
      "tool": "repo_index",
      "args": ["./src", "--json"]
    },
    {
      "tool": "json_fmt",
      "args": ["--minify"]
    },
    {
      "tool": "prompt_fmt",
      "args": ["--format", "ollama"]
    }
  ]
}
```

### Execute Pipeline

```bash
# From JSON string
rustutils pipe '{"steps":[{"tool":"repo_index","args":["./src","--json"]}]}'

# From file
rustutils pipe pipeline.json --input input.txt --output output.txt
```

### Python Pipeline Example

```python
import subprocess
import json

def run_pipeline(steps):
    """Execute a tool pipeline."""
    pipeline = {"steps": steps}
    
    result = subprocess.run(
        ["rustutils", "pipe", json.dumps(pipeline)],
        capture_output=True,
        text=True
    )
    
    return result.stdout

# AI workflow: Index repo → Format for LLM
pipeline = run_pipeline([
    {"tool": "repo_index", "args": ["./src", "--json", "--hash"]},
    {"tool": "json_fmt", "args": ["--minify"]},
    {"tool": "prompt_fmt", "args": ["--format", "ollama"]}
])

print(pipeline)
```

---

## NDJSON Streaming

For large datasets, use JSON Lines format:

### Output Format

Each line is a valid JSON object:
```json
{"path":"src/main.rs","size":1234,"language":"rust"}
{"path":"src/lib.rs","size":5678,"language":"rust"}
{"path":"Cargo.toml","size":901,"language":"toml"}
```

### Tools Supporting --jsonl

```bash
# Stream file index
repo_index ./project --jsonl

# Stream filesystem scan
fs_scan ./src --jsonl

# Process line by line in Python
import subprocess
import json

proc = subprocess.Popen(
    ["repo_index", "./src", "--jsonl"],
    stdout=subprocess.PIPE,
    text=True
)

for line in proc.stdout:
    entry = json.loads(line)
    print(f"File: {entry['path']} ({entry['language']})")
```

### Pipeline with Streaming

```bash
# Stream repo index → filter → process
repo_index ./src --jsonl | \
  grep '"language":"rust"' | \
  while read line; do
    echo "$line" | jq '.path'
  done
```

---

## Complete AI Integration Example

### Claude/AI System with Tools

```python
import subprocess
import json
from typing import Optional, Dict, Any

class AIToolManager:
    def __init__(self):
        # Load tool schemas
        result = subprocess.run(
            ["rustutils", "schema"],
            capture_output=True,
            text=True
        )
        self.manifest = json.loads(result.stdout)
        self.tools = {t["name"]: t for t in self.manifest["tools"]}
    
    def get_system_prompt(self) -> str:
        """Generate system prompt with tool descriptions."""
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in self.manifest["tools"]
        ])
        
        return f"""You are an AI assistant with access to these tools:

{tools_desc}

To use a tool, respond with a JSON object:
```json
{{
  "tool": "tool_name",
  "args": {{
    "arg_name": "value"
  }}
}}
```

I will execute the tool and return the result."""
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return output."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        
        cmd_args = [tool_name]
        for key, value in args.items():
            if isinstance(value, bool):
                if value:
                    cmd_args.append(f"--{key}")
            else:
                cmd_args.append(f"--{key}={value}")
        
        # Always request JSON output for parsing
        if "--json" not in cmd_args and "--jsonl" not in cmd_args:
            cmd_args.append("--json")
        
        result = subprocess.run(cmd_args, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        try:
            data = json.loads(result.stdout)
            return json.dumps(data, indent=2)
        except:
            return result.stdout
    
    def chat(self, user_message: str, conversation_history: list = None) -> str:
        """Process a chat message, potentially using tools."""
        # Here you would call your LLM API
        # The LLM would respond with tool calls
        pass

# Usage
manager = AIToolManager()
print(manager.get_system_prompt())

# Execute a tool
result = manager.execute_tool("fs_scan", {
    "path": "./project",
    "json": True,
    "max-depth": 2
})
print(result)
```

---

## Best Practices

### 1. Always Use --json for AI

```python
# Good
result = run_tool("fs_scan", "./path", json=True)
data = json.loads(result)

# Bad - hard to parse
result = run_tool("fs_scan", "./path")
```

### 2. Handle Errors Gracefully

```python
def safe_run_tool(tool_name, **kwargs):
    try:
        result = subprocess.run(
            [tool_name] + build_args(kwargs),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {"error": result.stderr}
        
        if kwargs.get("json"):
            return json.loads(result.stdout)
        return result.stdout
        
    except subprocess.TimeoutExpired:
        return {"error": f"Tool timed out after 30s"}
    except Exception as e:
        return {"error": str(e)}
```

### 3. Use Pipelines for Complex Workflows

```python
# Instead of multiple subprocess calls
files = run_tool("fs_scan", "./src", json=True)
filtered = [f for f in files if f["language"] == "rust"]
formatted = run_tool("json_fmt", input=filtered)

# Use a pipeline
pipeline = run_pipeline([
    {"tool": "fs_scan", "args": ["./src", "--json"]},
    {"tool": "filter", "args": ["language", "rust"]},
    {"tool": "json_fmt", "args": []}
])
```

### 4. Stream Large Results

```python
# Good for large repos
for line in stream_tool("repo_index", "./large-project", jsonl=True):
    entry = json.loads(line)
    process_entry(entry)

# Bad - loads everything into memory
result = run_tool("repo_index", "./large-project", json=True)
```

---

## Tool Reference

### File Operations

| Tool | JSON Output | Streaming | Schema |
|------|-------------|-----------|--------|
| fs_scan | ✓ | ✓ | ✓ |
| repo_index | ✓ | ✓ | ✓ |
| file_hash | ✓ | ✗ | ✓ |
| file_watch | ✗ | ✗ | ✓ |

### System Operations

| Tool | JSON Output | Streaming | Schema |
|------|-------------|-----------|--------|
| proc_list | ✓ | ✗ | ✓ |
| port_check | ✓ | ✗ | ✓ |
| disk_info | ✓ | ✗ | ✓ |
| git_status | ✓ | ✗ | ✓ |

### AI Helpers

| Tool | JSON Output | Streaming | Schema |
|------|-------------|-----------|--------|
| prompt_fmt | ✓ | ✗ | ✓ |
| response_parse | ✓ | ✗ | ✓ |
| model_list | ✓ | ✗ | ✓ |

---

## Troubleshooting

### Tool Not Found

```python
# Make sure tools are in PATH
import shutil
if not shutil.which("fs_scan"):
    print("Error: fs_scan not in PATH")
```

### JSON Parse Error

```python
# Check if tool supports --json
result = subprocess.run(["fs_scan", "--help"], capture_output=True, text=True)
if "--json" not in result.stdout:
    print("Warning: This tool may not support JSON output")
```

### Timeout Handling

```python
# Always set timeouts for AI safety
result = subprocess.run(
    ["repo_index", "./src", "--json"],
    capture_output=True,
    text=True,
    timeout=60  # 60 second limit
)
```

---

This is your complete AI integration layer. All 40+ tools are now:
- Auto-discoverable via schemas
- Chainable via pipelines
- Streamable via NDJSON
- MCP-compatible
