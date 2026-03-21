#!/usr/bin/env rust
//! Clipboard - Read/write clipboard

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Text to copy (or read from stdin if -)
    #[arg(short, long)]
    copy: Option<String>,

    /// Read clipboard content
    #[arg(short, long)]
    paste: bool,

    /// Clear clipboard
    #[arg(short, long)]
    clear: bool,
}

fn get_clipboard() -> Result<String> {
    let output = Command::new("powershell")
        .args(["-NoProfile", "-Command", "Get-Clipboard"])
        .output()?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

fn set_clipboard(text: &str) -> Result<()> {
    Command::new("powershell")
        .args(["-NoProfile", "-Command", "Set-Clipboard"])
        .stdin(std::process::Stdio::piped())
        .spawn()?
        .stdin
        .ok_or_else(|| anyhow::anyhow!("Failed to open stdin"))?
        .write_all(text.as_bytes())?;
    Ok(())
}

fn clear_clipboard() -> Result<()> {
    Command::new("powershell")
        .args(["-NoProfile", "-Command", "Set-Clipboard -Value $null"])
        .output()?;
    Ok(())
}

fn main() -> Result<()> {
    let args = Args::parse();

    if args.clear {
        clear_clipboard()?;
        println!("Clipboard cleared.");
        return Ok(());
    }

    if args.paste {
        let content = get_clipboard()?;
        print!("{}", content);
        return Ok(());
    }

    if let Some(text) = args.copy {
        let text = if text == "-" {
            let mut buffer = String::new();
            std::io::stdin().read_line(&mut buffer)?;
            buffer
        } else {
            text
        };
        set_clipboard(&text)?;
        println!("Copied to clipboard ({} characters).", text.len());
        return Ok(());
    }

    // Default: paste
    let content = get_clipboard()?;
    print!("{}", content);

    Ok(())
}
