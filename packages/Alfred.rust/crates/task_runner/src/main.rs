#!/usr/bin/env rust
//! Task Runner - Run scheduled/automated tasks

use anyhow::Result;
use clap::Parser;
use serde::Deserialize;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Task configuration file
    #[arg(required = true)]
    config: PathBuf,

    /// Task name to run (or "all")
    #[arg(default_value = "all")]
    task: String,

    /// Dry run (show what would be executed)
    #[arg(short, long)]
    dry_run: bool,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Debug, Deserialize)]
struct TaskConfig {
    name: String,
    command: String,
    #[serde(default)]
    args: Vec<String>,
    #[serde(default)]
    working_dir: Option<String>,
    #[serde(default)]
    description: String,
}

#[derive(Debug, Deserialize)]
struct Config {
    tasks: Vec<TaskConfig>,
}

fn run_task(task: &TaskConfig, dry_run: bool, verbose: bool) -> Result<i32> {
    if dry_run {
        println!("[DRY RUN] Would execute: {} {}", task.command, task.args.join(" "));
        if let Some(dir) = &task.working_dir {
            println!("          Working directory: {}", dir);
        }
        return Ok(0);
    }

    if verbose {
        println!("Running task: {}", task.name);
        println!("Command: {} {}", task.command, task.args.join(" "));
    }

    let mut cmd = Command::new(&task.command);
    cmd.args(&task.args);

    if let Some(dir) = &task.working_dir {
        cmd.current_dir(dir);
    }

    let output = cmd.output()?;

    if verbose || !output.status.success() {
        println!("stdout: {}", String::from_utf8_lossy(&output.stdout));
        eprintln!("stderr: {}", String::from_utf8_lossy(&output.stderr));
    }

    Ok(output.status.code().unwrap_or(-1))
}

fn main() -> Result<()> {
    let args = Args::parse();

    let content = fs::read_to_string(&args.config)?;
    let config: Config = serde_json::from_str(&content)?;

    let tasks_to_run: Vec<&TaskConfig> = if args.task == "all" {
        config.tasks.iter().collect()
    } else {
        config.tasks
            .iter()
            .filter(|t| t.name == args.task)
            .collect()
    };

    if tasks_to_run.is_empty() {
        eprintln!("No tasks found matching: {}", args.task);
        return Ok(());
    }

    println!("Task Runner");
    println!("Config: {}", args.config.display());
    println!("Tasks to run: {}\n", tasks_to_run.len());

    let mut success_count = 0;
    let mut fail_count = 0;

    for task in tasks_to_run {
        match run_task(task, args.dry_run, args.verbose) {
            Ok(code) if code == 0 => {
                println!("✓ {} - Success", task.name);
                success_count += 1;
            }
            Ok(code) => {
                eprintln!("✗ {} - Failed (exit code: {})", task.name, code);
                fail_count += 1;
            }
            Err(e) => {
                eprintln!("✗ {} - Error: {}", task.name, e);
                fail_count += 1;
            }
        }
    }

    println!("\nSummary: {} succeeded, {} failed", success_count, fail_count);

    Ok(())
}
