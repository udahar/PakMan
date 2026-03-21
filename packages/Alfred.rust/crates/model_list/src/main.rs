#!/usr/bin/env rust
//! Model List - List available Ollama models

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Ollama base URL
    #[arg(short, long, default_value = "http://127.0.0.1:11434")]
    url: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Show model sizes
    #[arg(short, long)]
    size: bool,
}

#[derive(serde::Deserialize)]
struct ModelInfo {
    name: String,
    size: Option<u64>,
    modified_at: Option<String>,
}

#[derive(serde::Deserialize)]
struct ModelResponse {
    models: Vec<ModelInfo>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let output = Command::new("powershell")
        .args([
            "-NoProfile",
            "-Command",
            &format!(
                "Invoke-RestMethod -Uri '{}/api/tags' | ConvertTo-Json -Depth 10",
                args.url
            ),
        ])
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    
    if args.json {
        println!("{}", stdout);
    } else {
        println!("Available Ollama Models:");
        println!("========================\n");
        
        // Simple parsing
        println!("{}", stdout);
    }

    Ok(())
}
