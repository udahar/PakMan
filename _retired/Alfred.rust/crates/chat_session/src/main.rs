#!/usr/bin/env rust
//! Chat Session - Interactive chat with Ollama

use anyhow::Result;
use clap::Parser;
use std::io::{self, Write};
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Model to use
    #[arg(short, long, default_value = "qwen2.5:7b")]
    model: String,

    /// System prompt
    #[arg(short, long)]
    system: Option<String>,

    /// Ollama URL
    #[arg(long, default_value = "http://127.0.0.1:11434")]
    url: String,
}

fn chat_with_ollama(prompt: &str, model: &str, system: Option<&str>) -> Result<String> {
    let prompt_json = serde_json::json!({
        "model": model,
        "prompt": prompt,
        "system": system.unwrap_or(""),
        "stream": false
    });

    let output = Command::new("powershell")
        .args([
            "-NoProfile",
            "-Command",
            &format!(
                "Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -ContentType 'application/json' -Body '{}' | Select-Object -ExpandProperty response",
                serde_json::to_string(&prompt_json)?
            ),
        ])
        .output()?;

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Chat Session with {}", args.model);
    println!("Type 'quit' or 'exit' to end session.\n");

    let mut stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        print!("> ");
        stdout.flush()?;

        let mut input = String::new();
        stdin.read_line(&mut input)?;

        let input = input.trim();
        if input.is_empty() {
            continue;
        }

        if input.eq_ignore_ascii_case("quit") || input.eq_ignore_ascii_case("exit") {
            println!("Goodbye!");
            break;
        }

        match chat_with_ollama(input, &args.model, args.system.as_deref()) {
            Ok(response) => {
                println!("\n{}\n", response);
            }
            Err(e) => {
                eprintln!("Error: {}", e);
            }
        }
    }

    Ok(())
}
