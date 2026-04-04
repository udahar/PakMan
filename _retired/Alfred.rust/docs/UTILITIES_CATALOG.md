# Rust Utilities Catalog

Complete catalog of all Rust utilities in this collection.

## File Utilities (6 tools)

### fs_scan
Scan filesystem and output JSON structure.

```bash
fs_scan C:\path\to\scan --json
fs_scan . --max-depth 2 --hidden
fs_scan /home --json --output files.json
```

**Options:**
- `--json` - Output as JSON
- `--max-depth N` - Limit directory depth
- `--hidden` - Include hidden files
- `--output FILE` - Save to file

---

### file_hash
Generate MD5, SHA256 hashes for files.

```bash
file_hash myfile.txt
file_hash --algorithm sha256 file1 file2
file_hash --recursive ./src
```

**Options:**
- `--algorithm` - md5, sha256, or both
- `--recursive` - Scan directories recursively

---

### file_watch
Watch files/directories for changes.

```bash
file_watch ./src --recursive
file_watch C:\logs --command "cargo build"
file_watch /path --verbose
```

**Options:**
- `--recursive` - Watch subdirectories
- `--command CMD` - Run command on change
- `--verbose` - Show detailed events

---

### dir_sync
Compare and sync two directories.

```bash
dir_sync ./source ./backup
dir_sync ./src /backup --dry-run
```

**Options:**
- `--dry-run` - Show what would be synced
- `--delete` - Remove extra files in destination

---

### file_search
Fast file finder with pattern matching.

```bash
file_search "*.rs" ./src
file_search "*.log" --older-than 7d
```

**Options:**
- `--pattern` - File pattern to match
- `--older-than` - Files older than N days
- `--newer-than` - Files newer than N days

---

### du_rs
Disk usage analyzer.

```bash
du_rs C:\Users
du_rs /home --max-depth 2
```

**Options:**
- `--max-depth N` - Limit depth
- `--sort` - Sort by size

---

## Text Processing (5 tools)

### json_fmt
Format or minify JSON files.

```bash
json_fmt input.json
json_fmt --minify input.json
json_fmt --validate config.json
```

**Options:**
- `--minify` - Remove whitespace
- `--validate` - Validate only
- `--output FILE` - Save to file

---

### grep_lite
Simple grep alternative.

```bash
grep_lite "pattern" file.txt
grep_lite "TODO" ./src --recursive --extension rs
```

**Options:**
- `--recursive` - Search directories
- `--ignore-case` - Case insensitive
- `--line-number` - Show line numbers
- `--extension` - Filter by extension
- `--max-results` - Limit results

---

### text_extract
Extract text from files (strip binary).

```bash
text_extract binary.exe
text_extract document.pdf --output text.txt
```

---

### line_count
Count lines in files.

```bash
line_count *.rs
line_count ./src --recursive
```

---

### text_replace
Find/replace in files.

```bash
text_replace "old" "new" file.txt
text_replace --regex "\d+" "NUMBER" *.log
```

---

## System Tools (6 tools)

### proc_list
List running processes.

```bash
proc_list
proc_list --json
proc_list --filter chrome --limit 10
```

**Options:**
- `--json` - Output as JSON
- `--filter` - Filter by name
- `--full` - Show full command line
- `--limit` - Limit results

---

### port_check
Check if ports are open/in use.

```bash
port_check 80 443 8080
port_check 11434 --host localhost
```

**Options:**
- `--host` - Host to check
- `--timeout` - Connection timeout

---

### disk_info
Display disk information.

```bash
disk_info C:
disk_info D: --json
```

**Options:**
- `--json` - Output as JSON

---

### net_stats
Network statistics.

```bash
net_stats
net_stats --interface eth0
```

---

### env_dump
Dump environment variables.

```bash
env_dump
env_dump --json
env_dump --filter PATH
```

---

### sys_info
System information.

```bash
sys_info
sys_info --json
```

---

## Automation Tools (5 tools)

### queue_processor
Process JSON queue every N seconds.

```bash
queue_processor tasks.json
queue_processor queue.json --interval 10 --cleanup
```

**Options:**
- `--interval N` - Seconds between runs
- `--cleanup` - Remove processed tasks
- `--max-tasks N` - Max tasks per run

**Example queue.json:**
```json
{
  "tasks": [
    {"id": "1", "action": "scan", "parameters": {"path": "/tmp"}},
    {"id": "2", "action": "notify", "parameters": {"message": "Done!"}}
  ]
}
```

---

### task_runner
Run scheduled/automated tasks.

```bash
task_runner tasks.json
task_runner config.json --task backup --dry-run
```

**Options:**
- `--dry-run` - Show what would run
- `--verbose` - Detailed output

---

### scheduler
Cron-like job scheduler.

```bash
scheduler jobs.json
```

---

### watcher
Run command when files change.

```bash
watcher ./src --command "cargo build"
watcher ./templates --pattern "*.html" --command "refresh"
```

---

