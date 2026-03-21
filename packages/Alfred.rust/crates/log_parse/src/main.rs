#!/usr/bin/env rust
//! Log Parser - Parse and analyze log files

use anyhow::Result;
use chrono::{DateTime, Local};
use clap::{Parser, ValueEnum};
use regex::Regex;
use serde::Serialize;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Log file to parse
    #[arg(required = true)]
    file: PathBuf,

    /// Output format
    #[arg(short, long, value_enum, default_value = "text")]
    format: OutputFormat,

    /// Filter by log level
    #[arg(short, long)]
    level: Option<String>,

    /// Show last N lines
    #[arg(short, long, default_value = "0")]
    tail: usize,

    /// Show statistics
    #[arg(short, long)]
    stats: bool,
}

#[derive(Debug, Clone, ValueEnum)]
enum OutputFormat {
    Text,
    Json,
}

#[derive(Debug, Serialize)]
struct LogEntry {
    timestamp: Option<String>,
    level: String,
    message: String,
}

#[derive(Debug, Serialize)]
struct LogStats {
    total_lines: usize,
    parsed_entries: usize,
    level_counts: std::collections::HashMap<String, usize>,
}

fn parse_log_line(line: &str) -> Option<LogEntry> {
    // Common log patterns
    let patterns = [
        // ISO timestamp with level: 2024-01-15T10:30:00Z INFO message
        r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*)\s+(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\s+(.*)$",
        // Simple level: INFO: message or [INFO] message
        r"^(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)[:\s\]]+\s*(.*)$",
        // Just message (assume INFO)
        r"^(.*)$",
    ];

    for pattern in &patterns {
        if let Ok(re) = Regex::new(pattern) {
            if let Some(caps) = re.captures(line) {
                match caps.len() {
                    4 => {
                        return Some(LogEntry {
                            timestamp: Some(caps[1].to_string()),
                            level: caps[2].to_string(),
                            message: caps[3].to_string(),
                        })
                    }
                    3 => {
                        return Some(LogEntry {
                            timestamp: None,
                            level: caps[1].to_string(),
                            message: caps[2].to_string(),
                        })
                    }
                    2 => {
                        return Some(LogEntry {
                            timestamp: None,
                            level: "INFO".to_string(),
                            message: caps[1].to_string(),
                        })
                    }
                    _ => {}
                }
            }
        }
    }

    None
}

fn calculate_stats(entries: &[LogEntry]) -> LogStats {
    let mut level_counts = std::collections::HashMap::new();

    for entry in entries {
        *level_counts.entry(entry.level.clone()).or_insert(0) += 1;
    }

    LogStats {
        total_lines: entries.len(),
        parsed_entries: entries.len(),
        level_counts,
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    let content = fs::read_to_string(&args.file)?;
    let lines: Vec<&str> = content.lines().collect();

    // Apply tail filter
    let lines_to_parse: Vec<&str> = if args.tail > 0 && lines.len() > args.tail {
        lines[lines.len() - args.tail..].to_vec()
    } else {
        lines
    };

    // Parse entries
    let mut entries: Vec<LogEntry> = lines_to_parse
        .iter()
        .filter_map(|line| parse_log_line(line))
        .collect();

    // Filter by level
    if let Some(level) = &args.level {
        entries.retain(|e| e.level.to_uppercase() == level.to_uppercase());
    }

    if args.stats {
        let stats = calculate_stats(&entries);
        
        if args.format == OutputFormat::Json {
            println!("{}", serde_json::to_string_pretty(&stats)?);
        } else {
            println!("Log Statistics:");
            println!("  Total lines: {}", stats.total_lines);
            println!("  Parsed entries: {}", stats.parsed_entries);
            println!("\n  Level breakdown:");
            for (level, count) in &stats.level_counts {
                println!("    {}: {}", level, count);
            }
        }
        return Ok(());
    }

    // Output
    match args.format {
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&entries)?);
        }
        OutputFormat::Text => {
            for entry in &entries {
                let timestamp = entry
                    .timestamp
                    .as_ref()
                    .map(|t| t.as_str())
                    .unwrap_or("----");
                println!("[{}] {}: {}", timestamp, entry.level, entry.message);
            }
        }
    }

    Ok(())
}
