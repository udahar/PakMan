#!/usr/bin/env rust
//! Response Parser - Parse structured data from LLM responses

use anyhow::Result;
use clap::Parser;
use regex::Regex;
use serde::Serialize;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// LLM response file (or - for stdin)
    #[arg(required = true)]
    input: PathBuf,

    /// Expected format (json, markdown, code)
    #[arg(short, long, default_value = "json")]
    format: String,

    /// Extract only the structured content
    #[arg(short, long)]
    extract: bool,

    /// Validate the output
    #[arg(short, long)]
    validate: bool,
}

#[derive(Serialize)]
struct ParseResult {
    success: bool,
    content: String,
    format: String,
    error: Option<String>,
}

fn extract_json(text: &str) -> Option<String> {
    // Try to find JSON object
    let mut brace_count = 0;
    let mut start = None;
    let mut end = None;

    for (i, c) in text.chars().enumerate() {
        match c {
            '{' => {
                if brace_count == 0 {
                    start = Some(i);
                }
                brace_count += 1;
            }
            '}' => {
                brace_count -= 1;
                if brace_count == 0 {
                    end = Some(i);
                    break;
                }
            }
            _ => {}
        }
    }

    if let (Some(start), Some(end)) = (start, end) {
        Some(text[start..=end].to_string())
    } else {
        None
    }
}

fn extract_code_block(text: &str, language: Option<&str>) -> Option<String> {
    let pattern = if let Some(lang) = language {
        format!("```{}\n(.*?)```", lang)
    } else {
        "```(?:\\w+)?\n(.*?)```".to_string()
    };

    if let Ok(re) = Regex::new(&pattern) {
        re.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
    } else {
        None
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Read input
    let content = if args.input.to_str() == Some("-") {
        let mut buffer = String::new();
        std::io::Read::read_to_string(&mut std::io::stdin(), &mut buffer)?;
        buffer
    } else {
        fs::read_to_string(&args.input)?
    };

    let mut result = ParseResult {
        success: true,
        content: String::new(),
        format: args.format.clone(),
        error: None,
    };

    match args.format.as_str() {
        "json" => {
            if args.extract {
                if let Some(json) = extract_json(&content) {
                    result.content = json;
                } else {
                    result.success = false;
                    result.error = Some("No JSON object found in response".to_string());
                }
            } else {
                result.content = content;
            }

            if args.validate && result.success {
                // Validate JSON
                if serde_json::from_str::<serde_json::Value>(&result.content).is_err() {
                    result.success = false;
                    result.error = Some("Invalid JSON".to_string());
                }
            }
        }
        "markdown" | "md" => {
            if args.extract {
                if let Some(code) = extract_code_block(&content, None) {
                    result.content = code;
                } else {
                    result.content = content;
                }
            } else {
                result.content = content;
            }
        }
        "code" => {
            if args.extract {
                // Try common languages
                for lang in ["rust", "python", "javascript", "typescript", "java"] {
                    if let Some(code) = extract_code_block(&content, Some(lang)) {
                        result.content = code;
                        result.format = lang.to_string();
                        break;
                    }
                }
                if result.content.is_empty() {
                    result.content = content;
                }
            } else {
                result.content = content;
            }
        }
        _ => {
            result.content = content;
        }
    }

    if args.format == "json" || args.format == "md" {
        println!("{}", serde_json::to_string_pretty(&result)?);
    } else {
        println!("{}", result.content);
    }

    Ok(())
}
