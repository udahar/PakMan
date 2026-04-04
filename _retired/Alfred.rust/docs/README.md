# Rust Utility Bank - Complete Catalog

**40 Rust command-line utilities** for automation, AI integration, and system administration.

## Quick Start

```bash
cd C:\Users\Richard\clawd\Frank\Rust
cargo build --release
.\install.ps1 --release
```

---

## All Utilities (40 total)

### File Utilities (6)

| Tool | Description | Example |
|------|-------------|---------|
| `fs_scan` | Scan filesystem, output JSON | `fs_scan C:\path --json` |
| `file_hash` | Generate MD5/SHA256 hashes | `file_hash file.txt` |
| `file_watch` | Watch for file changes | `file_watch ./src --cmd "build"` |
| `dir_sync` | Compare/sync directories | `dir_sync ./src ./backup` |
| `file_search` | Fast file finder | `file_search "*.rs" ./src` |
| `du_rs` | Disk usage analyzer | `du_rs C:\Users` |

### Text Processing (5)

| Tool | Description | Example |
|------|-------------|---------|
| `json_fmt` | Format/minify JSON | `json_fmt config.json` |
| `grep_lite` | Simple grep | `grep_lite "TODO" ./src -r` |
| `text_extract` | Extract text from files | `text_extract binary.exe` |
| `line_count` | Count lines | `line_count *.rs` |
| `text_replace` | Find/replace | `text_replace "old" "new" file.txt` |

### System Tools (6)

| Tool | Description | Example |
|------|-------------|---------|
| `proc_list` | List processes | `proc_list --json` |
| `port_check` | Check ports | `port_check 80 443 8080` |
| `disk_info` | Disk information | `disk_info C:` |
| `net_stats` | Network statistics | `net_stats` |
| `env_dump` | Environment variables | `env_dump --json` |
| `sys_info` | System information | `sys_info` |

### Network Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `http_get` | HTTP GET client | `http_get https://api.example.com` |
| `ping_rs` | Ping utility | `ping_rs google.com -p 443` |
| `dns_lookup` | DNS resolver | `dns_lookup example.com` |

### Security Tools (2)

| Tool | Description | Example |
|------|-------------|---------|
| `password_check` | Password strength | `password_check "mypassword"` |
| `cert_info` | Certificate info | `cert_info example.com` |

### Development Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `git_status` | Git repo status | `git_status ./myproject` |
| `env_compare` | Compare .env files | `env_compare .env.dev .env.prod` |
| `diff_json` | Compare JSON files | `diff_json a.json b.json` |

### Admin Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `service_ctrl` | Windows services | `service_ctrl Spooler --action stop` |
| `event_log` | Event log viewer | `event_log System -n 50` |
| `reg_query` | Registry query | `reg_query "HKLM\SOFTWARE\MyApp"` |

### Automation Tools (5)

| Tool | Description | Example |
|------|-------------|---------|
| `queue_processor` | Process JSON queue | `queue_processor tasks.json -i 5` |
| `task_runner` | Run scheduled tasks | `task_runner config.json` |
| `scheduler` | Cron-like scheduler | `scheduler jobs.json` |
| `watcher` | Run on file change | `watcher ./src --cmd "cargo"` |
| `batch_run` | Batch command runner | `batch_run "gzip" *.txt` |

### Data Tools (6)

| Tool | Description | Example |
|------|-------------|---------|
| `csv_view` | View CSV as table | `csv_view data.csv` |
| `csv_to_json` | CSV to JSON | `csv_to_json input.csv` |
| `json_to_csv` | JSON to CSV | `json_to_csv input.json` |
| `log_parse` | Parse log files | `log_parse app.log --stats` |
| `config_reader` | Read config files | `config_reader settings.toml` |
| `data_sample` | Sample from large files | `data_sample --lines 1000 big.csv` |

### AI Helper Tools (5)

| Tool | Description | Example |
|------|-------------|---------|
| `prompt_fmt` | Format LLM prompts | `prompt_fmt prompt.txt --format ollama` |
| `response_parse` | Parse LLM responses | `response_parse output.txt --extract` |
| `context_pack` | Pack context tokens | `context_pack --max 4096 text.txt` |
| `model_list` | List Ollama models | `model_list` |
| `chat_session` | Interactive chat | `chat_session --model llama3.2` |

### Database Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `db_query` | Database queries | `db_query -t sqlite -c my.db -q "SELECT *"` |
| `cache_ctrl` | Cache management | `cache_ctrl --stats` |
| `rate_limiter` | Rate limiting | `rate_limiter --check` |

### Productivity Tools (3)

| Tool | Description | Example |
|------|-------------|---------|
| `clipboard` | Clipboard ops | `clipboard --copy "text"` |
| `note_take` | Quick notes | `note_take "Meeting at 3pm" -t work` |
| `bookmark` | Bookmark manager | `bookmark add https://example.com` |

### Misc Utilities (7)

