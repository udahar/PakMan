# Rust CLI Best Practices

Patterns used across all 40+ utilities in this collection.

## 1. clap Derive Mode

All tools use `#[derive(Parser)]` for automatic CLI generation:

```rust
use clap::Parser;

#[derive(Parser)]
#[command(author, version, about)]
struct Args {
    /// Directory to scan
    #[arg(default_value = ".")]
    path: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();
    // --help generated automatically
    // --version generated automatically
}
```

**Benefits:**
- Free `--help` with nice formatting
- Free `--version`
- Type-safe argument parsing
- Environment variable support

---

## 2. anyhow for Error Handling

Clean error propagation everywhere:

```rust
use anyhow::{Result, Context};

fn main() -> Result<()> {
    let content = std::fs::read_to_string("config.json")
        .context("Failed to read config")?;
    
    do_work()?;
    Ok(())
}

fn do_work() -> Result<()> {
    // Errors automatically bubble up
    Ok(())
}
```

**Benefits:**
- No boilerplate error types
- Automatic error context
- Clean `?` operator

---

## 3. walkdir for Filesystem Traversal

Powerful recursive directory scanning:

```rust
use walkdir::WalkDir;

for entry in WalkDir::new(".")
    .follow_links(true)
    .into_iter()
    .filter_entry(|e| !is_hidden(e))
{
    let entry = entry?;
    println!("{}", entry.path().display());
}
```

**Benefits:**
- Handles symlinks safely
- Easy filtering
- Depth control
- Used by ripgrep, fd, etc.

---

## 4. JSON Output Pattern

Machine-readable output for AI integration:

```rust
use serde::Serialize;

#[derive(Serialize)]
struct Output {
    success: bool,
    data: Vec<String>,
    error: Option<String>,
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    let output = Output {
        success: true,
        data: scan_files()?,
        error: None,
    };
    
    if args.json {
        println!("{}", serde_json::to_string_pretty(&output)?);
    } else {
        // Human-readable format
        for item in &output.data {
            println!("  {}", item);
        }
    }
}
```

**Benefits:**
- AI-friendly output
- Easy piping to `jq`
- Consistent format across tools

---

## 5. tracing for Logging

Production-grade logging:

```rust
use tracing::{info, debug, error};

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    
    info!("Starting scan...");
    debug!("Path: {}", args.path);
    
    for file in &files {
        process(file)?;
    }
    
    Ok(())
}
```

Run with:
```bash
RUST_LOG=debug mytool
RUST_LOG=mytool=trace mytool
```

**Benefits:**
- Structured logging
- Runtime log level control
- Async-compatible

---

## 6. notify for File Watching

File system events:

```rust
use notify::{Watcher, RecursiveMode, recommended_watcher};

fn watch(path: &str, callback: impl Fn()) -> Result<()> {
    let (tx, rx) = std::sync::mpsc::channel();
    
    let mut watcher = recommended_watcher(tx)?;
    watcher.watch(path.as_ref(), RecursiveMode::Recursive)?;
    
    loop {
        match rx.recv() {
            Ok(event) => {
                println!("File changed: {:?}", event.paths);
                callback();
            }
            Err(e) => println!("Watch error: {}", e),
        }
    }
}
```

**Benefits:**
- Cross-platform
- Efficient (uses OS APIs)
- Recursive watching

---

## 7. common Crate for Shared Code

DRY principle across 40+ tools:

```rust
// crates/common/src/output.rs
use serde::Serialize;

pub fn print_json<T: Serialize>(data: &T) -> Result<()> {
    println!("{}", serde_json::to_string_pretty(data)?);
    Ok(())
}

pub fn print_success(msg: &str) {
    eprintln!("✓ {}", msg);
}
```

Usage in every tool:
```rust
use common::{print_json, print_success};

fn main() -> Result<()> {
    print_json(&data)?;
    print_success("Done!");
}
```

**Benefits:**
- Consistent output format
- Shared error handling
- Common utilities
- Easier maintenance

---

## 8. Unix Tool Behavior

