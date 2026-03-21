#!/usr/bin/env rust
//! Sleep - Cross-platform sleep command

use anyhow::Result;
use clap::Parser;
use std::thread;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Duration to sleep
    #[arg(required = true)]
    duration: String,
}

fn parse_duration(s: &str) -> Result<Duration> {
    let s = s.trim();
    
    // Check for unit suffix
    if s.ends_with('s') || s.ends_with("sec") || s.ends_with("secs") {
        let num: f64 = s[..s.len() - 1].parse()?;
        Ok(Duration::from_secs_f64(num))
    } else if s.ends_with('m') || s.ends_with("min") || s.ends_with("mins") {
        let num: f64 = s[..s.len() - 1].parse()?;
        Ok(Duration::from_secs_f64(num * 60.0))
    } else if s.ends_with('h') || s.ends_with("hr") || s.ends_with("hrs") {
        let num: f64 = s[..s.len() - 1].parse()?;
        Ok(Duration::from_secs_f64(num * 3600.0))
    } else if s.ends_with("ms") {
        let num: f64 = s[..s.len() - 2].parse()?;
        Ok(Duration::from_millis((num) as u64))
    } else {
        // Default to seconds
        let num: f64 = s.parse()?;
        Ok(Duration::from_secs_f64(num))
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    let duration = parse_duration(&args.duration)?;
    
    eprintln!("Sleeping for {:?}...", duration);
    thread::sleep(duration);
    eprintln!("Done.");

    Ok(())
}
