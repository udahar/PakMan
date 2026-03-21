#!/usr/bin/env rust
//! HTTP GET - Simple HTTP client

use anyhow::Result;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// URL to fetch
    #[arg(required = true)]
    url: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Show headers
    #[arg(short, long)]
    headers: bool,

    /// Timeout in seconds
    #[arg(short, long, default_value = "30")]
    timeout: u64,

    /// Output file
    #[arg(short, long)]
    output: Option<String>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(args.timeout))
        .build()?;

    let response = client.get(&args.url).send()?;

    if args.headers {
        println!("Status: {}", response.status());
        println!("\nHeaders:");
        for (name, value) in response.headers() {
            println!("  {}: {}", name, value.to_str().unwrap_or("?"));
        }
        println!();
    }

    let body = response.text()?;

    if let Some(out_file) = args.output {
        std::fs::write(&out_file, &body)?;
        println!("Saved to: {}", out_file);
    } else if args.json {
        println!("{}", serde_json::to_string_pretty(&serde_json::json!({
            "body": body
        }))?);
    } else {
        println!("{}", body);
    }

    Ok(())
}
