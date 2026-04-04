#!/usr/bin/env rust
//! Queue Processor - Process JSON queue tasks every N seconds

use anyhow::Result;
use chrono::{DateTime, Local};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::time::Duration;
use tokio::time;
use tracing::{info, warn, error};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Queue JSON file
    #[arg(required = true)]
    queue_file: PathBuf,

    /// Processing interval in seconds
    #[arg(short, long, default_value = "5")]
    interval: u64,

    /// Remove processed tasks
    #[arg(short, long)]
    cleanup: bool,

    /// Max tasks per run (0 = unlimited)
    #[arg(short, long, default_value = "0")]
    max_tasks: usize,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct Task {
    id: String,
    action: String,
    #[serde(default)]
    parameters: serde_json::Value,
    #[serde(default)]
    created_at: Option<String>,
    #[serde(default)]
    status: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct Queue {
    tasks: Vec<Task>,
    #[serde(default)]
    processed: Vec<Task>,
}

impl Queue {
    fn load(path: &PathBuf) -> Result<Self> {
        let content = fs::read_to_string(path)?;
        let queue: Queue = serde_json::from_str(&content)?;
        Ok(queue)
    }

    fn save(&self, path: &PathBuf) -> Result<()> {
        let content = serde_json::to_string_pretty(self)?;
        fs::write(path, content)?;
        Ok(())
    }

    fn pending_tasks(&mut self) -> Vec<&mut Task> {
        self.tasks
            .iter_mut()
            .filter(|t| t.status != "completed" && t.status != "failed")
            .collect()
    }
}

async fn process_task(task: &Task) -> Result<String> {
    info!("Processing task: {} ({})", task.id, task.action);

    // Simulate task processing based on action type
    let result = match task.action.as_str() {
        "scan" => {
            let path = task.parameters.get("path")
                .and_then(|v| v.as_str())
                .unwrap_or(".");
            format!("Scanned: {}", path)
        }
        "notify" => {
            let message = task.parameters.get("message")
                .and_then(|v| v.as_str())
                .unwrap_or("Notification");
            format!("Notification: {}", message)
        }
        "log" => {
            let message = task.parameters.get("message")
                .and_then(|v| v.as_str())
                .unwrap_or("Log entry");
            info!("LOG: {}", message);
            "Logged".to_string()
        }
        "wait" => {
            let seconds = task.parameters.get("seconds")
                .and_then(|v| v.as_u64())
                .unwrap_or(1);
            time::sleep(Duration::from_secs(seconds)).await;
            format!("Waited {} seconds", seconds)
        }
        "echo" => {
            let text = task.parameters.get("text")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            text.to_string()
        }
        _ => {
            format!("Unknown action: {}", task.action)
        }
    };

    Ok(result)
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    let args = Args::parse();

    info!("Queue Processor starting...");
    info!("Queue file: {}", args.queue_file.display());
    info!("Interval: {} seconds", args.interval);

    let mut interval = time::interval(Duration::from_secs(args.interval));

    loop {
        interval.tick().await;

        let now: DateTime<Local> = Local::now();
        info!("\n=== Processing cycle at {} ===", now.format("%H:%M:%S"));

        match Queue::load(&args.queue_file) {
            Ok(mut queue) => {
                let pending = queue.pending_tasks();
                let task_count = pending.len();

                if task_count == 0 {
                    info!("No pending tasks");
                    continue;
                }

                info!("Found {} pending tasks", task_count);

                let mut processed_count = 0;
                let mut task_ids_to_complete = Vec::new();

                for task in pending {
                    if args.max_tasks > 0 && processed_count >= args.max_tasks {
                        info!("Reached max tasks limit ({})", args.max_tasks);
                        break;
                    }

                    match process_task(task).await {
                        Ok(result) => {
                            info!("Task {} completed: {}", task.id, result);
                            task.status = "completed".to_string();
                            task_ids_to_complete.push(task.clone());
                            processed_count += 1;
                        }
                        Err(e) => {
                            error!("Task {} failed: {}", task.id, e);
                            task.status = "failed".to_string();
                        }
                    }
                }

                // Move completed tasks to processed list if cleanup enabled
                if args.cleanup {
                    queue.processed.extend(task_ids_to_complete);
                    queue.tasks.retain(|t| t.status != "completed");
                }

                if let Err(e) = queue.save(&args.queue_file) {
                    error!("Failed to save queue: {}", e);
                }

                info!("Processed {} tasks", processed_count);
            }
            Err(e) => {
                warn!("Failed to load queue: {}", e);
            }
        }
    }
}
