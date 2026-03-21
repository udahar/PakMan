#!/usr/bin/env rust
//! Schema Generator CLI - Generate and display tool schemas

use anyhow::Result;
use clap::Parser;
use schema_gen::{print_manifest, print_schema};

#[derive(Parser)]
#[command(author, version, about = "Generate JSON schemas for Rust utilities")]
struct Args {
    /// Tool name to get schema for (or "all" for manifest)
    #[arg(default_value = "all")]
    tool: String,
}

fn main() -> Result<()> {
    let args = Args::parse();

    if args.tool == "all" {
        print_manifest()?;
    } else {
        // Get description from known tools
        let description = match args.tool.as_str() {
            "fs_scan" => "Scan filesystem and output JSON structure",
            "repo_index" => "Index repository files for AI embeddings",
            "json_fmt" => "Format or minify JSON files",
            "proc_list" => "List running processes",
            "port_check" => "Check if ports are open/in use",
            "file_hash" => "Generate MD5/SHA256 hashes for files",
            "file_watch" => "Watch files/directories for changes",
            "queue_processor" => "Process JSON queue every N seconds",
            "prompt_fmt" => "Format prompts for LLM APIs",
            "git_status" => "Git repository status checker",
            "password_check" => "Check password strength",
            "http_get" => "Simple HTTP GET client",
            "dns_lookup" => "DNS lookup utility",
            "clipboard" => "Clipboard operations",
            "uuid_gen" => "Generate UUIDs",
            "disk_info" => "Display disk information",
            _ => "Custom utility",
        };
        print_schema(&args.tool, description)?;
    }

    Ok(())
}
