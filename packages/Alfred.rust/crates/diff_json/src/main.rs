#!/usr/bin/env rust
//! JSON Diff - Compare two JSON files

use anyhow::Result;
use clap::Parser;
use serde_json::Value;
use std::fs;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// First JSON file
    #[arg(required = true)]
    file1: String,

    /// Second JSON file
    #[arg(required = true)]
    file2: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn diff_values(path: &str, v1: &Value, v2: &Value, diffs: &mut Vec<String>) {
    match (v1, v2) {
        (Value::Object(m1), Value::Object(m2)) => {
            // Check keys in m1
            for (k, v1) in m1 {
                let new_path = if path.is_empty() {
                    k.clone()
                } else {
                    format!("{}.{}", path, k)
                };
                
                match m2.get(k) {
                    Some(v2) => diff_values(&new_path, v1, v2, diffs),
                    None => diffs.push(format!("{}: REMOVED", new_path)),
                }
            }
            
            // Check keys only in m2
            for k in m2.keys() {
                if !m1.contains_key(k) {
                    let path = if path.is_empty() {
                        k.clone()
                    } else {
                        format!("{}.{}", path, k)
                    };
                    diffs.push(format!("{}: ADDED", path));
                }
            }
        }
        (Value::Array(a1), Value::Array(a2)) => {
            if a1.len() != a2.len() {
                diffs.push(format!("{}: Array length changed ({} -> {})", path, a1.len(), a2.len()));
            }
            for (i, (v1, v2)) in a1.iter().zip(a2.iter()).enumerate() {
                diff_values(&format!("{}[{}]", path, i), v1, v2, diffs);
            }
        }
        (v1, v2) => {
            if v1 != v2 {
                let v1_str = match v1 {
                    Value::String(s) => s.clone(),
                    _ => v1.to_string(),
                };
                let v2_str = match v2 {
                    Value::String(s) => s.clone(),
                    _ => v2.to_string(),
                };
                diffs.push(format!("{}: {} -> {}", path, v1_str, v2_str));
            }
        }
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    let content1 = fs::read_to_string(&args.file1)?;
    let content2 = fs::read_to_string(&args.file2)?;

    let json1: Value = serde_json::from_str(&content1)?;
    let json2: Value = serde_json::from_str(&content2)?;

    let mut diffs = Vec::new();
    diff_values("", &json1, &json2, &diffs);

    if args.json {
        println!("{}", serde_json::json!({
            "file1": args.file1,
            "file2": args.file2,
            "identical": diffs.is_empty(),
            "differences": diffs
        }));
    } else {
        if diffs.is_empty() {
            println!("✓ Files are identical");
        } else {
            println!("Differences found:");
            for diff in &diffs {
                println!("  {}", diff);
            }
        }
    }

    Ok(())
}