Standard flags across all tools:

```bash
# Machine-readable output
--json

# Control verbosity
--quiet    # Minimal output
--verbose  # Debug info

# Standard POSIX
--help     # Usage info
--version  # Version number
```

**Benefits:**
- Predictable interface
- Easy scripting
- Composable pipelines

---

## 9. Piping Support

Tools work in pipelines:

```bash
# Pipe JSON to jq
fs_scan . --json | jq '.data.entries[] | .path'

# Pipe to grep
proc_list --json | grep -i python

# Chain tools
repo_index ./src --json | json_fmt | prompt_fmt --format ollama
```

**Implementation:**
```rust
// Read from stdin if "-"
let content = if args.input == "-" {
    let mut buffer = String::new();
    std::io::stdin().read_to_string(&mut buffer)?;
    buffer
} else {
    std::fs::read_to_string(&args.input)?
};
```

---

## 10. Rayon for Parallel Processing

Multi-core processing:

```rust
use rayon::prelude::*;

fn process_files(paths: &[PathBuf]) -> Result<()> {
    paths
        .par_iter()  // Parallel iterator
        .for_each(|path| {
            match process_file(path) {
                Ok(_) => info!("Processed: {}", path.display()),
                Err(e) => error!("Failed: {} - {}", path.display(), e),
            }
        });
    
    Ok(())
}
```

**Benefits:**
- Automatic parallelization
- Uses all CPU cores
- 10-100x faster on large datasets
- Zero-cost abstraction

---

## Example: Complete Tool Template

```rust
//! Tool Name - Description

use anyhow::Result;
use clap::Parser;
use common::{print_json, print_success, init_logging};
use rayon::prelude::*;
use serde::Serialize;
use tracing::info;
use walkdir::WalkDir;

#[derive(Parser)]
#[command(author, version, about)]
struct Args {
    /// Input path
    #[arg(default_value = ".")]
    path: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Parallel processing
    #[arg(short, long, default_value = "4")]
    threads: usize,
}

#[derive(Serialize)]
struct Output {
    items: Vec<String>,
    total: usize,
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    if args.verbose {
        init_logging("debug");
    }
    
    info!("Processing: {}", args.path);
    
    let items: Vec<String> = WalkDir::new(&args.path)
        .into_iter()
        .filter_map(|e| e.ok())
        .par_bridge()  // Parallel
        .filter_map(|e| {
            e.path()
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
        })
        .collect();
    
    let output = Output {
        items,
        total: items.len(),
    };
    
    if args.json {
        print_json(&output)?;
    } else {
        print_success(&format!("Found {} items", output.total));
        for item in &output.items {
            println!("  {}", item);
        }
    }
    
    Ok(())
}
```

---

## Composability Examples

```bash
# Development workflow
fs_scan ./src --json | jq '.entries[].path' | xargs wc -l

# AI workflow
repo_index ./code --json --hash | \
  json_fmt | \
  prompt_fmt --format ollama | \
  curl -X POST http://localhost:11434/api/generate -d @-

# System admin
proc_list --json | jq '.[] | select(.cpu > 50)'
port_check 80,443,8080,11434
event_log System -n 10 -l Error

# Automation
file_watch ./src --recursive --command "cargo build" &
queue_processor tasks.json --interval 5
```

---

## Performance Tips

1. **Use `par_iter()` for large collections**
2. **Buffer I/O operations**
3. **Use `mmap` for large file reading**
4. **Avoid unnecessary allocations**
5. **Profile with `cargo flamegraph`**

---

## Testing Tips

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_process() {
        assert_eq!(process("input"), "output");
    }
    
    #[test]
    fn test_json_output() {
        let output = run_tool(&["--json"]);
        assert!(serde_json::from_str::<Value>(&output).is_ok());
    }
}
```

Run tests:
```bash
cargo test
cargo test -- --nocapture  # Show println! output
```

---

This is the Rust CLI toolkit that powers tools like:
- ripgrep
- fd
- bat
- exa
- zoxide

And now your 40+ utility bank!
