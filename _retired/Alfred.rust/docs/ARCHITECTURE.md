# Rust Utility Bank - AI-Ready Architecture

**40+ Rust command-line utilities** with a unified architecture for AI agent integration.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (LLM)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ JSON-RPC protocol
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│  - Advertises available tools                               │
│  - Receives JSON requests                                   │
│  - Spawns subprocess tools                                  │
│  - Returns JSON responses                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ subprocess calls
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  rustutils (main binary - git/docker/kubectl style)         │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│  │fs_scan  │json_fmt │proc_list│repo_... │  ...    │       │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘       │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Common Library (shared utilities)               │
│  - Logging setup                                            │
│  - JSON output helpers                                      │
│  - CLI argument helpers                                     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Build Everything

```bash
cd C:\Users\Richard\clawd\Frank\Rust
cargo build --release
```

### Install All Tools

```powershell
.\install.ps1 --release
```

### Test the MCP Server

```bash
# Start MCP server
cargo run -p mcp_server

# Send a request
echo '{"tool":"fs_scan","args":[".","--json"]}' | cargo run -p mcp_server
```

## Usage Patterns

### 1. Direct Tool Usage

```bash
# All tools support --json for machine-readable output
fs_scan ./project --json
proc_list --json
repo_index ./codebase --json --hash
```

### 2. Via rustutils (recommended)

```bash
# Single binary entry point
rustutils fs_scan ./project --json
rustutils proc_list --json
rustutils repo_index ./codebase --json

# List all tools
rustutils list

# Get tool manifest (for AI discovery)
rustutils manifest
```

### 3. Via MCP Server (AI integration)

```python
import subprocess
import json

# Start MCP server
proc = subprocess.Popen(
    ["mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Read tool manifest
manifest = json.loads(proc.stdout.readline())
print("Available tools:", [t["name"] for t in manifest["tools"]])

# Call a tool
request = {
    "tool": "fs_scan",
    "args": ["./project", "--json"],
    "id": "req-1"
}
proc.stdin.write(json.dumps(request) + "\n")
proc.stdin.flush()

# Read response
response = json.loads(proc.stdout.readline())
print("Result:", response["output"])
```

## Tool Manifest

Get machine-readable tool descriptions:

```bash
rustutils manifest
```

Output:
```json
{
  "tools": [
    {
      "name": "fs_scan",
      "description": "Scan filesystem and output JSON structure",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {"type": "string"},
          "--json": {"type": "boolean"},
          "--max-depth": {"type": "integer"}
        }
      }
    },
    {
      "name": "repo_index",
      "description": "Index repository files for AI embeddings",
      ...
    }
  ]
}
```

## All Tools (40+)

### Core Utilities

| Tool | Description | Example |
|------|-------------|---------|
| `fs_scan` | Scan filesystem | `fs_scan ./path --json` |
| `repo_index` | Index files for AI | `repo_index ./code --json --hash` |
| `json_fmt` | Format JSON | `json_fmt file.json` |
| `file_hash` | Generate hashes | `file_hash file.txt` |
| `file_watch` | Watch for changes | `file_watch ./src --cmd "build"` |

### System Tools

| Tool | Description | Example |
|------|-------------|---------|
| `proc_list` | List processes | `proc_list --json` |
| `port_check` | Check ports | `port_check 80 443` |
| `disk_info` | Disk information | `disk_info C:` |
| `git_status` | Git repo status | `git_status ./project --json` |

### AI Helpers

| Tool | Description | Example |
|------|-------------|---------|
| `prompt_fmt` | Format LLM prompts | `prompt_fmt prompt.txt --format ollama` |
| `response_parse` | Parse LLM output | `response_parse output.txt --extract` |
| `model_list` | List Ollama models | `model_list --json` |
| `chat_session` | Interactive chat | `chat_session --model llama3.2` |

### Network Tools

| Tool | Description | Example |
|------|-------------|---------|
| `http_get` | HTTP client | `http_get https://api.example.com` |
| `dns_lookup` | DNS resolver | `dns_lookup example.com --json` |

### Data Tools

| Tool | Description | Example |
|------|-------------|---------|
| `csv_view` | View CSV | `csv_view data.csv --json` |
| `log_parse` | Parse logs | `log_parse app.log --stats` |
| `env_compare` | Compare .env | `env_compare .env.dev .env.prod --json` |
| `diff_json` | Compare JSON | `diff_json a.json b.json` |

