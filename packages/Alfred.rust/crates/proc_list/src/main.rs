#!/usr/bin/env rust
//! Process List - List running processes

use anyhow::Result;
use clap::Parser;
use serde::Serialize;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Filter by name pattern
    #[arg(short, long)]
    filter: Option<String>,

    /// Show full command line
    #[arg(short, long)]
    full: bool,

    /// Limit results
    #[arg(short, long, default_value = "0")]
    limit: usize,
}

#[derive(Serialize, Debug)]
struct ProcessInfo {
    pid: u32,
    name: String,
    cpu_usage: f32,
    memory_usage: f32,
}

fn get_processes_windows() -> Vec<ProcessInfo> {
    let mut processes = Vec::new();

    // Use PowerShell to get process info
    let output = Command::new("powershell")
        .args([
            "-NoProfile",
            "-Command",
            "Get-Process | Select-Object Id,Name,CPU,WorkingSet | ConvertTo-Json",
        ])
        .output();

    if let Ok(output) = output {
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Simple parsing - in production use serde_json properly
        for line in stdout.lines() {
            if line.contains("\"Id\"") || line.contains("\"Name\"") {
                continue;
            }
            
            // Extract basic info from PowerShell output
            if let Some(pid_str) = line.split('"').nth(1) {
                if let Ok(pid) = pid_str.parse::<u32>() {
                    processes.push(ProcessInfo {
                        pid,
                        name: pid_str.to_string(),
                        cpu_usage: 0.0,
                        memory_usage: 0.0,
                    });
                }
            }
        }
    }

    processes
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut processes = get_processes_windows();

    // Filter by name
    if let Some(filter) = &args.filter {
        processes.retain(|p| p.name.to_lowercase().contains(&filter.to_lowercase()));
    }

    // Limit results
    if args.limit > 0 {
        processes.truncate(args.limit);
    }

    if args.json {
        println!("{}", serde_json::to_string_pretty(&processes)?);
    } else {
        println!("{:<8} {:<30} {:>10} {:>10}", "PID", "Name", "CPU%", "Mem%");
        println!("{}", "-".repeat(64));
        
        for proc in &processes {
            println!(
                "{:<8} {:<30} {:>10.2} {:>10.2}",
                proc.pid, proc.name, proc.cpu_usage, proc.memory_usage
            );
        }
        
        println!("\nTotal: {} processes", processes.len());
    }

    Ok(())
}