### batch_run
Run command on multiple files.

```bash
batch_run "gzip" *.txt
batch_run "convert {} -resize 50% out_{}" *.jpg
```

---

## Data Tools (6 tools)

### csv_view
View CSV files as formatted tables.

```bash
csv_view data.csv
csv_view --max-rows 20 data.csv
csv_view --json data.csv
```

**Options:**
- `--delimiter` - Field separator
- `--max-rows` - Limit rows displayed
- `--json` - Output as JSON

---

### csv_to_json
Convert CSV to JSON.

```bash
csv_to_json input.csv --output output.json
```

---

### json_to_csv
Convert JSON to CSV.

```bash
json_to_json input.json --output output.csv
```

---

### log_parse
Parse and analyze log files.

```bash
log_parse app.log
log_parse --stats app.log
log_parse --level ERROR --tail 100 app.log
```

**Options:**
- `--level` - Filter by level
- `--tail N` - Last N lines
- `--stats` - Show statistics
- `--format` - Output format (text/json)

---

### config_reader
Read INI/TOML/YAML configs.

```bash
config_reader config.toml
config_reader --json settings.ini
```

---

### data_sample
Sample data from large files.

```bash
data_sample --lines 1000 large_file.csv
data_sample --percent 10 big_data.json
```

---

## AI Helper Tools (5 tools)

### prompt_fmt
Format prompts for LLM APIs.

```bash
prompt_fmt prompt.txt
prompt_fmt --system system.txt --model llama3.2
prompt_fmt --format ollama prompt.txt
```

**Options:**
- `--system FILE` - System prompt file
- `--model` - Model name
- `--temperature` - Temperature setting
- `--format` - json, ollama, openai, text

---

### response_parse
Parse structured data from LLM responses.

```bash
response_parse response.txt --format json --extract
response_parse --validate output.txt
```

**Options:**
- `--format` - Expected format (json/markdown/code)
- `--extract` - Extract only structured content
- `--validate` - Validate the output

---

### context_pack
Pack context into tokens.

```bash
context_pack --max-tokens 4096 input.txt
```

---

### token_count
Count tokens in text.

```bash
token_count prompt.txt
token_count --model gpt-4 text.txt
```

---

### embedding_prep
Prepare text for embeddings.

```bash
embedding_prep --chunk-size 512 document.txt
```

---

## Misc Utilities (7 tools)

### hash_gen
Generate various hashes.

```bash
hash_gen "my text"
hash_gen --algorithm sha256 "text"
```

**Options:**
- `--algorithm` - md5, sha256, sha512, all

---

### uuid_gen
Generate UUIDs.

```bash
uuid_gen
uuid_gen --count 10
uuid_gen --version 4 --json
```

**Options:**
- `--count` - Number to generate
- `--version` - UUID version (4 or 7)
- `--json` - Output as JSON array

---

### epoch
Unix timestamp converter.

```bash
epoch
epoch 1709654400
epoch now --json
```

**Options:**
- `--format` - Output format
- `--json` - Output as JSON

---

### random_gen
Generate random data.

```bash
random_gen --type string --length 32
random_gen --type password --length 16 --special
random_gen --type number --min 1 --max 100
```

**Options:**
- `--type` - string, password, number, bytes, hex
- `--length` - Output length
- `--count` - Number of items

---

### sleep
Cross-platform sleep command.

```bash
sleep 5s
sleep 1m
sleep 100ms
```

**Options:**
- Supports: s, m, h, ms suffixes

---

### timer
Countdown/pomodoro timer.

```bash
timer 25m
timer --break 5m
```

---

### counter
Simple counter.

```bash
counter --increment
counter --reset
```

---

## Integration Examples

### Python Integration

```python
import subprocess
import json

# Scan directory
result = subprocess.run(
    ["fs_scan", "C:/path", "--json"],
    capture_output=True, text=True
)
files = json.loads(result.stdout)

# Watch for changes
subprocess.Popen(
    ["file_watch", "./src", "--command", "cargo build"]
)

# Process queue
subprocess.run(["queue_processor", "tasks.json", "--interval", "5"])
```

### AI Agent Integration

```python
def run_tool(tool_name, *args, **kwargs):
    cmd = [tool_name] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if kwargs.get('json') else result.stdout

# AI can call:
files = run_tool('fs_scan', '/path', '--json', json=True)
hashes = run_tool('file_hash', 'file.txt')
formatted = run_tool('json_fmt', 'input.json')
```

### pkgman Integration

```bash
pkgman install fs_scan
pkgman install json_fmt
pkgman install queue_processor
pkgman install file_watch
pkgman install all-rust-utils
```

---

## Building

```bash
cd Rust
cargo build --release
```

All executables will be in `target/release/`

## Installing

Windows:
```powershell
.\install.ps1 --release
```

Linux/Mac:
```bash
./install.sh --release
```

## Updating

```bash
git pull
cargo build --release
.\install.ps1  # or ./install.sh
```
