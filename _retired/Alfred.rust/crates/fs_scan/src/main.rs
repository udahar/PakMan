#!/usr/bin/env rust
//! Filesystem Scanner - Scan directories and output JSON structure

use anyhow::Result;
use chrono::DateTime;
use clap::Parser;
use serde::Serialize;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Directory to scan
    #[arg(default_value = ".")]
    path: PathBuf,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Max depth (0 = unlimited)
    #[arg(short, long, default_value = "0")]
    max_depth: usize,

    /// Include hidden files
    #[arg(short, long)]
    hidden: bool,

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
    name: String,
    size: u64,
    is_dir: bool,
    is_file: bool,
    modified: Option<String>,
    depth: usize,
}

#[derive(Serialize, Debug)]
struct ScanResult {
    scanned_path: String,
    total_files: usize,
    total_dirs: usize,
    total_size: u64,
    entries: Vec<FileEntry>,
    scan_time: String,
}

fn scan_directory(args: &Args) -> Result<ScanResult> {
    let mut entries = Vec::new();
    let mut total_files = 0;
    let mut total_dirs = 0;
    let mut total_size = 0u64;

    let mut walker = WalkDir::new(&args.path)
        .follow_links(true)
        .into_iter()
        .filter_entry(|e| {
            if !args.hidden {
                let name = e.file_name().to_string_lossy();
                if name.starts_with('.') {
                    return false;
                }
            }
            if args.max_depth > 0 {
                e.depth() <= args.max_depth
            } else {
                true
            }
        });

    while let Some(Ok(entry)) = walker.next() {
        let path = entry.path();
        let metadata = entry.metadata().ok();
        
        let is_dir = entry.file_type().is_dir();
        let is_file = entry.file_type().is_file();
        let size = metadata.as_ref().map(|m| m.len()).unwrap_or(0);
        let modified = metadata
            .as_ref()
            .and_then(|m| m.modified().ok())
            .map(|t| DateTime::from(t).to_rfc3339());

        if is_dir {
            total_dirs += 1;
        } else if is_file {
            total_files += 1;
            total_size += size;
        }

        entries.push(FileEntry {
            path: path.to_string_lossy().to_string(),
            name: entry.file_name().to_string_lossy().to_string(),
            size,
            is_dir,
            is_file,
            modified,
            depth: entry.depth(),
        });
    }

    Ok(ScanResult {
        scanned_path: args.path.to_string_lossy().to_string(),
        total_files,
        total_dirs,
        total_size,
        entries,
        scan_time: chrono::now().to_rfc3339(),
    })
}

fn main() -> Result<()> {
    let args = Args::parse();

    let result = scan_directory(&args)?;

    if args.jsonl {
        // Output each entry as a separate JSON line
        for entry in &result.entries {
            println!("{}", serde_json::to_string(entry)?);
        }
    } else if args.json {
        let output = serde_json::to_string_pretty(&result)?;
        if let Some(out_path) = &args.output {
            std::fs::write(out_path, output)?;
        } else {
            println!("{}", output);
        }
    } else {
        // Human-readable output
        println!("Scanned: {}", result.scanned_path);
        println!("Files: {}", result.total_files);
        println!("Directories: {}", result.total_dirs);
        println!("Total size: {:.2} MB", result.total_size as f64 / 1024.0 / 1024.0);
        println!("\nFirst 20 entries:");
        
        for entry in result.entries.iter().take(20) {
            let type_str = if entry.is_dir { "DIR " } else { "FILE" };
            let size_str = if entry.is_file {
                format!("{:>10}", entry.size)
            } else {
                "          ".to_string()
            };
            println!("{} {} {}", type_str, size_str, entry.path);
        }

        if result.entries.len() > 20 {
            println!("... and {} more", result.entries.len() - 20);
        }
    }

    Ok(())
}
