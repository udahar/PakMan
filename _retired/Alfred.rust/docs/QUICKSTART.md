# Rust Utilities - Quick Start Guide

Get started with your 48-crate AI runtime in 5 minutes.

---

## Prerequisites

- Rust installed (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- Windows, Linux, or Mac

---

## Build (3 minutes)

### Windows
```powershell
cd C:\Users\Richard\clawd\Frank\Rust
.\build.ps1
```

### Linux/Mac
```bash
cd /path/to/Rust
./build.sh
```

---

## First Steps (2 minutes)

### 1. Test rustutils
```bash
# Windows
.\target\release\rustutils.exe --version

# Linux/Mac
./target/release/rustutils --version
```

### 2. List all tools
```bash
rustutils list
```

Output:
```
Available Rust Utilities:
========================

  fs_scan            Scan filesystem and output JSON structure
  repo_index         Index repository files for AI embeddings
  json_fmt           Format or minify JSON files
  proc_list          List running processes
  # ... 40+ more
```

### 3. Get tool schemas
```bash
rustutils schema
```

This outputs JSON schemas for all tools - perfect for AI discovery!

### 4. Scan a directory
```bash
rustutils fs_scan . --json
```

### 5. Register your first skill
```bash
rustutils skill register crates/skill_registry/examples/analyze_repo.json
```

### 6. List skills
```bash
rustutils skill list
```

### 7. Run a pipeline
```bash
rustutils pipe '{"steps":[{"tool":"fs_scan","args":[".","--json"]}]}'
```

---

## Python Integration

### Install dependencies
```bash
pip install requests
```

### Example: Call tools from Python
```python
import subprocess
import json

def run_tool(tool_name, **kwargs):
    args = [tool_name]
    for key, value in kwargs.items():
        if isinstance(value, bool):
            if value:
                args.append(f"--{key}")
        else:
            args.append(f"--{key}={value}")
    
    result = subprocess.run(
        ["rustutils"] + args,
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout) if "--json" in args else result.stdout

# Scan directory
files = run_tool("fs_scan", path="./project", json=True)
print(f"Found {files['data']['total_files']} files")

# Index repository
index = run_tool("repo_index", path="./src", json=True, hash=True)
for entry in index["data"]["entries"][:5]:
    print(f"  {entry['relative_path']} - {entry['language']}")
```

---

## MCP Server (AI Integration)

### Start MCP server
```bash
cargo run -p mcp_server --release
```

### Python MCP client
```python
import subprocess
import json

proc = subprocess.Popen(
    ["cargo", "run", "-p", "mcp_server", "--release"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Read tool manifest
manifest = json.loads(proc.stdout.readline())
print("Available tools:", [t["name"] for t in manifest["tools"]])

# Call a tool
request = {"tool": "fs_scan", "args": ["./project", "--json"]}
proc.stdin.write(json.dumps(request) + "\n")
proc.stdin.flush()

response = json.loads(proc.stdout.readline())
print("Result:", response["output"])
```

---

## Common Commands

### Tools
```bash
# Scan filesystem
rustutils fs_scan ./project --json

# Index repository
rustutils repo_index ./code --json --hash

# List processes
rustutils proc_list --json

# Check ports
rustutils port_check 80 443 8080

# Generate UUIDs
rustutils uuid_gen --count 5 --json
```

### Skills
```bash
# Register skill
rustutils skill register my_skill.json

# Search skills
rustutils skill search "analysis"

# List skills
rustutils skill list

# Run skill
rustutils skill run analyze_repo ./myproject
```

### Memory
```bash
# Store
rustutils memory store ticket:174 '{"status":"active"}'

# Recall
rustutils memory recall ticket:174

# Search
rustutils memory search "authentication"
```

### Pipelines
```bash
# Run pipeline
rustutils pipe '{"steps":[{"tool":"fs_scan","args":[".","--json"]}]}'

# Pipeline with file
rustutils pipe pipeline.json --input input.txt --output output.txt
```

### Genome
```bash
# Register tool
rustutils skill register-tool genome.json

# View fitness
rustutils skill capabilities filesystem.scan

# View lineage
rustutils skill lineage repo_index
```

---

## Example Skill JSON

```json
{
  "id": "analyze_repository",
  "name": "analyze_repository",
  "description": "Analyze a code repository",
  "pipeline": {
    "steps": [
      {"tool": "repo_index", "args": ["--json", "--hash"]},
      {"tool": "json_fmt", "args": ["--minify"]},
      {"tool": "prompt_fmt", "args": ["--format", "ollama"]}
    ]
  },
  "tags": ["analysis", "repository", "code"],
  "category": "analysis",
  "version": "1.0.0"
}
```

---

## Example Tool Genome JSON

```json
{
  "tool_id": "repo_index",
  "version": "1.0.0",
  "parent": "fs_scan",
  "capability": "filesystem.scan",
  "category": "filesystem",
  "created_by": "human",
  "fitness_score": 0.92,
  "mutation_type": "specialized_for_repos"
}
```

---

## Troubleshooting

### Build fails
```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
cargo build --release
```

### Tool not found
```bash
# Make sure you're using rustutils
rustutils fs_scan . --json

# Not individual binary
fs_scan . --json
```

### Skills not persisting
```bash
# Check skills.db exists
ls skills.db

# Or specify path
rustutils --db /path/to/skills.db skill list
```

---

## Next Steps

1. **Read the docs:**
   - `RUNTIME_ARCHITECTURE.md` - Full architecture
   - `AI_INTEGRATION.md` - AI integration patterns
   - `BEST_PRACTICES.md` - Rust CLI patterns

2. **Create your own skills:**
   - Copy `crates/skill_registry/examples/analyze_repo.json`
   - Modify the pipeline
   - Register with `rustutils skill register`

3. **Integrate with Alfred:**
   - Use MCP server for JSON-RPC
   - Or call rustutils directly via subprocess

4. **Track tool fitness:**
   - Record executions: `rustutils skill record fs_scan true --runtime 85`
   - View fitness: `rustutils skill capabilities filesystem.scan`

---

## Architecture Summary

```
48 crates total:
- 40 individual tools
- common (shared utilities)
- mcp_server (AI protocol)
- repo_index (file indexer)
- rustutils (main dispatcher)
- schema_gen (auto-discovery)
- skill_registry (skills + genome)
- memory_client (Postgres/Qdrant)
```

You now have a **complete AI runtime environment**!
