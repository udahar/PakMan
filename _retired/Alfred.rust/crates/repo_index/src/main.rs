#!/usr/bin/env rust
//! Repo Index - Index repository files for AI embeddings
//!
//! Scans a directory and outputs file information including:
//! - Path
//! - Size
//! - Hash (SHA256)
//! - Language detection
//! - Modified time

use anyhow::Result;
use chrono::{DateTime, Local};
use clap::Parser;
use common::{print_json, ToolOutput};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author, version, about = "Index repository files for AI embeddings")]
struct Args {
    /// Directory to index
    #[arg(default_value = ".")]
    path: PathBuf,

    /// Max depth (0 = unlimited)
    #[arg(short, long, default_value = "0")]
    max_depth: usize,

    /// Include hidden files
    #[arg(short, long)]
    hidden: bool,

    /// File patterns to include (e.g., "*.rs,*.toml")
    #[arg(short, long)]
    include: Option<String>,

    /// File patterns to exclude (e.g., "*.git,*.lock")
    #[arg(short, long)]
    exclude: Option<String>,

    /// Calculate file hashes
    #[arg(short, long)]
    hash: bool,

    /// Output file (default: stdout)
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Output as JSON lines (NDJSON)
    #[arg(long)]
    jsonl: bool,
}

#[derive(Serialize, Debug)]
struct FileEntry {
    path: String,
    relative_path: String,
    size: u64,
    hash: Option<String>,
    language: String,
    extension: Option<String>,
    modified: Option<String>,
    is_binary: bool,
    line_count: Option<usize>,
}

#[derive(Serialize, Debug)]
struct IndexResult {
    indexed_path: String,
    total_files: usize,
    total_size: u64,
    languages: std::collections::HashMap<String, usize>,
    entries: Vec<FileEntry>,
    indexed_at: String,
}

fn detect_language(path: &Path) -> String {
    let ext = path.extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();

    match ext.as_str() {
        "rs" => "rust",
        "py" => "python",
        "js" | "mjs" => "javascript",
        "ts" => "typescript",
        "jsx" | "tsx" => "typescript-react",
        "go" => "go",
        "rb" => "ruby",
        "java" => "java",
        "c" | "h" => "c",
        "cpp" | "cc" | "cxx" | "hpp" => "cpp",
        "cs" => "csharp",
        "php" => "php",
        "swift" => "swift",
        "kt" | "kts" => "kotlin",
        "scala" => "scala",
        "rs" => "rust",
        "sh" | "bash" => "shell",
        "ps1" => "powershell",
        "bat" | "cmd" => "batch",
        "json" => "json",
        "yaml" | "yml" => "yaml",
        "toml" => "toml",
        "xml" => "xml",
        "md" => "markdown",
        "txt" => "text",
        "html" | "htm" => "html",
        "css" | "scss" | "sass" | "less" => "css",
        "sql" => "sql",
        "graphql" => "graphql",
        "proto" => "protobuf",
        "dockerfile" => "dockerfile",
        "makefile" => "makefile",
        "cmake" => "cmake",
        _ => {
            let filename = path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_lowercase();
            
            match filename.as_str() {
                "dockerfile" => "dockerfile",
                "makefile" => "makefile",
                "readme" => "markdown",
                "license" => "text",
                _ => "unknown",
            }
        }
    }
}

fn is_binary(content: &[u8]) -> bool {
    // Check for null bytes in first 8KB
    let sample = if content.len() > 8192 {
        &content[..8192]
    } else {
        content
    };
    
    sample.contains(&0u8)
}

fn count_lines(content: &[u8]) -> usize {
    std::str::from_utf8(content)
        .map(|s| s.lines().count())
        .unwrap_or(0)
}

fn compute_hash(path: &Path) -> Option<String> {
    let mut file = std::fs::File::open(path).ok()?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 8192];
    
    use std::io::Read;
    while let Ok(n) = file.read(&mut buffer) {
        if n == 0 {
            break;
        }
        hasher.update(&buffer[..n]);
    }
    
    Some(hex::encode(hasher.finalize()))
}

