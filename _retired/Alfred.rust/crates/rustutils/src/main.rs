#!/usr/bin/env rust
//! RustUtils - Main entry point for all Rust utilities
//!
//! Usage:
//!   rustutils fs_scan ./path --json
//!   rustutils json_fmt file.json
//!   rustutils proc_list
//!   rustutils manifest

use anyhow::Result;
use clap::{Parser, Subcommand};
use common::print_json;
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Parser, Debug)]
#[command(
    author,
    version,
    about = "Rust Utilities - A collection of command-line tools",
    long_about = None
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Scan filesystem
    FsScan {
        #[arg(default_value = ".")]
        path: String,
        #[arg(short, long)]
        json: bool,
        #[arg(short, long, default_value = "0")]
        max_depth: usize,
        #[arg(short, long)]
        hidden: bool,
    },
    /// Format JSON
    JsonFmt {
        #[arg(required = true)]
        input: String,
        #[arg(short, long)]
        output: Option<String>,
        #[arg(short, long)]
        minify: bool,
    },
    /// List processes
    ProcList {
        #[arg(short, long)]
        json: bool,
        #[arg(short, long)]
        limit: Option<usize>,
    },
    /// Check ports
    PortCheck {
        #[arg(required = true)]
        ports: Vec<u16>,
        #[arg(short, long, default_value = "127.0.0.1")]
        host: String,
    },
    /// Generate hashes
    FileHash {
        #[arg(required = true)]
        files: Vec<String>,
        #[arg(short, long, default_value = "both")]
        algorithm: String,
    },
    /// Watch files
    FileWatch {
        #[arg(required = true)]
        path: String,
        #[arg(short, long)]
        recursive: bool,
        #[arg(short, long)]
        command: Option<String>,
    },
    /// Process JSON queue
    QueueProcessor {
        #[arg(required = true)]
        queue_file: String,
        #[arg(short, long, default_value = "5")]
        interval: u64,
    },
    /// Generate UUIDs
    UuidGen {
        #[arg(short, long, default_value = "1")]
        count: usize,
        #[arg(short, long)]
        json: bool,
    },
    /// Generate hashes from text
    HashGen {
        #[arg(required = true)]
        input: String,
        #[arg(short, long, default_value = "all")]
        algorithm: String,
    },
    /// Unix timestamp converter
    Epoch {
        #[arg(default_value = "now")]
        timestamp: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Sleep for duration
    Sleep {
        #[arg(required = true)]
        duration: String,
    },
    /// Random data generator
    RandomGen {
        #[arg(short, long, default_value = "string")]
        r#type: String,
        #[arg(short, long, default_value = "16")]
        length: usize,
        #[arg(short, long)]
        count: usize,
    },
    /// View CSV files
    CsvView {
        #[arg(required = true)]
        file: String,
        #[arg(short, long)]
        json: bool,
        #[arg(short, long, default_value = "0")]
        max_rows: usize,
    },
    /// Parse log files
    LogParse {
        #[arg(required = true)]
        file: String,
        #[arg(short, long)]
        stats: bool,
        #[arg(short, long)]
        level: Option<String>,
    },
    /// Format prompts for LLM
    PromptFmt {
        #[arg(required = true)]
        input: String,
        #[arg(short, long)]
        system: Option<String>,
        #[arg(short, long, default_value = "json")]
        format: String,
    },
    /// Parse LLM responses
    ResponseParse {
        #[arg(required = true)]
        input: String,
        #[arg(short, long, default_value = "json")]
        format: String,
        #[arg(short, long)]
        extract: bool,
    },
    /// List Ollama models
    ModelList {
        #[arg(short, long)]
        json: bool,
    },
    /// Git status
    GitStatus {
        #[arg(default_value = ".")]
        path: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Compare environments
    EnvCompare {
        #[arg(required = true)]
        file1: String,
        #[arg(required = true)]
        file2: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Compare JSON files
    DiffJson {
        #[arg(required = true)]
        file1: String,
        #[arg(required = true)]
        file2: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Password strength checker
    PasswordCheck {
        #[arg(required = true)]
        password: String,
        #[arg(short, long)]
        json: bool,
    },
    /// HTTP GET client
    HttpGet {
        #[arg(required = true)]
        url: String,
        #[arg(short, long)]
        json: bool,
        #[arg(short, long)]
        headers: bool,
    },
    /// DNS lookup
    DnsLookup {
        #[arg(required = true)]
        domain: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Disk information
    DiskInfo {
        #[arg(default_value = "C:")]
        drive: String,
        #[arg(short, long)]
        json: bool,
    },
    /// Clipboard operations
    Clipboard {
        #[arg(short, long)]
        copy: Option<String>,
        #[arg(short, long)]
        paste: bool,
        #[arg(short, long)]
        clear: bool,
    },
    /// Index repository files
    RepoIndex {
        #[arg(default_value = ".")]
        path: String,
        #[arg(short, long)]
        json: bool,
        #[arg(short, long)]
        hash: bool,
    },
    /// Generate tool schema
    Schema {
        /// Tool name (or "all" for manifest)
        #[arg(default_value = "all")]
        tool: String,
    },
    /// Execute a pipeline of tools
    Pipe {
        /// Pipeline definition (JSON or path to file)
        #[arg(required = true)]
        definition: String,
        /// Input file (stdin if not provided)
        #[arg(short, long)]
        input: Option<String>,
        /// Output file (stdout if not provided)
        #[arg(short, long)]
        output: Option<String>,
    },
    /// Generate tool manifest (alias for schema all)
    Manifest,
    /// List all available tools
    List,
    /// Skill management
    Skill {
        #[command(subcommand)]
        command: SkillCommands,
    },
    /// Memory operations
    Memory {
        #[command(subcommand)]
        command: MemoryCommands,
    },
}

#[derive(Subcommand)]
enum SkillCommands {
    /// Register a skill
    Register { file: String },
    /// Search skills
    Search { query: String },
    /// List skills
    List,
    /// Run a skill
    Run { id: String, input: String },
}

#[derive(Subcommand)]
enum MemoryCommands {
    /// Store a value
    Store { key: String, value: String },
    /// Recall a value
    Recall { key: String },
    /// Search memory
    Search { query: String },
}

#[derive(Serialize)]
struct ToolInfo {
    name: String,
    description: String,
}

fn get_tool_manifest() -> Vec<ToolInfo> {
    vec![
        ToolInfo { name: "fs_scan".into(), description: "Scan filesystem and output JSON structure".into() },
        ToolInfo { name: "json_fmt".into(), description: "Format or minify JSON files".into() },
        ToolInfo { name: "proc_list".into(), description: "List running processes".into() },
        ToolInfo { name: "port_check".into(), description: "Check if ports are open/in use".into() },
        ToolInfo { name: "file_hash".into(), description: "Generate MD5/SHA256 hashes for files".into() },
        ToolInfo { name: "file_watch".into(), description: "Watch files/directories for changes".into() },
        ToolInfo { name: "queue_processor".into(), description: "Process JSON queue every N seconds".into() },
        ToolInfo { name: "uuid_gen".into(), description: "Generate UUIDs".into() },
        ToolInfo { name: "hash_gen".into(), description: "Generate hashes from text".into() },
        ToolInfo { name: "epoch".into(), description: "Unix timestamp converter".into() },
        ToolInfo { name: "sleep".into(), description: "Cross-platform sleep command".into() },
        ToolInfo { name: "random_gen".into(), description: "Generate random data".into() },
        ToolInfo { name: "csv_view".into(), description: "View CSV files as formatted tables".into() },
        ToolInfo { name: "log_parse".into(), description: "Parse and analyze log files".into() },
        ToolInfo { name: "prompt_fmt".into(), description: "Format prompts for LLM APIs".into() },
        ToolInfo { name: "response_parse".into(), description: "Parse structured data from LLM responses".into() },
        ToolInfo { name: "model_list".into(), description: "List available Ollama models".into() },
        ToolInfo { name: "git_status".into(), description: "Git repository status checker".into() },
        ToolInfo { name: "env_compare".into(), description: "Compare two .env files".into() },
        ToolInfo { name: "diff_json".into(), description: "Compare two JSON files".into() },
        ToolInfo { name: "password_check".into(), description: "Check password strength".into() },
        ToolInfo { name: "http_get".into(), description: "Simple HTTP GET client".into() },
        ToolInfo { name: "dns_lookup".into(), description: "DNS lookup utility".into() },
        ToolInfo { name: "disk_info".into(), description: "Display disk information".into() },
        ToolInfo { name: "clipboard".into(), description: "Clipboard operations".into() },
        ToolInfo { name: "repo_index".into(), description: "Index repository files for AI embeddings".into() },
    ]
}

fn run_external_tool(tool: &str, args: &[String]) -> Result<i32> {
    let status = Command::new(tool)
        .args(args)
        .status()?;
    Ok(status.code().unwrap_or(1))
}

#[derive(Serialize, Deserialize, Debug)]
struct PipelineStep {
    tool: String,
    #[serde(default)]
    args: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Pipeline {
    steps: Vec<PipelineStep>,
}

fn run_pipeline(definition: &str, input: Option<&str>, output: Option<&str>) -> Result<()> {
    // Try to load definition from file first
    let pipeline: Pipeline = if std::path::Path::new(definition).exists() {
        let content = std::fs::read_to_string(definition)?;
        serde_json::from_str(&content)?
    } else {
        // Try to parse as JSON directly
        serde_json::from_str(definition)?
    };

    eprintln!("Executing pipeline with {} steps...", pipeline.steps.len());

    let mut current_input: Option<String> = input.map(|s| s.to_string());

    for (i, step) in pipeline.steps.iter().enumerate() {
        eprintln!("Step {}/{}: {}", i + 1, pipeline.steps.len(), step.tool);

        let mut args = step.args.clone();
        
        // Add --jsonl for streaming if not last step
        if i < pipeline.steps.len() - 1 && !args.iter().any(|a| a.starts_with("--json")) {
            args.push("--json".to_string());
        }

        // Run the tool
        let child = Command::new(&step.tool)
            .args(&args)
            .stdin(if current_input.is_some() { std::process::Stdio::piped() } else { std::process::Stdio::inherit() })
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::inherit())
            .spawn()?;

        // Write input if provided
        if let Some(ref input_data) = current_input {
            use std::io::Write;
            child.stdin.unwrap().write_all(input_data.as_bytes())?;
        }

        let output_result = child.wait_with_output()?;
        
        if !output_result.status.success() {
            eprintln!("Step {} failed: {}", step.tool, String::from_utf8_lossy(&output_result.stderr));
            std::process::exit(1);
        }

        current_input = Some(String::from_utf8_lossy(&output_result.stdout).to_string());
    }

    // Write final output
    if let Some(out_file) = output {
        std::fs::write(out_file, current_input.unwrap_or_default())?;
        eprintln!("Output written to: {}", out_file);
    } else {
        print!("{}", current_input.unwrap_or_default());
    }

    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Manifest => {
            let manifest = get_tool_manifest();
            print_json(&manifest)?;
        }
        Commands::List => {
            println!("Available Rust Utilities:");
            println!("========================\n");
            for tool in get_tool_manifest() {
                println!("  {:<20} {}", tool.name, tool.description);
            }
        }
        Commands::FsScan { path, json, max_depth, hidden } => {
            let mut args = vec![path.clone()];
            if json { args.push("--json".to_string()); }
            if max_depth > 0 { args.push(format!("--max-depth={}", max_depth)); }
            if hidden { args.push("--hidden".to_string()); }
            run_external_tool("fs_scan", &args)?;
        }
        Commands::JsonFmt { input, output, minify } => {
            let mut args = vec![input.clone()];
            if let Some(out) = output { args.push(format!("--output={}", out)); }
            if minify { args.push("--minify".to_string()); }
            run_external_tool("json_fmt", &args)?;
        }
        Commands::ProcList { json, limit } => {
            let mut args = vec![];
            if json { args.push("--json".to_string()); }
            if let Some(lim) = limit { args.push(format!("--limit={}", lim)); }
            run_external_tool("proc_list", &args)?;
        }
        Commands::PortCheck { ports, host } => {
            let mut args: Vec<String> = ports.iter().map(|p| p.to_string()).collect();
            args.push(format!("--host={}", host));
            run_external_tool("port_check", &args)?;
        }
        Commands::FileHash { files, algorithm } => {
            let mut args = files.clone();
            args.push(format!("--algorithm={}", algorithm));
            run_external_tool("file_hash", &args)?;
        }
        Commands::FileWatch { path, recursive, command } => {
            let mut args = vec![path.clone()];
            if recursive { args.push("--recursive".to_string()); }
            if let Some(cmd) = command { args.push(format!("--command={}", cmd)); }
            run_external_tool("file_watch", &args)?;
        }
        Commands::QueueProcessor { queue_file, interval } => {
            let mut args = vec![queue_file.clone()];
            args.push(format!("--interval={}", interval));
            run_external_tool("queue_processor", &args)?;
        }
        Commands::UuidGen { count, json } => {
            let mut args = vec![];
            args.push(format!("--count={}", count));
            if json { args.push("--json".to_string()); }
            run_external_tool("uuid_gen", &args)?;
        }
        Commands::HashGen { input, algorithm } => {
            let mut args = vec![input.clone()];
            args.push(format!("--algorithm={}", algorithm));
            run_external_tool("hash_gen", &args)?;
        }
        Commands::Epoch { timestamp, json } => {
            let mut args = vec![timestamp.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("epoch", &args)?;
        }
        Commands::Sleep { duration } => {
            run_external_tool("sleep", &[duration])?;
        }
        Commands::RandomGen { r#type, length, count } => {
            let mut args = vec![];
            args.push(format!("--type={}", r#type));
            args.push(format!("--length={}", length));
            args.push(format!("--count={}", count));
            run_external_tool("random_gen", &args)?;
        }
        Commands::CsvView { file, json, max_rows } => {
            let mut args = vec![file.clone()];
            if json { args.push("--json".to_string()); }
            if max_rows > 0 { args.push(format!("--max-rows={}", max_rows)); }
            run_external_tool("csv_view", &args)?;
        }
        Commands::LogParse { file, stats, level } => {
            let mut args = vec![file.clone()];
            if stats { args.push("--stats".to_string()); }
            if let Some(lvl) = level { args.push(format!("--level={}", lvl)); }
            run_external_tool("log_parse", &args)?;
        }
        Commands::PromptFmt { input, system, format } => {
            let mut args = vec![input.clone()];
            if let Some(sys) = system { args.push(format!("--system={}", sys)); }
            args.push(format!("--format={}", format));
            run_external_tool("prompt_fmt", &args)?;
        }
        Commands::ResponseParse { input, format, extract } => {
            let mut args = vec![input.clone()];
            args.push(format!("--format={}", format));
            if extract { args.push("--extract".to_string()); }
            run_external_tool("response_parse", &args)?;
        }
        Commands::ModelList { json } => {
            let mut args = vec![];
            if json { args.push("--json".to_string()); }
            run_external_tool("model_list", &args)?;
        }
        Commands::GitStatus { path, json } => {
            let mut args = vec![path.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("git_status", &args)?;
        }
        Commands::EnvCompare { file1, file2, json } => {
            let mut args = vec![file1.clone(), file2.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("env_compare", &args)?;
        }
        Commands::DiffJson { file1, file2, json } => {
            let mut args = vec![file1.clone(), file2.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("diff_json", &args)?;
        }
        Commands::PasswordCheck { password, json } => {
            let mut args = vec![password.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("password_check", &args)?;
        }
        Commands::HttpGet { url, json, headers } => {
            let mut args = vec![url.clone()];
            if json { args.push("--json".to_string()); }
            if headers { args.push("--headers".to_string()); }
            run_external_tool("http_get", &args)?;
        }
        Commands::DnsLookup { domain, json } => {
            let mut args = vec![domain.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("dns_lookup", &args)?;
        }
        Commands::DiskInfo { drive, json } => {
            let mut args = vec![drive.clone()];
            if json { args.push("--json".to_string()); }
            run_external_tool("disk_info", &args)?;
        }
        Commands::Clipboard { copy, paste, clear } => {
            let mut args = vec![];
            if let Some(text) = copy { args.push(format!("--copy={}", text)); }
            if paste { args.push("--paste".to_string()); }
            if clear { args.push("--clear".to_string()); }
            run_external_tool("clipboard", &args)?;
        }
        Commands::RepoIndex { path, json, hash } => {
            let mut args = vec![path.clone()];
            if json { args.push("--json".to_string()); }
            if hash { args.push("--hash".to_string()); }
            run_external_tool("repo_index", &args)?;
        }
        Commands::Schema { tool } => {
            if tool == "all" {
                schema_gen::print_manifest()?;
            } else {
                schema_gen::print_schema(&tool, "Tool schema")?;
            }
        }
        Commands::Manifest => {
            schema_gen::print_manifest()?;
        }
        Commands::Pipe { definition, input, output } => {
            run_pipeline(&definition, input.as_deref(), output.as_deref())?;
        }
        Commands::List => {
            println!("Available Rust Utilities:");
            println!("========================\n");
            for tool in schema_gen::generate_manifest().tools {
                println!("  {:<20} {}", tool.name, tool.description);
            }
        }
        Commands::Skill { command } => {
            use skill_registry::SkillRegistry;
            let registry = SkillRegistry::open(&std::path::PathBuf::from("skills.db"))?;
            
            match command {
                SkillCommands::Register { file } => {
                    let content = std::fs::read_to_string(&file)?;
                    let skill: skill_registry::Skill = serde_json::from_str(&content)?;
                    registry.register_skill(skill)?;
                    println!("✓ Skill registered");
                }
                SkillCommands::Search { query } => {
                    let skills = registry.search_skills(&query)?;
                    for skill in skills {
                        println!("{} - {}", skill.id, skill.description);
                    }
                }
                SkillCommands::List => {
                    let skills = registry.list_skills()?;
                    for skill in skills {
                        println!("{} - {}", skill.id, skill.description);
                    }
                }
                SkillCommands::Run { id, input: _ } => {
                    if let Some(skill) = registry.get_skill(&id)? {
                        println!("Running skill: {}", skill.name);
                        println!("Pipeline: {} steps", skill.pipeline.steps.len());
                    }
                }
            }
        }
        Commands::Memory { command } => {
            use memory_client::{MemoryClient, Memory};
            let client = MemoryClient::new(None, None);
            
            match command {
                MemoryCommands::Store { key, value } => {
                    let val: serde_json::Value = serde_json::from_str(&value)?;
                    client.store(&key, val)?;
                    println!("✓ Stored: {}", key);
                }
                MemoryCommands::Recall { key } => {
                    if let Some(val) = client.recall(&key)? {
                        println!("{}", serde_json::to_string_pretty(&val)?);
                    } else {
                        println!("Not found: {}", key);
                    }
                }
                MemoryCommands::Search { query } => {
                    let results = client.search(&query)?;
                    for entry in results {
                        println!("{}: {}", entry.key, serde_json::to_string(&entry.value)?);
                    }
                }
            }
        }
    }

    Ok(())
}
