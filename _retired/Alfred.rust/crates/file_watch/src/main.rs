#!/usr/bin/env rust
//! File Watcher - Watch files/directories for changes

use anyhow::Result;
use clap::Parser;
use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to watch
    #[arg(required = true)]
    path: PathBuf,

    /// Watch recursively
    #[arg(short, long)]
    recursive: bool,

    /// Run command on change
    #[arg(short, long)]
    command: Option<String>,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Watching: {}", args.path.display());
    if args.recursive {
        println!("Mode: Recursive");
    }
    if let Some(cmd) = &args.command {
        println!("Command on change: {}", cmd);
    }
    println!("Press Ctrl+C to stop\n");

    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    ctrlc::set_handler(move || {
        r.store(false, Ordering::SeqCst);
    })?;

    let (tx, rx) = std::sync::mpsc::channel();

    let mut watcher = RecommendedWatcher::new(
        move |res: Result<Event, notify::Error>| {
            if let Ok(event) = res {
                tx.send(event).unwrap();
            }
        },
        Config::default(),
    )?;

    let mode = if args.recursive {
        RecursiveMode::Recursive
    } else {
        RecursiveMode::NonRecursive
    };

    watcher.watch(&args.path, mode)?;

    while running.load(Ordering::SeqCst) {
        if let Ok(event) = rx.recv_timeout(Duration::from_secs(1)) {
            if args.verbose {
                println!("Event: {:?}", event);
            }

            for path in &event.paths {
                let event_type = match event.kind {
                    EventKind::Create(_) => "CREATE",
                    EventKind::Modify(_) => "MODIFY",
                    EventKind::Remove(_) => "REMOVE",
                    _ => "OTHER",
                };

                println!("[{}] {}", event_type, path.display());

                if let Some(cmd) = &args.command {
                    println!("  -> Running: {}", cmd);
                    let _ = std::process::Command::new("cmd")
                        .arg("/C")
                        .arg(cmd)
                        .output();
                }
            }
        }
    }

    println!("\nStopped watching.");
    Ok(())
}
