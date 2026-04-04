#!/usr/bin/env rust
//! Event Log - Query Windows Event Log

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Log name (System, Application, Security)
    #[arg(default_value = "System")]
    log_name: String,

    /// Number of events to retrieve
    #[arg(short, long, default_value = "20")]
    count: usize,

    /// Event level (Error, Warning, Information)
    #[arg(short, long)]
    level: Option<String>,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let level_filter = if let Some(level) = &args.level {
        format!(" -Level {}", level)
    } else {
        String::new()
    };

    let command = format!(
        "Get-WinEvent -LogName '{}' -MaxEvents {}{} -ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated,Id,LevelDisplayName,Message -First 10 | "
        "ConvertTo-Json",
        args.log_name, args.count, level_filter
    );

    let output = Command::new("powershell")
        .args(["-NoProfile", "-Command", &command])
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout);

    if args.json {
        println!("{}", stdout);
    } else {
        println!("Event Log: {}", args.log_name);
        println!("Last {} events{}\n", args.count, 
            if let Some(l) = &args.level { format!(" (Level: {})", l) } else { String::new() });
        
        // Simple parsing of PowerShell output
        println!("{}", stdout);
    }

    Ok(())
}
