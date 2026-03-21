//! Schema Generator - Auto-generate JSON schemas for all tools
//!
//! Uses clap's reflection to extract parameter information.

use anyhow::Result;
use clap::CommandFactory;
use serde::Serialize;
use std::collections::HashMap;

#[derive(Serialize, Debug)]
pub struct ToolSchema {
    pub name: String,
    pub description: String,
    pub parameters: JsonSchema,
}

#[derive(Serialize, Debug)]
pub struct JsonSchema {
    #[serde(rename = "type")]
    pub schema_type: String,
    pub properties: HashMap<String, PropertySchema>,
    pub required: Vec<String>,
}

#[derive(Serialize, Debug)]
pub struct PropertySchema {
    #[serde(rename = "type")]
    pub prop_type: String,
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub examples: Option<Vec<String>>,
}

#[derive(Serialize, Debug)]
pub struct ToolManifest {
    pub version: String,
    pub tools: Vec<ToolSchema>,
}

/// Generate schema for a single tool
pub fn generate_tool_schema(name: &str, description: &str) -> ToolSchema {
    // For now, return hardcoded schemas
    // In the future, this could use procedural macros
    get_builtin_schema(name, description)
}

fn get_builtin_schema(name: &str, description: &str) -> ToolSchema {
    let mut properties = HashMap::new();
    let mut required = Vec::new();

    match name {
        "fs_scan" => {
            properties.insert("path".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Directory to scan".to_string()),
                default: Some(serde_json::json!(".")),
                examples: Some(vec!["./src".to_string(), "/home/user".to_string()]),
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("max-depth".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Max directory depth (0 = unlimited)".to_string()),
                default: Some(serde_json::json!(0)),
                examples: None,
            });
            properties.insert("hidden".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Include hidden files".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "repo_index" => {
            properties.insert("path".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Directory to index".to_string()),
                default: Some(serde_json::json!(".")),
                examples: None,
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("hash".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Calculate file hashes".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("max-depth".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Max directory depth".to_string()),
                default: Some(serde_json::json!(0)),
                examples: None,
            });
        }

        "json_fmt" => {
            properties.insert("input".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Input file path (or - for stdin)".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("output".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Output file path".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("minify".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Minify JSON output".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("validate".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Validate only, no output".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            required.push("input".to_string());
        }

        "proc_list" => {
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("filter".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Filter by process name".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("limit".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Limit number of results".to_string()),
                default: Some(serde_json::json!(0)),
                examples: None,
            });
        }

        "port_check" => {
            properties.insert("ports".to_string(), PropertySchema {
                prop_type: "array".to_string(),
                description: Some("Ports to check".to_string()),
                default: None,
                examples: Some(vec!["80".to_string(), "443".to_string(), "8080".to_string()]),
            });
            properties.insert("host".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Host to check".to_string()),
                default: Some(serde_json::json!("127.0.0.1")),
                examples: None,
            });
            properties.insert("timeout".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Timeout in seconds".to_string()),
                default: Some(serde_json::json!(1)),
                examples: None,
            });
        }

        "file_hash" => {
            properties.insert("files".to_string(), PropertySchema {
                prop_type: "array".to_string(),
                description: Some("Files to hash".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("algorithm".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Hash algorithm (md5, sha256, both)".to_string()),
                default: Some(serde_json::json!("both")),
                examples: Some(vec!["md5".to_string(), "sha256".to_string(), "both".to_string()]),
            });
            properties.insert("recursive".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Scan directories recursively".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "file_watch" => {
            properties.insert("path".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Path to watch".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("recursive".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Watch recursively".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("command".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Command to run on change".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("verbose".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Verbose output".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "queue_processor" => {
            properties.insert("queue_file".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Queue JSON file".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("interval".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Processing interval in seconds".to_string()),
                default: Some(serde_json::json!(5)),
                examples: None,
            });
            properties.insert("cleanup".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Remove processed tasks".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("max-tasks".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Max tasks per run (0 = unlimited)".to_string()),
                default: Some(serde_json::json!(0)),
                examples: None,
            });
        }

        "prompt_fmt" => {
            properties.insert("input".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Input prompt file".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("system".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("System prompt file".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("format".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Output format (json, ollama, openai, text)".to_string()),
                default: Some(serde_json::json!("json")),
                examples: Some(vec!["json".to_string(), "ollama".to_string(), "openai".to_string()]),
            });
            properties.insert("model".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Model name".to_string()),
                default: None,
                examples: Some(vec!["qwen2.5:7b".to_string(), "llama3.2".to_string()]),
            });
            properties.insert("temperature".to_string(), PropertySchema {
                prop_type: "number".to_string(),
                description: Some("Temperature (0.0-1.0)".to_string()),
                default: None,
                examples: None,
            });
        }

        "git_status" => {
            properties.insert("path".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Repository path".to_string()),
                default: Some(serde_json::json!(".")),
                examples: None,
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("untracked".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Show untracked files".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "password_check" => {
            properties.insert("password".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Password to check".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            required.push("password".to_string());
        }

        "http_get" => {
            properties.insert("url".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("URL to fetch".to_string()),
                default: None,
                examples: Some(vec!["https://api.example.com/data".to_string()]),
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("headers".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Show response headers".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("timeout".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Timeout in seconds".to_string()),
                default: Some(serde_json::json!(30)),
                examples: None,
            });
            required.push("url".to_string());
        }

        "dns_lookup" => {
            properties.insert("domain".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Domain to lookup".to_string()),
                default: None,
                examples: Some(vec!["example.com".to_string(), "google.com".to_string()]),
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            required.push("domain".to_string());
        }

        "clipboard" => {
            properties.insert("copy".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Text to copy to clipboard".to_string()),
                default: None,
                examples: None,
            });
            properties.insert("paste".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Read clipboard content".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
            properties.insert("clear".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Clear clipboard".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "uuid_gen" => {
            properties.insert("count".to_string(), PropertySchema {
                prop_type: "integer".to_string(),
                description: Some("Number of UUIDs to generate".to_string()),
                default: Some(serde_json::json!(1)),
                examples: None,
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON array".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        "disk_info" => {
            properties.insert("drive".to_string(), PropertySchema {
                prop_type: "string".to_string(),
                description: Some("Drive letter (Windows) or path (Unix)".to_string()),
                default: Some(serde_json::json!("C:")),
                examples: None,
            });
            properties.insert("json".to_string(), PropertySchema {
                prop_type: "boolean".to_string(),
                description: Some("Output as JSON".to_string()),
                default: Some(serde_json::json!(false)),
                examples: None,
            });
        }

        _ => {
            // Generic schema for unknown tools
            properties.insert("args".to_string(), PropertySchema {
                prop_type: "array".to_string(),
                description: Some("Command line arguments".to_string()),
                default: Some(serde_json::json!([])),
                examples: None,
            });
        }
    }

    ToolSchema {
        name: name.to_string(),
        description: description.to_string(),
        parameters: JsonSchema {
            schema_type: "object".to_string(),
            properties,
            required,
        },
    }
}

/// Generate complete manifest of all tools
pub fn generate_manifest() -> ToolManifest {
    ToolManifest {
        version: env!("CARGO_PKG_VERSION").to_string(),
        tools: vec![
            generate_tool_schema("fs_scan", "Scan filesystem and output JSON structure"),
            generate_tool_schema("repo_index", "Index repository files for AI embeddings"),
            generate_tool_schema("json_fmt", "Format or minify JSON files"),
            generate_tool_schema("proc_list", "List running processes"),
            generate_tool_schema("port_check", "Check if ports are open/in use"),
            generate_tool_schema("file_hash", "Generate MD5/SHA256 hashes for files"),
            generate_tool_schema("file_watch", "Watch files/directories for changes"),
            generate_tool_schema("queue_processor", "Process JSON queue every N seconds"),
            generate_tool_schema("prompt_fmt", "Format prompts for LLM APIs"),
            generate_tool_schema("git_status", "Git repository status checker"),
            generate_tool_schema("password_check", "Check password strength"),
            generate_tool_schema("http_get", "Simple HTTP GET client"),
            generate_tool_schema("dns_lookup", "DNS lookup utility"),
            generate_tool_schema("clipboard", "Clipboard operations"),
            generate_tool_schema("uuid_gen", "Generate UUIDs"),
            generate_tool_schema("disk_info", "Display disk information"),
        ],
    }
}

/// Print schema for a tool
pub fn print_schema(name: &str, description: &str) -> Result<()> {
    let schema = generate_tool_schema(name, description);
    println!("{}", serde_json::to_string_pretty(&schema)?);
    Ok(())
}

/// Print complete manifest
pub fn print_manifest() -> Result<()> {
    let manifest = generate_manifest();
    println!("{}", serde_json::to_string_pretty(&manifest)?);
    Ok(())
}
