#!/usr/bin/env rust
//! Rate Limiter - Token bucket rate limiting

use anyhow::Result;
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Rate limit file
    #[arg(short, long, default_value = "./rate_limit.json")]
    file: PathBuf,

    /// Maximum requests
    #[arg(short, long, default_value = "100")]
    max: u32,

    /// Window in seconds
    #[arg(short, long, default_value = "60")]
    window: u64,

    /// Check if request is allowed
    #[arg(short, long)]
    check: bool,

    /// Reset counter
    #[arg(short, long)]
    reset: bool,

    /// Show status
    #[arg(short, long)]
    status: bool,
}

#[derive(Serialize, Deserialize, Default)]
struct RateLimit {
    count: u32,
    window_start: i64,
    max: u32,
    window_secs: u64,
}

impl RateLimit {
    fn load(path: &PathBuf) -> Result<Self> {
        if path.exists() {
            let content = fs::read_to_string(path)?;
            Ok(serde_json::from_str(&content)?)
        } else {
            Ok(Self::default())
        }
    }

    fn save(&self, path: &PathBuf) -> Result<()> {
        let content = serde_json::to_string_pretty(self)?;
        fs::write(path, content)?;
        Ok(())
    }

    fn check_and_increment(&mut self) -> bool {
        let now = chrono::Local::now().timestamp();
        
        // Reset window if expired
        if now - self.window_start >= self.window_secs as i64 {
            self.count = 0;
            self.window_start = now;
        }

        // Check if under limit
        if self.count < self.max {
            self.count += 1;
            true
        } else {
            false
        }
    }

    fn remaining(&self) -> u32 {
        let now = chrono::Local::now().timestamp();
        if now - self.window_start >= self.window_secs as i64 {
            self.max
        } else {
            self.max - self.count
        }
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut limit = RateLimit::load(&args.file)?;
    limit.max = args.max;
    limit.window_secs = args.window;

    if args.reset {
        limit.count = 0;
        limit.window_start = chrono::Local::now().timestamp();
        limit.save(&args.file)?;
        println!("Rate limit reset.");
        return Ok(());
    }

    if args.status {
        println!("Rate Limit Status:");
        println!("  Max: {} requests / {} seconds", limit.max, limit.window_secs);
        println!("  Used: {}", limit.count);
        println!("  Remaining: {}", limit.remaining());
        return Ok(());
    }

    if args.check {
        if limit.check_and_increment() {
            limit.save(&args.file)?;
            println!("ALLOWED (remaining: {})", limit.remaining());
            std::process::exit(0);
        } else {
            println!("DENIED (retry after {}s)", limit.window_secs);
            std::process::exit(1);
        }
    }

    // Default: show status
    println!("Rate Limit Status:");
    println!("  Max: {} requests / {} seconds", limit.max, limit.window_secs);
    println!("  Used: {}", limit.count);
    println!("  Remaining: {}", limit.remaining());

    Ok(())
}
