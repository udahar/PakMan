#!/usr/bin/env rust
//! JSON Formatter - Format or minify JSON files

use anyhow::Result;
use clap::Parser;
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Input file (or - for stdin)
    #[arg(required = true)]
    input: PathBuf,

    /// Output file (default: stdout)
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Minify (remove whitespace)
    #[arg(short, long)]
    minify: bool,

    /// Validate only (no output)
    #[arg(short, long)]
    validate: bool,
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

    // Parse JSON
    let parsed: serde_json::Value = serde_json::from_str(&content)?;

    if args.validate {
        println!("✓ Valid JSON");
        return Ok(());
    }

    // Format output
    let output = if args.minify {
        serde_json::to_string(&parsed)?
    } else {
        serde_json::to_string_pretty(&parsed)?
    };

    // Write output
    if let Some(out_path) = &args.output {
        fs::write(out_path, output)?;
        println!("Written to: {}", out_path.display());
    } else {
        println!("{}", output);
    }

    Ok(())
}