fn should_include_file(path: &Path, include: &Option<String>, exclude: &Option<String>) -> bool {
    let filename = path.file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("");

    // Check exclude patterns
    if let Some(patterns) = exclude {
        for pattern in patterns.split(',') {
            let pattern = pattern.trim();
            if pattern.starts_with("*.") {
                let ext = &pattern[1..];
                if filename.ends_with(ext) {
                    return false;
                }
            } else if filename.contains(pattern) {
                return false;
            }
        }
    }

    // Check include patterns
    if let Some(patterns) = include {
        for pattern in patterns.split(',') {
            let pattern = pattern.trim();
            if pattern.starts_with("*.") {
                let ext = &pattern[1..];
                if filename.ends_with(ext) {
                    return true;
                }
            } else if filename.contains(pattern) {
                return true;
            }
        }
        return false;
    }

    true
}

fn index_directory(args: &Args) -> Result<IndexResult> {
    let mut entries = Vec::new();
    let mut total_size = 0u64;
    let mut languages: std::collections::HashMap<String, usize> = std::collections::HashMap::new();

    let mut walker = WalkDir::new(&args.path)
        .follow_links(true)
        .into_iter()
        .filter_entry(|e| {
            // Skip hidden files unless requested
            if !args.hidden {
                let name = e.file_name().to_string_lossy();
                if name.starts_with('.') {
                    return false;
                }
            }
            
            // Skip depth
            if args.max_depth > 0 && e.depth() > args.max_depth {
                return false;
            }
            
            true
        });

    while let Some(Ok(entry)) = walker.next() {
        let path = entry.path();
        
        if !path.is_file() {
            continue;
        }

        // Check include/exclude patterns
        if !should_include_file(path, &args.include, &args.exclude) {
            continue;
        }

        let metadata = entry.metadata().ok();
        let size = metadata.as_ref().map(|m| m.len()).unwrap_or(0);
        
        let modified = metadata
            .as_ref()
            .and_then(|m| m.modified().ok())
            .map(|t| DateTime::from(t).to_rfc3339());

        let extension = path.extension()
            .and_then(|e| e.to_str())
            .map(|s| s.to_lowercase());

        let language = detect_language(path);

        // Read file content for hash and line count
        let content = std::fs::read(path).ok();
        let is_binary = content.as_ref().map(|c| is_binary(c)).unwrap_or(false);
        
        let line_count = if !is_binary {
            content.as_ref().map(|c| count_lines(c))
        } else {
            None
        };

        let hash = if args.hash && !is_binary {
            compute_hash(path)
        } else {
            None
        };

        // Get relative path
        let relative_path = path.strip_prefix(&args.path)
            .unwrap_or(path)
            .to_string_lossy()
            .to_string();

        total_size += size;
        *languages.entry(language.clone()).or_insert(0) += 1;

        entries.push(FileEntry {
            path: path.to_string_lossy().to_string(),
            relative_path,
            size,
            hash,
            language,
            extension,
            modified,
            is_binary,
            line_count,
        });
    }

    Ok(IndexResult {
        indexed_path: args.path.to_string_lossy().to_string(),
        total_files: entries.len(),
        total_size,
        languages,
        entries,
        indexed_at: Local::now().to_rfc3339(),
    })
}

fn main() -> Result<()> {
    let args = Args::parse();

    let result = index_directory(&args)?;

    if args.jsonl {
        // Output each entry as a separate JSON line
        for entry in &result.entries {
            println!("{}", serde_json::to_string(entry)?);
        }
    } else if args.json {
        print_json(&ToolOutput::success_json(serde_json::to_value(&result)?))?;
    } else {
        // Human-readable output
        println!("Repository Index");
        println!("================");
        println!("Path: {}", result.indexed_path);
        println!("Files: {}", result.total_files);
        println!("Total size: {:.2} MB", result.total_size as f64 / 1024.0 / 1024.0);
        println!();
        println!("Languages:");
        for (lang, count) in &result.languages {
            println!("  {}: {} files", lang, count);
        }
        println!();
        println!("First 20 files:");
        for entry in result.entries.iter().take(20) {
            let size_str = if entry.size > 1024 * 1024 {
                format!("{:.1}MB", entry.size as f64 / 1024.0 / 1024.0)
            } else if entry.size > 1024 {
                format!("{:.1}KB", entry.size as f64 / 1024.0)
            } else {
                format!("{}B", entry.size)
            };
            println!("  [{}] {} ({})", entry.language, entry.relative_path, size_str);
        }
        
        if result.entries.len() > 20 {
            println!("  ... and {} more", result.entries.len() - 20);
        }
    }

    // Save to file if requested
    if let Some(output) = &args.output {
        let json = serde_json::to_string_pretty(&result)?;
        std::fs::write(output, json)?;
        eprintln!("Saved to: {}", output.display());
    }

    Ok(())
}
