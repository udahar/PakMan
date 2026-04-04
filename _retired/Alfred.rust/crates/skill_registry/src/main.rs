#!/usr/bin/env rust
//! Skill Registry CLI - Manage skills and tool genome

use anyhow::Result;
use chrono::Local;
use clap::{Parser, Subcommand};
use skill_registry::{Skill, SkillRegistry, ToolGenome, Pipeline, PipelineStep};
use std::path::PathBuf;

#[derive(Parser)]
#[command(author, version, about = "Skill Registry and Tool Genome Manager")]
struct Args {
    /// Database path
    #[arg(short, long, default_value = "skills.db")]
    db: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Register a new skill
    Register {
        /// Skill JSON file
        #[arg(required = true)]
        file: PathBuf,
    },
    /// Search skills
    Search {
        /// Search query
        #[arg(required = true)]
        query: String,
    },
    /// List all skills
    List,
    /// Get skill details
    Get {
        /// Skill ID
        #[arg(required = true)]
        id: String,
    },
    /// Run a skill
    Run {
        /// Skill ID
        #[arg(required = true)]
        id: String,
        /// Input data
        #[arg(required = true)]
        input: String,
    },
    /// Register a tool in the genome
    RegisterTool {
        /// Tool JSON file
        #[arg(required = true)]
        file: PathBuf,
    },
    /// Get tool genome info
    Genome {
        /// Tool ID
        #[arg(required = true)]
        tool_id: String,
    },
    /// List tools by capability
    Capabilities {
        /// Capability name
        #[arg(required = true)]
        capability: String,
    },
    /// Show tool lineage
    Lineage {
        /// Tool ID
        #[arg(required = true)]
        tool_id: String,
    },
    /// Record tool execution
    Record {
        /// Tool ID
        #[arg(required = true)]
        tool_id: String,
        /// Success (true/false)
        #[arg(required = true)]
        success: bool,
        /// Runtime in ms
        #[arg(short, long)]
        runtime: f64,
    },
    /// Deprecate a tool
    Deprecate {
        /// Tool ID
        #[arg(required = true)]
        tool_id: String,
    },
    /// Export all skills
    Export {
        /// Output file
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
}

fn main() -> Result<()> {
    let args = Args::parse();

    let registry = SkillRegistry::open(&args.db)?;

    match args.command {
        Commands::Register { file } => {
            let content = std::fs::read_to_string(&file)?;
            let skill: Skill = serde_json::from_str(&content)?;
            registry.register_skill(skill)?;
            println!("✓ Skill registered");
        }

        Commands::Search { query } => {
            let skills = registry.search_skills(&query)?;
            if skills.is_empty() {
                println!("No skills found for: {}", query);
            } else {
                println!("Found {} skills:\n", skills.len());
                for skill in skills {
                    println!("  {} - {}", skill.id, skill.description);
                    println!("    Tags: {}", skill.tags.join(", "));
                    println!("    Usage: {} (success: {}, fail: {})", 
                        skill.usage_count, skill.success_count, skill.failure_count);
                    println!();
                }
            }
        }

        Commands::List => {
            let skills = registry.list_skills()?;
            println!("Registered Skills ({}):\n", skills.len());
            for skill in skills {
                println!("  {:<30} {}", skill.id, skill.description);
            }
        }

        Commands::Get { id } => {
            if let Some(skill) = registry.get_skill(&id)? {
                println!("{}", serde_json::to_string_pretty(&skill)?);
            } else {
                println!("Skill not found: {}", id);
            }
        }

        Commands::Run { id, input } => {
            if let Some(skill) = registry.get_skill(&id)? {
                println!("Running skill: {}", skill.name);
                println!("Pipeline: {} steps", skill.pipeline.steps.len());
                
                // In a real implementation, this would execute the pipeline
                // For now, just show what would run
                for (i, step) in skill.pipeline.steps.iter().enumerate() {
                    println!("  Step {}: {} {:?}", i + 1, step.tool, step.args);
                }
                
                // Record usage
                registry.record_usage(&id, true, 0.0)?;
            } else {
                println!("Skill not found: {}", id);
            }
        }

        Commands::RegisterTool { file } => {
            let content = std::fs::read_to_string(&file)?;
            let genome: ToolGenome = serde_json::from_str(&content)?;
            registry.register_tool(genome)?;
            println!("✓ Tool registered in genome");
        }

        Commands::Genome { tool_id } => {
            if let Some(genome) = registry.get_tool_genome(&tool_id)? {
                println!("{}", serde_json::to_string_pretty(&genome)?);
            } else {
                println!("Tool not found in genome: {}", tool_id);
            }
        }

        Commands::Capabilities { capability } => {
            let tools = registry.get_tools_by_capability(&capability)?;
            println!("Tools with capability '{}' ({}):\n", capability, tools.len());
            for tool in tools {
                let fitness = tool.fitness_score * 100.0;
                println!("  {} (v{}) - Fitness: {:.1}%, Usage: {}", 
                    tool.tool_id, tool.version, fitness, tool.usage_count);
            }
        }

        Commands::Lineage { tool_id } => {
            let lineage = registry.get_lineage(&tool_id)?;
            println!("Lineage for {}:", tool_id);
            for ancestor in &lineage {
                println!("  ← {}", ancestor);
            }
            if lineage.is_empty() {
                println!("  (no ancestors or descendants)");
            }
        }

        Commands::Record { tool_id, success, runtime } => {
            registry.update_tool_fitness(&tool_id, success, runtime)?;
            println!("✓ Recorded {} for {}", 
                if success { "success" } else { "failure" }, tool_id);
        }

        Commands::Deprecate { tool_id } => {
            registry.deprecate_tool(&tool_id)?;
            println!("✓ Tool deprecated: {}", tool_id);
        }

        Commands::Export { output } => {
            let skills = registry.list_skills()?;
            let json = serde_json::to_string_pretty(&skills)?;
            
            if let Some(path) = output {
                std::fs::write(&path, json)?;
                println!("✓ Exported {} skills to {}", skills.len(), path.display());
            } else {
                println!("{}", json);
            }
        }
    }

    Ok(())
}
