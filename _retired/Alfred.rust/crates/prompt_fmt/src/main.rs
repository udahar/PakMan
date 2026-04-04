#!/usr/bin/env rust
//! Prompt Formatter - Format prompts for LLM APIs

use anyhow::Result;
use clap::Parser;
use serde::Serialize;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Input prompt file (or - for stdin)
    #[arg(required = true)]
    input: PathBuf,

    /// System prompt file
    #[arg(short, long)]
    system: Option<PathBuf>,

    /// Output format
    #[arg(short, long, value_enum, default_value = "json")]
    format: OutputFormat,

    /// Model name to include
    #[arg(short, long)]
    model: Option<String>,

    /// Temperature (0.0 - 1.0)
    #[arg(short, long)]
    temperature: Option<f32>,
}

#[derive(Debug, Clone, clap::ValueEnum)]
enum OutputFormat {
    Json,
    Ollama,
    Openai,
    Text,
}

#[derive(Serialize)]
struct OllamaRequest {
    model: String,
    prompt: String,
    system: Option<String>,
    stream: bool,
    options: Option<ModelOptions>,
}

#[derive(Serialize)]
struct OpenAiRequest {
    model: String,
    messages: Vec<Message>,
    temperature: Option<f32>,
}

#[derive(Serialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct ModelOptions {
    temperature: f32,
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Read user prompt
    let prompt = if args.input.to_str() == Some("-") {
        let mut buffer = String::new();
        std::io::Read::read_to_string(&mut std::io::stdin(), &mut buffer)?;
        buffer
    } else {
        fs::read_to_string(&args.input)?
    };

    // Read system prompt if provided
    let system = if let Some(sys_path) = &args.system {
        Some(fs::read_to_string(sys_path)?)
    } else {
        None
    };

    let model = args.model.unwrap_or_else(|| "qwen2.5:7b".to_string());

    match args.format {
        OutputFormat::Json => {
            let output = serde_json::json!({
                "prompt": prompt,
                "system": system,
                "model": model,
            });
            println!("{}", serde_json::to_string_pretty(&output)?);
        }
        OutputFormat::Ollama => {
            let request = OllamaRequest {
                model,
                prompt,
                system,
                stream: false,
                options: args.temperature.map(|t| ModelOptions { temperature: t }),
            };
            println!("{}", serde_json::to_string_pretty(&request)?);
        }
        OutputFormat::OpenAi => {
            let mut messages = Vec::new();
            
            if let Some(sys) = system {
                messages.push(Message {
                    role: "system".to_string(),
                    content: sys,
                });
            }
            
            messages.push(Message {
                role: "user".to_string(),
                content: prompt,
            });

            let request = OpenAiRequest {
                model,
                messages,
                temperature: args.temperature,
            };
            println!("{}", serde_json::to_string_pretty(&request)?);
        }
        OutputFormat::Text => {
            if let Some(sys) = system {
                println!("SYSTEM:\n{}\n", sys);
            }
            println!("USER:\n{}", prompt);
        }
    }

    Ok(())
}
