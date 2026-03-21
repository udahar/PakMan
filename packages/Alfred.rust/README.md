# Alfred.rust

Rust workspace containing 47 native utility crates for the Alfred AI platform. High-performance subsystems used by Alfred's orchestration layer — things that need to be fast, reliable, and resource-minimal.

## Crates

| Crate | Description |
|-------|-------------|
| `mcp_server` | MCP protocol server implementation |
| `task_runner` | Async task queue and worker pool |
| `queue_processor` | Message queue processing |
| `model_list` | Ollama model inventory |
| `memory_client` | Qdrant vector store client |
| `observatory` | System metrics collector |
| `governor` | Rate limiting and flow control |
| `rate_limiter` | Per-vendor request throttling |
| `subsystem_registry` | Service discovery and registration |
| `skill_registry` | PakMan skill index |
| `service_ctrl` | Windows/Linux service management |
| `proc_list` | Process enumeration |
| `disk_info` | Disk usage and health |
| `port_check` | Port availability scanner |
| `dns_lookup` | DNS resolution utilities |
| `ping_rs` | ICMP ping |
| `http_get` | HTTP client primitives |
| `git_status` | Git repository status |
| `fs_scan` | Filesystem traversal |
| `file_watch` | File system event watcher |
| `file_hash` | Checksum and integrity |
| `log_parse` | Log file parsing |
| `event_log` | Windows Event Log reader |
| `reg_query` | Windows Registry reader |
| `grep_lite` | Fast pattern search |
| `diff_json` | JSON diff utility |
| `json_fmt` | JSON formatting |
| `schema_gen` | JSON Schema generator |
| `response_parse` | LLM response parser |
| `prompt_fmt` | Prompt formatting |
| `chat_session` | Chat session manager |
| `note_take` | Persistent note storage |
| `repo_index` | Repository indexing |
| `db_query` | Database query runner |
| `cache_ctrl` | Cache management |
| `clipboard` | Clipboard read/write |
| `csv_view` | CSV parsing and display |
| `env_compare` | Environment diff |
| `epoch` | Unix timestamp utilities |
| `hash_gen` | Hash generation |
| `password_check` | Password strength check |
| `random_gen` | Random value generation |
| `uuid_gen` | UUID generation |
| `sleep` | Async sleep primitives |
| `rustutils` | Shared utility library |
| `common` | Common types and traits |

## Build

```bash
# Windows
.\build.ps1

# Linux/WSL
./build.sh
```

## Install

```bash
# Windows
.\install.ps1

# Linux/WSL
./install.sh
```

## Requirements

- Rust 1.70+
- Cargo
