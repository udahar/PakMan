#!/usr/bin/env rust
//! Disk Info - Display disk information

use anyhow::Result;
use clap::Parser;
use serde::Serialize;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Drive letter (Windows) or path (Unix)
    #[arg(default_value = "C:")]
    drive: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

#[derive(Serialize)]
struct DiskInfo {
    drive: String,
    total_gb: f64,
    free_gb: f64,
    used_gb: f64,
    usage_percent: f64,
}

fn get_disk_info_windows(drive: &str) -> Option<DiskInfo> {
    let output = Command::new("powershell")
        .args([
            "-NoProfile",
            "-Command",
            &format!(
                "Get-PSDrive -Name '{}' | Select-Object Used,Free | ConvertTo-Json",
                drive.trim_end_matches(':')
            ),
        ])
        .output()
        .ok()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Simple parsing
    let mut used = 0.0;
    let mut free = 0.0;
    
    for line in stdout.lines() {
        if line.contains("\"Used\"") {
            if let Some(val) = line.split(':').nth(1) {
                used = val.trim().parse().unwrap_or(0.0);
            }
        }
        if line.contains("\"Free\"") {
            if let Some(val) = line.split(':').nth(1) {
                free = val.trim().parse().unwrap_or(0.0);
            }
        }
    }

    let total = used + free;
    let used_gb = used / (1024.0 * 1024.0 * 1024.0);
    let free_gb = free / (1024.0 * 1024.0 * 1024.0);
    let total_gb = total / (1024.0 * 1024.0 * 1024.0);
    let usage_percent = if total > 0.0 { (used / total) * 100.0 } else { 0.0 };

    Some(DiskInfo {
        drive: drive.to_string(),
        total_gb,
        free_gb,
        used_gb,
        usage_percent,
    })
}

fn main() -> Result<()> {
    let args = Args::parse();

    if let Some(info) = get_disk_info_windows(&args.drive) {
        if args.json {
            println!("{}", serde_json::to_string_pretty(&info)?);
        } else {
            println!("Drive: {}", info.drive);
            println!("Total: {:.2} GB", info.total_gb);
            println!("Free:  {:.2} GB", info.free_gb);
            println!("Used:  {:.2} GB", info.used_gb);
            println!("Usage: {:.1}%", info.usage_percent);
        }
    } else {
        eprintln!("Failed to get disk info for {}", args.drive);
    }

    Ok(())
}
