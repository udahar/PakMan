#!/usr/bin/env rust
//! Git Status - Quick git repository status

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Repository path
    #[arg(default_value = ".")]
    path: String,

    /// Output as JSON
    #[arg(short, long)]
    json: bool,

    /// Show untracked files
    #[arg(short, long)]
    untracked: bool,
}

#[derive(serde::Serialize)]
struct GitStatus {
    path: String,
    is_repo: bool,
    branch: Option<String>,
    ahead: Option<usize>,
    behind: Option<usize>,
    changed: usize,
    staged: usize,
    untracked: usize,
    clean: bool,
}

fn run_git(args: &[&str], path: &str) -> Option<String> {
    Command::new("git")
        .args(args)
        .current_dir(path)
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Check if it's a git repo
    let is_repo = run_git(&["rev-parse", "--is-inside-work-tree"], &args.path)
        .map(|o| o.trim() == "true")
        .unwrap_or(false);

    let mut status = GitStatus {
        path: args.path.clone(),
        is_repo,
        branch: None,
        ahead: None,
        behind: None,
        changed: 0,
        staged: 0,
        untracked: 0,
        clean: true,
    };

    if is_repo {
        // Get branch
        status.branch = run_git(&["branch", "--show-current"], &args.path)
            .map(|b| b.trim().to_string());

        // Get status
        if let Some(output) = run_git(&["status", "--porcelain", "-b"], &args.path) {
            let lines: Vec<&str> = output.lines().collect();
            
            // Parse branch info from first line
            if let Some(first) = lines.first() {
                if first.starts_with("## ") {
                    let branch_info = &first[3..];
                    if branch_info.contains("...") {
                        let parts: Vec<&str> = branch_info.split("...").collect();
                        if parts.len() == 2 {
                            let remote_info = parts[1];
                            if let Some(ahead_idx) = remote_info.find("ahead ") {
                                if let Some(end) = remote_info[ahead_idx..].find(' ') {
                                    status.ahead = remote_info[ahead_idx + 6..ahead_idx + end].parse().ok();
                                }
                            }
                            if let Some(behind_idx) = remote_info.find("behind ") {
                                status.behind = remote_info[behind_idx + 7..].parse().ok();
                            }
                        }
                    }
                }
            }

            // Count changes
            for line in lines.iter().skip(1) {
                if line.starts_with("??") {
                    status.untracked += 1;
                } else if line.starts_with("M ") || line.starts_with("A ") || line.starts_with("D ") {
                    status.staged += 1;
                } else if line.starts_with(" M") || line.starts_with(" A") || line.starts_with(" D") {
                    status.changed += 1;
                }
            }

            status.clean = status.changed == 0 && status.staged == 0 && status.untracked == 0;
        }
    }

    if args.json {
        println!("{}", serde_json::to_string_pretty(&status)?);
    } else {
        if !is_repo {
            println!("Not a git repository: {}", args.path);
        } else {
            println!("Git Status: {}", args.path);
            if let Some(branch) = &status.branch {
                println!("Branch: {}", branch);
            }
            if let Some(ahead) = status.ahead {
                println!("Ahead by: {} commits", ahead);
            }
            if let Some(behind) = status.behind {
                println!("Behind by: {} commits", behind);
            }
            println!();
            println!("Changes:");
            println!("  Staged:   {}", status.staged);
            println!("  Changed:  {}", status.changed);
            println!("  Untracked: {}", status.untracked);
            println!();
            if status.clean {
                println!("✓ Working tree clean");
            } else {
                println!("✗ Working tree has changes");
            }
        }
    }

    Ok(())
}
