#!/usr/bin/env rust
//! Grep Lite - Simple pattern search in files

use anyhow::Result;
use clap::Parser;
use regex::Regex;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Pattern to search
    #[arg(required = true)]
    pattern: String,

    /// Files or directories to search
    #[arg(required = true)]
    paths: Vec<PathBuf>,

    /// Case insensitive
    #[arg(short, long)]
    ignore_case: bool,

    /// Recursive search
    #[arg(short, long)]
    recursive: bool,

    /// Show line numbers
    #[arg(short, long)]
    line_number: bool,

    /// File extension filter (e.g., "rs", "txt")
    #[arg(short, long)]
    extension: Option<String>,

    /// Max results (0 = unlimited)
    #[arg(short, long, default_value = "0")]
    max_results: usize,
}

fn search_file(path: &PathBuf, regex: &Regex, args: &Args, count: &mut usize) -> Result<()> {
    let content = fs::read_to_string(path)?;
    
    for (line_num, line) in content.lines().enumerate() {
        if regex.is_match(line) {
            if args.max_results > 0 && *count >= args.max_results {
                return Ok(());
            }
            
            let line_display = if line.len() > 200 {
                format!("{}...", &line[..200])
            } else {
                line.to_string()
            };

            if args.line_number {
                println!("{}:{}: {}", path.display(), line_num + 1, line_display);
            } else {
                println!("{}: {}", path.display(), line_display);
            }
            
            *count += 1;
        }
    }
    
    Ok(())
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Build regex
    let pattern = if args.ignore_case {
        format!("(?i){}", args.pattern)
    } else {
        args.pattern.clone()
    };
    let regex = Regex::new(&pattern)?;

    let mut count = 0usize;

    for path in &args.paths {
        if path.is_file() {
            // Check extension filter
            if let Some(ext) = &args.extension {
                if path.extension().map(|e| e.to_str()) != Some(Some(ext)) {
                    continue;
                }
            }
            
            let _ = search_file(path, &regex, &args, &mut count);
        } else if path.is_dir() && args.recursive {
            for entry in walkdir::WalkDir::new(path)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file())
            {
                let entry_path = entry.path().to_path_buf();
                
                // Check extension filter
                if let Some(ext) = &args.extension {
                    if entry_path.extension().map(|e| e.to_str()) != Some(Some(ext)) {
                        continue;
                    }
                }
                
                let _ = search_file(&entry_path, &regex, &args, &mut count);
                
                if args.max_results > 0 && count >= args.max_results {
                    break;
                }
            }
        }
    }

    if args.max_results > 0 {
        println!("\nFound {} matches (max: {})", count, args.max_results);
    } else {
        println!("\nFound {} matches", count);
    }

    Ok(())
}
