#!/usr/bin/env rust
//! Observatory CLI - Live dashboard for Alfred's ecosystem
//!
//! A control tower for monitoring tool evolution, subsystem health, and system metrics.

use anyhow::Result;
use chrono::{Duration, Local};
use clap::{Parser, Subcommand};
use observatory::{Observatory, SystemOverview, SubsystemMap, LineageGraph};
use std::io::{self, Write};

#[derive(Parser)]
#[command(
    author,
    version,
    about = "Observatory - Control Tower for Alfred's Ecosystem",
    long_about = None
)]
struct Args {
    #[command(subcommand)]
    command: Commands,

    /// Output format
    #[arg(short, long, value_enum, default_value = "text")]
    format: OutputFormat,
}

#[derive(Subcommand)]
enum Commands {
    /// System overview dashboard
    Overview,
    /// Tool lineage graph
    Lineage {
        /// Tool ID
        #[arg(required = true)]
        tool: String,
    },
    /// Subsystem capability map
    SubsystemMap,
    /// Pipeline heatmap
    PipelineHeatmap,
    /// Governor dashboard
    Governor,
    /// Capability radar
    CapabilityRadar,
    /// Mutation log
    MutationLog,
    /// Telemetry stream (live)
    Stream,
    /// Export full state
    Export {
        /// Output file
        #[arg(short, long)]
        output: Option<String>,
    },
}

#[derive(clap::ValueEnum, Clone, Debug)]
enum OutputFormat {
    Text,
    Json,
}

fn print_overview(overview: &SystemOverview, format: &OutputFormat) {
    match format {
        OutputFormat::Text => {
            println!("╔══════════════════════════════════════════════════════════╗");
            println!("║           ALFRED OBSERVATORY - SYSTEM OVERVIEW            ║");
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  Timestamp: {}", overview.timestamp);
            println!("║  System State: {}", overview.state);
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  TOTALS                                                  ║");
            println!("║    Tools:        {:>6}                                    ", overview.totals.tools);
            println!("║    Skills:       {:>6}                                    ", overview.totals.skills);
            println!("║    Subsystems:   {:>6}                                    ", overview.totals.subsystems);
            println!("║    Pipelines:    {:>6}                                    ", overview.totals.pipelines);
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  HEALTH                                                  ║");
            println!("║    Avg Tool Fitness:      {:.1}%                         ", overview.health.avg_tool_fitness * 100.0);
            println!("║    Avg Subsystem Fitness: {:.1}%                         ", overview.health.avg_subsystem_fitness * 100.0);
            println!("║    Success Rate:          {:.1}%                         ", overview.health.success_rate * 100.0);
            println!("║    Active Tools:          {:>6}                          ", overview.health.active_tools);
            println!("╚══════════════════════════════════════════════════════════╝");
        }
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&overview).unwrap());
        }
    }
}

fn print_lineage(graph: &LineageGraph, format: &OutputFormat) {
    match format {
        OutputFormat::Text => {
            println!("\nLineage for: {}\n", graph.tool_id);
            
            if !graph.ancestors.is_empty() {
                println!("Ancestors:");
                for (i, ancestor) in graph.ancestors.iter().enumerate() {
                    let indent = "  ".repeat(i);
                    println!("  {}← {}", indent, ancestor);
                }
            } else {
                println!("(no ancestors - root tool)");
            }
            
            if !graph.descendants.is_empty() {
                println!("\nDescendants:");
                for descendant in &graph.descendants {
                    println!("  → {}", descendant);
                }
            }
            
            if !graph.fitness_history.is_empty() {
                println!("\nFitness History:");
                for point in &graph.fitness_history {
                    println!("  {}: {:.2}", point.timestamp, point.fitness);
                }
            }
        }
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&graph).unwrap());
        }
    }
}

fn print_subsystem_map(map: &SubsystemMap, format: &OutputFormat) {
    match format {
        OutputFormat::Text => {
            println!("\n╔══════════════════════════════════════════════════════════╗");
            println!("║              SUBSYSTEM CAPABILITY MAP                     ║");
            println!("╠══════════════════════════════════════════════════════════╣");
            
            let mut by_category: std::collections::HashMap<String, Vec<_>> = std::collections::HashMap::new();
            for node in &map.subsystems {
                by_category.entry(node.category.clone())
                    .or_insert_with(Vec::new)
                    .push(node);
            }
            
            for (category, nodes) in &by_category {
                println!("\n║  {:<50} ║", category.to_uppercase());
                println!("║  ──────────────────────────────────────────────────  ║");
                for node in nodes {
                    let fitness_bar = "█".repeat((node.fitness * 10.0) as usize);
                    println!("║    {:<20} [{}] {:.0}%  ", 
                        node.name, fitness_bar, node.fitness * 100.0);
                    println!("║      Tools: {}                                           ", node.tool_count);
                }
            }
            
            println!("\n║  CONNECTIONS: {}                                  ", map.connections.len());
            println!("╚══════════════════════════════════════════════════════════╝");
        }
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&map).unwrap());
        }
    }
}

