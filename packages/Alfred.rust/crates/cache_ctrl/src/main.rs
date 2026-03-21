#!/usr/bin/env rust
//! Cache Control - Manage cache directories

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about = "Cache Management Utility")]
struct Args {
    /// Cache directory
    #[arg(short, long, default_value = "./cache")]
    dir: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Show cache statistics
    Stats,
    /// Clear cache
    Clear {
        /// Clear only items older than N days
        #[arg(short, long)]
        older_than: Option<usize>,
    },
    /// Get cached value
    Get {
        /// Cache key
        key: String,
    },
    /// Set cached value
    Set {
        /// Cache key
        key: String,
        /// Value (or - for stdin)
        value: String,
        /// TTL in seconds
        #[arg(short, long)]
        ttl: Option<u64>,
    },
    /// List cache keys
    List,
}

fn get_cache_size(dir: &PathBuf) -> Result<u64> {
    let mut size = 0u64;
    if dir.exists() {
        for entry in fs::read_dir(dir)? {
            if let Ok(entry) = entry {
                if let Ok(meta) = entry.metadata() {
                    if meta.is_file() {
                        size += meta.len();
                    }
                }
            }
        }
    }
    Ok(size)
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Ensure cache directory exists
    fs::create_dir_all(&args.dir)?;

    match args.command {
        Commands::Stats => {
            let size = get_cache_size(&args.dir)?;
            let entries = fs::read_dir(&args.dir)?.count();
            
            println!("Cache Statistics:");
            println!("  Directory: {}", args.dir.display());
            println!("  Entries: {}", entries);
            println!("  Size: {:.2} KB", size as f64 / 1024.0);
        }
        Commands::Clear { older_than } => {
            if let Some(days) = older_than {
                let now = std::time::SystemTime::now();
                let threshold = std::time::Duration::from_secs(days as u64 * 86400);
                let mut cleared = 0;

                for entry in fs::read_dir(&args.dir)? {
                    if let Ok(entry) = entry {
                        if let Ok(meta) = entry.metadata() {
                            if let Ok(modified) = meta.modified() {
                                if now.duration_since(modified).unwrap_or_default() > threshold {
                                    let _ = fs::remove_file(entry.path());
                                    cleared += 1;
                                }
                            }
                        }
                    }
                }
                println!("Cleared {} entries older than {} days", cleared, days);
            } else {
                let _ = fs::remove_dir_all(&args.dir);
                fs::create_dir_all(&args.dir)?;
                println!("Cache cleared.");
            }
        }
        Commands::Get { key } => {
            let cache_file = args.dir.join(&key);
            if cache_file.exists() {
                let content = fs::read_to_string(&cache_file)?;
                println!("{}", content);
            } else {
                eprintln!("Cache miss: {}", key);
            }
        }
        Commands::Set { key, value, ttl } => {
            let cache_file = args.dir.join(&key);
            
            let content = if let Some(ttl) = ttl {
                let expires = chrono::Local::now().timestamp() + ttl as i64;
                format!("{}\n{}", expires, value)
            } else {
                value
            };

            fs::write(&cache_file, &content)?;
            println!("Cached: {}", key);
        }
        Commands::List => {
            println!("Cache keys:");
            for entry in fs::read_dir(&args.dir)? {
                if let Ok(entry) = entry {
                    println!("  {}", entry.file_name().to_string_lossy());
                }
            }
        }
    }

    Ok(())
}
