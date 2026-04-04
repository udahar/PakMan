#!/usr/bin/env rust
//! DB Query - Simple database query wrapper

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Database type (postgres, mysql, sqlite)
    #[arg(short, long, default_value = "sqlite")]
    db_type: String,

    /// Connection string or file path
    #[arg(short, long, required = true)]
    connect: String,

    /// SQL query
    #[arg(short, long, required = true)]
    query: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    match args.db_type.as_str() {
        "sqlite" => {
            // Use sqlite3 command
            let output = Command::new("sqlite3")
                .args(["-json", &args.connect, &args.query])
                .output();

            match output {
                Ok(out) => {
                    let stdout = String::from_utf8_lossy(&out.stdout);
                    if args.json {
                        println!("{}", stdout);
                    } else {
                        // Parse and format
                        println!("{}", stdout);
                    }
                }
                Err(e) => {
                    eprintln!("SQLite error: {}", e);
                    eprintln!("Make sure sqlite3 is installed.");
                }
            }
        }
        "postgres" | "mysql" => {
            eprintln!("For {} use psql/mysql client directly", args.db_type);
            eprintln!("Example: psql {} -c \"{}\"", args.connect, args.query);
        }
        _ => {
            eprintln!("Unknown database type: {}", args.db_type);
        }
    }

    Ok(())
}