fn print_governor_dashboard(budget: &governor::BudgetStatus, state: &governor::SystemState, format: &OutputFormat) {
    match format {
        OutputFormat::Text => {
            println!("\n╔══════════════════════════════════════════════════════════╗");
            println!("║                  GOVERNOR DASHBOARD                       ║");
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  System Mode: {:<40} ║", format!("{:?}", state));
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  BUDGET STATUS                                            ║");
            println!("║    Tool Creation:        {:>3} / {:<3}                     ", budget.tools_created_today, budget.tools_created_today + budget.tools_remaining);
            println!("║    Subsystem Creation:   {:>3} / {:<3}                     ", budget.subsystems_created_this_week, budget.subsystems_created_this_week + budget.subsystems_remaining);
            println!("╠══════════════════════════════════════════════════════════╣");
            println!("║  REMAINING BUDGET                                         ║");
            println!("║    Tools Today:          {:>3}                             ", budget.tools_remaining);
            println!("║    Subsystems This Week: {:>3}                             ", budget.subsystems_remaining);
            println!("╚══════════════════════════════════════════════════════════╝");
        }
        OutputFormat::Json => {
            println!("{}", serde_json::json!({
                "state": format!("{:?}", state),
                "budget": budget
            }));
        }
    }
}

fn print_capability_radar(format: &OutputFormat) {
    let capabilities = vec![
        ("filesystem", 8),
        ("network", 5),
        ("ai", 7),
        ("data", 6),
        ("security", 3),
        ("automation", 5),
        ("analysis", 7),
    ];
    
    match format {
        OutputFormat::Text => {
            println!("\n╔══════════════════════════════════════════════════════════╗");
            println!("║                  CAPABILITY RADAR                         ║");
            println!("╠══════════════════════════════════════════════════════════╣");
            for (cap, strength) in capabilities {
                let bar = "█".repeat(strength);
                println!("║  {:<15} {}                                     ", cap, bar);
            }
            println!("╚══════════════════════════════════════════════════════════╝");
        }
        OutputFormat::Json => {
            println!("{}", serde_json::json!({
                "capabilities": capabilities
            }));
        }
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    let observatory = observatory::create_observatory()?;
    
    match args.command {
        Commands::Overview => {
            let overview = observatory.get_overview()?;
            print_overview(&overview, &args.format);
        }
        Commands::Lineage { tool } => {
            let graph = observatory.get_lineage(&tool)?;
            print_lineage(&graph, &args.format);
        }
        Commands::SubsystemMap => {
            let map = observatory.get_subsystem_map()?;
            print_subsystem_map(&map, &args.format);
        }
        Commands::PipelineHeatmap => {
            // Would need pipeline execution data
            println!("Pipeline heatmap - coming soon");
        }
        Commands::Governor => {
            let budget = observatory.get_budget_status();
            let state = observatory.governor.get_state();
            print_governor_dashboard(&budget, &state, &args.format);
        }
        Commands::CapabilityRadar => {
            print_capability_radar(&args.format);
        }
        Commands::MutationLog => {
            let violations = observatory.get_violations();
            println!("Mutation Log ({} entries):", violations.len());
            for v in violations {
                println!("  [{}] {}: {}", v.timestamp, v.violation_type, v.details);
            }
        }
        Commands::Stream => {
            println!("Starting telemetry stream... (Ctrl+C to stop)");
            println!("Listening for events on stdin...\n");
            
            let stdin = io::stdin();
            let mut stdout = io::stdout();
            let mut event_count = 0;
            
            for line in stdin.lock().lines() {
                let line = line?;
                event_count += 1;
                
                // Parse and display event
                if let Ok(event) = serde_json::from_str::<serde_json::Value>(&line) {
                    let event_type = event.get("type").and_then(|v| v.as_str()).unwrap_or("unknown");
                    let timestamp = event.get("timestamp").and_then(|v| v.as_str()).unwrap_or("unknown");
                    
                    println!("[{}] {}: {:?}", timestamp, event_type, event);
                    stdout.flush()?;
                }
            }
            
            println!("\nReceived {} events", event_count);
        }
        Commands::Export { output } => {
            let state = observatory.export_state()?;
            
            if let Some(path) = output {
                std::fs::write(&path, state)?;
                println!("Exported to: {}", path);
            } else {
                println!("{}", state);
            }
        }
    }
    
    Ok(())
}