| Tool | Description | Example |
|------|-------------|---------|
| `hash_gen` | Generate hashes | `hash_gen "text"` |
| `uuid_gen` | Generate UUIDs | `uuid_gen --count 5` |
| `epoch` | Timestamp converter | `epoch 1709654400` |
| `random_gen` | Random data | `random_gen -t password -l 16` |
| `sleep` | Cross-platform sleep | `sleep 5s` |
| `timer` | Countdown timer | `timer 25m` |
| `counter` | Simple counter | `counter --increment` |

---

## Integration Examples

### Python Integration

```python
import subprocess
import json

# Scan directory
result = subprocess.run(["fs_scan", "C:/path", "--json"], capture_output=True, text=True)
files = json.loads(result.stdout)

# Check password strength
result = subprocess.run(["password_check", "mypassword", "--json"], capture_output=True, text=True)
report = json.loads(result.stdout)
print(f"Strength: {report['strength']}")

# Process queue
subprocess.Popen(["queue_processor", "tasks.json", "--interval", "5"])

# Watch files
subprocess.Popen(["file_watch", "./src", "--command", "cargo build"])
```

### AI Agent Integration

```python
def run_tool(tool_name, *args, json=False):
    cmd = [tool_name] + list(args)
    if json:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if json else result.stdout

# AI can call tools:
files = run_tool('fs_scan', '/path', json=True)
git_info = run_tool('git_status', './project', json=True)
models = run_tool('model_list', json=True)
allowed = run_tool('rate_limiter', '--check')  # exits 0 or 1
```

### Batch/PowerShell Integration

```powershell
# Get system info
$files = fs_scan C:\Users --json | ConvertFrom-Json

# Check all ports
port_check 80,443,8080,11434,5432,6379

# Process monitoring
$procs = proc_list --json | ConvertFrom-Json
$procs | Where-Object { $_.cpu -gt 50 }

# Queue processing
queue_processor C:\tasks\queue.json --interval 10 --cleanup
```

---

## Building

```bash
# Build all
cargo build --release

# Build specific utility
cargo build -p fs_scan --release

# Build and install
.\install.ps1 --release
```

## Installation

Windows:
```powershell
.\install.ps1 --release
```

Linux/Mac:
```bash
./install.sh --release
```

## pkgman Integration

Add to your package manager:

```bash
pkgman install rust-fs-scan
pkgman install rust-json-fmt
pkgman install rust-queue-processor
pkgman install rust-file-watch
pkgman install rust-password-check
pkgman install rust-git-status
pkgman install rust-prompt-fmt
pkgman install rust-chat-session
```

---

## File Structure

```
Rust/
├── Cargo.toml              # Workspace config
├── README.md               # This file
├── install.ps1             # Windows installer
├── install.sh              # Linux/Mac installer
├── UTILITIES_CATALOG.md    # Detailed catalog
└── crates/
    ├── fs_scan/
    ├── file_hash/
    ├── file_watch/
    ├── json_fmt/
    ├── grep_lite/
    ├── proc_list/
    ├── port_check/
    ├── disk_info/
    ├── http_get/
    ├── ping_rs/
    ├── dns_lookup/
    ├── password_check/
    ├── git_status/
    ├── env_compare/
    ├── diff_json/
    ├── service_ctrl/
    ├── event_log/
    ├── reg_query/
    ├── queue_processor/
    ├── task_runner/
    ├── csv_view/
    ├── log_parse/
    ├── prompt_fmt/
    ├── response_parse/
    ├── model_list/
    ├── chat_session/
    ├── db_query/
    ├── cache_ctrl/
    ├── rate_limiter/
    ├── clipboard/
    ├── note_take/
    ├── bookmark/
    ├── hash_gen/
    ├── uuid_gen/
    ├── epoch/
    ├── random_gen/
    ├── sleep/
    └── ...
```

---

## Usage Patterns

### AI Automation Loop

```python
while True:
    # Check rate limit
    if subprocess.run(["rate_limiter", "--check"]).returncode != 0:
        time.sleep(60)
        continue
    
    # Scan for new files
    files = json.loads(subprocess.run(
        ["fs_scan", "/input", "--json"], capture_output=True, text=True
    ).stdout)
    
    # Process each file
    for file in files['entries']:
        # Format prompt
        prompt = subprocess.run(
            ["prompt_fmt", "template.txt", "--model", "llama3.2"],
            capture_output=True, text=True
        ).stdout
        
        # Call AI...
        
    # Log completion
    subprocess.run(["note_take", f"Processed {len(files)} files", "-t", "automation"])
    
    time.sleep(5)
```

### System Health Check

```bash
#!/bin/bash
# health_check.sh

echo "=== System Health ==="

# Disk
disk_info C: --json | jq '.usage_percent'

# Memory
proc_list --json | jq '[.[].memory] | add'

# Ports
port_check 11434 5432 6379

# Services
service_ctrl Ollama --action status

# Event log
event_log System -n 10 -l Error
```

---

## License

MIT - Internal use (PromptRD Project)
