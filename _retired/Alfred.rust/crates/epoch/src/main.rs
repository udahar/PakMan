#!/usr/bin/env rust
//! Epoch Converter - Convert Unix timestamps

use anyhow::Result;
use chrono::{DateTime, Local, TimeZone};
use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Timestamp to convert (or "now" for current time)
    #[arg(default_value = "now")]
    timestamp: String,

    /// Output format
    #[arg(short, long, default_value = "iso")]
    format: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let (epoch, datetime) = if args.timestamp == "now" {
        let now = Local::now();
        (now.timestamp(), now)
    } else if let Ok(ts) = args.timestamp.parse::<i64>() {
        let dt = Local.timestamp_opt(ts, 0).unwrap();
        (ts, dt)
    } else {
        eprintln!("Invalid timestamp: {}", args.timestamp);
        eprintln!("Use a Unix timestamp (e.g., 1709654400) or 'now'");
        return Ok(());
    };

    let formatted = datetime.format(&args.format).to_string();

    if args.json {
        let output = serde_json::json!({
            "epoch": epoch,
            "iso": datetime.to_rfc3339(),
            "formatted": formatted,
        });
        println!("{}", serde_json::to_string_pretty(&output)?);
    } else {
        println!("Epoch: {}", epoch);
        println!("ISO:   {}", datetime.to_rfc3339());
        println!("{}:    {}", args.format, formatted);
    }

    Ok(())
}
