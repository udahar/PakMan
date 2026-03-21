#!/usr/bin/env rust
//! Registry Query - Query Windows Registry

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Registry path (e.g., HKLM\SOFTWARE\MyApp)
    #[arg(required = true)]
    path: String,

    /// Value name (or empty for all values)
    #[arg(short, long)]
    value: Option<String>,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Convert registry path for reg query
    let reg_path = args.path.replace("\\", "\\");
    
    let command = if let Some(value) = &args.value {
        format!("reg query \"{}\" /v \"{}\"", reg_path, value)
    } else {
        format!("reg query \"{}\"", reg_path)
    };

    let output = Command::new("cmd")
        .args(["/C", &command])
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if args.json {
        println!("{}", serde_json::json!({
            "path": args.path,
            "output": stdout.to_string(),
            "error": if stderr.is_empty() { None } else { Some(stderr.to_string()) }
        }));
    } else {
        if !stderr.is_empty() {
            eprintln!("Error: {}", stderr);
        }
        println!("{}", stdout);
    }

    Ok(())
}
