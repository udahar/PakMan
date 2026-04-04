#!/usr/bin/env rust
//! Note Taker - Quick note taking

use anyhow::Result;
use clap::Parser;
use chrono::Local;
use std::fs::{self, OpenOptions};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Note text (or - for stdin)
    #[arg(required = true)]
    text: String,

    /// Notes directory
    #[arg(short, long, default_value = "./notes")]
    dir: String,

    /// Append to existing note
    #[arg(short, long)]
    append: bool,

    /// Tag for the note
    #[arg(short, long)]
    tag: Option<String>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let mut notes_dir = PathBuf::from(&args.dir);
    fs::create_dir_all(&notes_dir)?;

    // Add tag subdirectory if specified
    if let Some(tag) = &args.tag {
        notes_dir.push(tag);
        fs::create_dir_all(&notes_dir)?;
    }

    // Generate filename with timestamp
    let timestamp = Local::now().format("%Y%m%d_%H%M%S");
    let filename = format!("note_{}.txt", timestamp);
    let filepath = notes_dir.join(&filename);

    // Get note content
    let content = if args.text == "-" {
        let mut buffer = String::new();
        std::io::stdin().read_line(&mut buffer)?;
        buffer
    } else {
        args.text
    };

    // Write note
    if args.append {
        // Find most recent note and append
        if let Ok(mut entries) = fs::read_dir(&notes_dir) {
            let mut files: Vec<_> = entries
                .filter_map(|e| e.ok())
                .filter(|e| e.path().extension().map(|ext| ext == "txt").unwrap_or(false))
                .collect();
            files.sort_by_key(|e| e.path());
            
            if let Some(last) = files.last() {
                OpenOptions::new()
                    .append(true)
                    .open(&last.path())?
                    .write_all(format!("\n\n---\n{}", content).as_bytes())?;
                println!("Appended to: {}", last.path().display());
                return Ok(());
            }
        }
    }

    // Write new note
    let full_content = format!(
        "Date: {}\nTag: {}\n\n{}\n",
        Local::now().format("%Y-%m-%d %H:%M:%S"),
        args.tag.as_deref().unwrap_or("none"),
        content
    );

    fs::write(&filepath, &full_content)?;
    println!("Note saved: {}", filepath.display());

    Ok(())
}
