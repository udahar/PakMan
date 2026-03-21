#!/usr/bin/env rust
//! Environment Comparator - Compare two .env files

use anyhow::Result;
use clap::Parser;
use std::collections::HashMap;
use std::fs;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// First .env file
    #[arg(required = true)]
    file1: String,

    /// Second .env file
    #[arg(required = true)]
    file2: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn parse_env(content: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        
        if let Some(eq_idx) = line.find('=') {
            let key = line[..eq_idx].trim().to_string();
            let value = line[eq_idx + 1..].trim().trim_matches('"').trim_matches('\'').to_string();
            map.insert(key, value);
        }
    }
    
    map
}

#[derive(serde::Serialize)]
struct EnvDiff {
    file1: String,
    file2: String,
    only_in_file1: Vec<String>,
    only_in_file2: Vec<String>,
    different: Vec<DiffEntry>,
    same: usize,
}

#[derive(serde::Serialize)]
struct DiffEntry {
    key: String,
    value1: String,
    value2: String,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let content1 = fs::read_to_string(&args.file1)?;
    let content2 = fs::read_to_string(&args.file2)?;

    let env1 = parse_env(&content1);
    let env2 = parse_env(&content2);

    let mut only_in_file1 = Vec::new();
    let mut only_in_file2 = Vec::new();
    let mut different = Vec::new();
    let mut same_count = 0;

    // Find keys only in file1 or different
    for (key, value1) in &env1 {
        match env2.get(key) {
            Some(value2) => {
                if value1 == value2 {
                    same_count += 1;
                } else {
                    different.push(DiffEntry {
                        key: key.clone(),
                        value1: value1.clone(),
                        value2: value2.clone(),
                    });
                }
            }
            None => {
                only_in_file1.push(key.clone());
            }
        }
    }

    // Find keys only in file2
    for key in env2.keys() {
        if !env1.contains_key(key) {
            only_in_file2.push(key.clone());
        }
    }

    let diff = EnvDiff {
        file1: args.file1.clone(),
        file2: args.file2.clone(),
        only_in_file1,
        only_in_file2,
        different,
        same: same_count,
    };

    if args.json {
        println!("{}", serde_json::to_string_pretty(&diff)?);
    } else {
        println!("Environment Comparison");
        println!("======================");
        println!("File 1: {}", args.file1);
        println!("File 2: {}", args.file2);
        println!();
        println!("Summary:");
        println!("  Same:           {}", diff.same);
        println!("  Different:      {}", diff.different.len());
        println!("  Only in file 1: {}", diff.only_in_file1.len());
        println!("  Only in file 2: {}", diff.only_in_file2.len());
        
        if !diff.different.is_empty() {
            println!("\nDifferent values:");
            for entry in &diff.different {
                println!("  {}:", entry.key);
                println!("    File 1: {}", entry.value1);
                println!("    File 2: {}", entry.value2);
            }
        }
        
        if !diff.only_in_file1.is_empty() {
            println!("\nOnly in file 1:");
            for key in &diff.only_in_file1 {
                println!("  {}", key);
            }
        }
        
        if !diff.only_in_file2.is_empty() {
            println!("\nOnly in file 2:");
            for key in &diff.only_in_file2 {
                println!("  {}", key);
            }
        }
    }

    Ok(())
}
