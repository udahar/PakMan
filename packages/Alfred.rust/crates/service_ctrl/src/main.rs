#!/usr/bin/env rust
//! Service Controller - Windows service management

use anyhow::Result;
use clap::{Parser, ValueEnum};
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Service name
    #[arg(required = true)]
    service: String,

    /// Action to perform
    #[arg(short, long, value_enum)]
    action: ServiceAction,
}

#[derive(Debug, Clone, ValueEnum)]
enum ServiceAction {
    Start,
    Stop,
    Restart,
    Status,
    List,
}

fn run_powershell(command: &str) -> Result<String> {
    let output = Command::new("powershell")
        .args(["-NoProfile", "-Command", command])
        .output()?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

fn main() -> Result<()> {
    let args = Args::parse();

    match args.action {
        ServiceAction::List => {
            let output = run_powershell("Get-Service | Select-Object Name,DisplayName,Status | ConvertTo-Json")?;
            println!("{}", output);
        }
        ServiceAction::Status => {
            let output = run_powershell(&format!(
                "Get-Service '{}' | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json",
                args.service
            ))?;
            println!("{}", output);
        }
        ServiceAction::Start => {
            println!("Starting service: {}", args.service);
            let _ = run_powershell(&format!("Start-Service '{}'", args.service));
            println!("Done.");
        }
        ServiceAction::Stop => {
            println!("Stopping service: {}", args.service);
            let _ = run_powershell(&format!("Stop-Service '{}'", args.service));
            println!("Done.");
        }
        ServiceAction::Restart => {
            println!("Restarting service: {}", args.service);
            let _ = run_powershell(&format!("Restart-Service '{}'", args.service));
            println!("Done.");
        }
    }

    Ok(())
}
