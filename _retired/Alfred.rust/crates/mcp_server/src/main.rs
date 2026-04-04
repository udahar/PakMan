#!/usr/bin/env rust
//! MCP Server - Model Context Protocol server for Rust utilities
//!
//! This server allows AI agents to discover and call Rust utilities
//! via a standardized JSON-RPC-like protocol.
//!
//! Usage:
//!   mcp_server
//!
//! Protocol:
//!   - Server advertises tools on startup (JSON array)
//!   - Client sends requests: {"tool": "name", "args": [...]}
//!   - Server responds: {"success": true/false, "output": "..."}

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::io::{self, BufRead, Write};
use std::process::{Command, Stdio};

#[derive(Serialize, Clone)]
struct Tool {
    name: String,
    description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    input_schema: Option<serde_json::Value>,
}

#[derive(Deserialize)]
struct Request {
    tool: String,
    #[serde(default)]
    args: Vec<String>,
    #[serde(default)]
    id: Option<String>,
}

#[derive(Serialize)]
struct Response {
    id: Option<String>,
    success: bool,
    output: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Serialize)]
struct ToolList {
    r#type: String,
    tools: Vec<Tool>,
}

fn get_tool_manifest() -> Vec<Tool> {
    vec![
        Tool {
            name: "fs_scan".into(),
            description: "Scan filesystem and output JSON structure. Use --json for machine-readable output.".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to scan"},
                    "--json": {"type": "boolean", "description": "Output as JSON"},
                    "--max-depth": {"type": "integer", "description": "Max directory depth"},
                    "--hidden": {"type": "boolean", "description": "Include hidden files"}
                }
            })),
        },
        Tool {
            name: "json_fmt".into(),
            description: "Format or minify JSON files".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input file path"},
                    "--minify": {"type": "boolean", "description": "Remove whitespace"},
                    "--output": {"type": "string", "description": "Output file path"}
                }
            })),
        },
        Tool {
            name: "proc_list".into(),
            description: "List running processes".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "--json": {"type": "boolean", "description": "Output as JSON"},
                    "--limit": {"type": "integer", "description": "Limit results"}
                }
            })),
        },
        Tool {
            name: "file_hash".into(),
            description: "Generate MD5/SHA256 hashes for files".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "files": {"type": "array", "items": {"type": "string"}},
                    "--algorithm": {"type": "string", "enum": ["md5", "sha256", "both"]}
                }
            })),
        },
        Tool {
            name: "file_watch".into(),
            description: "Watch files/directories for changes".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to watch"},
                    "--recursive": {"type": "boolean", "description": "Watch recursively"},
                    "--command": {"type": "string", "description": "Command to run on change"}
                }
            })),
        },
        Tool {
            name: "queue_processor".into(),
            description: "Process JSON queue every N seconds".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "queue_file": {"type": "string", "description": "Queue JSON file"},
                    "--interval": {"type": "integer", "description": "Seconds between runs"}
                }
            })),
        },
        Tool {
            name: "repo_index".into(),
            description: "Index repository files for AI embeddings. Returns file paths, hashes, sizes, languages.".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to index"},
                    "--json": {"type": "boolean", "description": "Output as JSON"},
                    "--hash": {"type": "boolean", "description": "Calculate file hashes"}
                }
            })),
        },
        Tool {
            name: "git_status".into(),
            description: "Git repository status checker".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Repository path"},
                    "--json": {"type": "boolean", "description": "Output as JSON"}
                }
            })),
        },
        Tool {
            name: "prompt_fmt".into(),
            description: "Format prompts for LLM APIs (Ollama, OpenAI)".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Prompt file"},
                    "--system": {"type": "string", "description": "System prompt file"},
                    "--format": {"type": "string", "enum": ["json", "ollama", "openai"]}
                }
            })),
        },
        Tool {
            name: "password_check".into(),
            description: "Check password strength".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "password": {"type": "string", "description": "Password to check"}
                }
            })),
        },
        Tool {
            name: "http_get".into(),
            description: "Simple HTTP GET client".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                }
            })),
        },
        Tool {
            name: "dns_lookup".into(),
            description: "DNS lookup utility".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain to lookup"}
                }
            })),
        },
        Tool {
            name: "port_check".into(),
            description: "Check if ports are open/in use".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "ports": {"type": "array", "items": {"type": "integer"}},
                    "--host": {"type": "string", "description": "Host to check"}
                }
            })),
        },
        Tool {
            name: "uuid_gen".into(),
            description: "Generate UUIDs".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "--count": {"type": "integer", "description": "Number of UUIDs"}
                }
            })),
        },
        Tool {
            name: "clipboard".into(),
            description: "Clipboard operations (read/write)".into(),
            input_schema: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "--copy": {"type": "string", "description": "Text to copy"},
                    "--paste": {"type": "boolean", "description": "Read clipboard"},
                    "--clear": {"type": "boolean", "description": "Clear clipboard"}
                }
            })),
        },
    ]
}

fn run_tool(tool: &str, args: &[String]) -> Result<(bool, String, Option<String>)> {
    let output = Command::new(tool)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let success = output.status.success();

    Ok((success, stdout, if success { None } else { Some(stderr) }))
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    let stdin = io::stdin();
    let mut stdout = io::stdout();

    // Advertise tools
    let tool_list = ToolList {
        r#type: "tool_list".into(),
        tools: get_tool_manifest(),
    };

    let manifest = serde_json::to_string(&tool_list)?;
    writeln!(stdout, "{}", manifest)?;
    stdout.flush()?;

    tracing::info!("MCP server started, advertising {} tools", tool_list.tools.len());

    // Process requests
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(e) => {
                tracing::error!("Failed to read line: {}", e);
                continue;
            }
        };

        let req: Request = match serde_json::from_str(&line) {
            Ok(r) => r,
            Err(e) => {
                let resp = Response {
                    id: None,
                    success: false,
                    output: String::new(),
                    error: Some(format!("Invalid request: {}", e)),
                };
                writeln!(stdout, "{}", serde_json::to_string(&resp)?)?;
                stdout.flush()?;
                continue;
            }
        };

        tracing::info!("Request: tool={} args={:?}", req.tool, req.args);

        // Run the tool
        let result = run_tool(&req.tool, &req.args);

        let resp = match result {
            Ok((success, output, error)) => Response {
                id: req.id,
                success,
                output,
                error,
            },
            Err(e) => Response {
                id: req.id,
                success: false,
                output: String::new(),
                error: Some(e.to_string()),
            },
        };

        let json = serde_json::to_string(&resp)?;
        writeln!(stdout, "{}", json)?;
        stdout.flush()?;

        tracing::info!("Response: success={}", resp.success);
    }

    Ok(())
}