### Automation

| Tool | Description | Example |
|------|-------------|---------|
| `queue_processor` | Process queue | `queue_processor tasks.json -i 5` |
| `task_runner` | Run tasks | `task_runner config.json` |
| `rate_limiter` | Rate limiting | `rate_limiter --check` |
| `cache_ctrl` | Cache management | `cache_ctrl --stats` |

### Utilities

| Tool | Description | Example |
|------|-------------|---------|
| `uuid_gen` | Generate UUIDs | `uuid_gen --count 5 --json` |
| `hash_gen` | Generate hashes | `hash_gen "text"` |
| `epoch` | Timestamp converter | `epoch 1709654400 --json` |
| `random_gen` | Random data | `random_gen -t password -l 16` |
| `clipboard` | Clipboard ops | `clipboard --copy "text"` |
| `password_check` | Password strength | `password_check "pass" --json` |

## Python Integration

### Direct Subprocess

```python
import subprocess
import json

def run_tool(tool_name, *args, json_output=True):
    """Run a Rust utility and return result."""
    cmd = [tool_name] + list(args)
    if json_output:
        cmd.append("--json")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if json_output:
        return json.loads(result.stdout)
    return result.stdout

# Examples
files = run_tool("fs_scan", "./project")
print(f"Found {files['data']['total_files']} files")

index = run_tool("repo_index", "./src", "--hash")
for entry in index["data"]["entries"][:5]:
    print(f"  {entry['relative_path']} ({entry['language']})")
```

### MCP Client

```python
import subprocess
import json

class MCPClient:
    def __init__(self, server_path="mcp_server"):
        self.proc = subprocess.Popen(
            [server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        # Read manifest
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

## AI Agent Integration

### Claude/AI System Prompt

```
You have access to these Rust utilities via the MCP server:

{tool_manifest}

To use a tool, send a JSON request:
{"tool": "fs_scan", "args": ["./project", "--json"]}

The server will respond with:
{"success": true, "output": "..."}

Always use --json flag for machine-readable output.
```

### Example AI Workflow

```python
def ai_file_analysis(ai_client, directory):
    # Step 1: Index the repository
    index = run_tool("repo_index", directory, "--json", "--hash")
    
    # Step 2: Get file statistics
    stats = {
        "total_files": index["data"]["total_files"],
        "languages": index["data"]["languages"],
        "total_size": index["data"]["total_size"]
    }
    
    # Step 3: Send to AI for analysis
    prompt = f"""
    Analyze this codebase:
    - {stats['total_files']} files
    - Languages: {stats['languages']}
    - Size: {stats['total_size']} bytes
    
    What type of project is this?
    """
    
    response = ai_client.generate(prompt)
    return response
```

## File Structure

```
Rust/
├── Cargo.toml              # Workspace config
├── README.md               # This file
├── ARCHITECTURE.md         # Architecture docs
├── install.ps1             # Windows installer
├── install.sh              # Linux/Mac installer
└── crates/
    ├── common/             # Shared utilities
    │   ├── src/
    │   │   ├── lib.rs
    │   │   ├── output.rs   # JSON output helpers
    │   │   ├── logging.rs  # Logging setup
    │   │   └── cli.rs      # CLI helpers
    │   └── Cargo.toml
    ├── rustutils/          # Main binary (git/docker style)
    ├── mcp_server/         # MCP server for AI
    ├── repo_index/         # NEW: File indexer
    ├── fs_scan/
    ├── json_fmt/
    └── ... (40+ tools)
```

## Building

```bash
# Build all
cargo build --release

# Build specific tool
cargo build -p repo_index --release

# Build MCP server
cargo build -p mcp_server --release

# Build rustutils
cargo build -p rustutils --release
```

## Testing

```bash
# Test MCP server
echo '{"tool":"uuid_gen","args":["--count","3","--json"]}' | \
  cargo run -p mcp_server

# Test rustutils
cargo run -p rustutils -- manifest
cargo run -p rustutils -- list
cargo run -p rustutils -- fs_scan . --json
```

## Next Steps

1. **Auto-discovery**: Scan PATH for rustutils-* binaries
2. **Streaming output**: Support streaming for long-running tools
3. **Concurrent execution**: Run multiple tools in parallel
4. **Tool schemas**: Generate OpenAPI-like schemas for LLMs

## License

MIT - Internal use (PromptRD Project)
