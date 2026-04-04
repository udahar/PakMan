//! Observatory - Real-time system monitoring dashboard
//!
//! Provides visibility into tool evolution, subsystem health, and system metrics.

use anyhow::Result;
use chrono::Local;
use serde::{Deserialize, Serialize};
use skill_registry::SkillRegistry;
use subsystem_registry::SubsystemRegistry;
use governor::{Governor, BudgetStatus, SystemState};

/// System overview for dashboard
#[derive(Serialize, Deserialize, Debug)]
pub struct SystemOverview {
    pub timestamp: String,
    pub state: String,
    pub totals: SystemTotals,
    pub health: SystemHealth,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SystemTotals {
    pub tools: usize,
    pub skills: usize,
    pub subsystems: usize,
    pub pipelines: usize,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SystemHealth {
    pub avg_tool_fitness: f32,
    pub avg_subsystem_fitness: f32,
    pub success_rate: f32,
    pub active_tools: usize,
}

/// Tool lineage visualization
#[derive(Serialize, Deserialize, Debug)]
pub struct LineageGraph {
    pub tool_id: String,
    pub ancestors: Vec<String>,
    pub descendants: Vec<String>,
    pub fitness_history: Vec<FitnessPoint>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct FitnessPoint {
    pub timestamp: String,
    pub fitness: f32,
}

/// Subsystem map
#[derive(Serialize, Deserialize, Debug)]
pub struct SubsystemMap {
    pub subsystems: Vec<SubsystemNode>,
    pub connections: Vec<Connection>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SubsystemNode {
    pub id: String,
    pub name: String,
    pub category: String,
    pub fitness: f32,
    pub tool_count: usize,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Connection {
    pub from: String,
    pub to: String,
    pub connection_type: String,
}

/// Observatory - system monitoring
pub struct Observatory {
    skill_registry: SkillRegistry,
    subsystem_registry: SubsystemRegistry,
    governor: Governor,
}

impl Observatory {
    pub fn new(
        skill_registry: SkillRegistry,
        subsystem_registry: SubsystemRegistry,
        governor: Governor,
    ) -> Self {
        Self {
            skill_registry,
            subsystem_registry,
            governor,
        }
    }

    /// Get system overview
    pub fn get_overview(&self) -> Result<SystemOverview> {
        let skills = self.skill_registry.list_skills().unwrap_or_default();
        let subsystems = self.subsystem_registry.list_subsystems().unwrap_or_default();
        
        let avg_tool_fitness = if !skills.is_empty() {
            skills.iter()
                .map(|s| if s.usage_count > 0 { 
                    s.success_count as f32 / (s.success_count + s.failure_count) as f32 
                } else { 0.5 })
                .sum::<f32>() / skills.len() as f32
        } else {
            0.5
        };

        let avg_subsystem_fitness = if !subsystems.is_empty() {
            subsystems.iter().map(|s| s.fitness_score).sum::<f32>() / subsystems.len() as f32
        } else {
            0.5
        };

        let total_success: u64 = skills.iter().map(|s| s.success_count).sum();
        let total_failure: u64 = skills.iter().map(|s| s.failure_count).sum();
        let success_rate = if total_success + total_failure > 0 {
            total_success as f32 / (total_success + total_failure) as f32
        } else {
            1.0
        };

        Ok(SystemOverview {
            timestamp: Local::now().to_rfc3339(),
            state: format!("{:?}", self.governor.get_state()),
            totals: SystemTotals {
                tools: skills.len(),
                skills: skills.len(),
                subsystems: subsystems.len(),
                pipelines: subsystems.iter().map(|s| s.pipelines.len()).sum(),
            },
            health: SystemHealth {
                avg_tool_fitness,
                avg_subsystem_fitness,
                success_rate,
                active_tools: skills.iter().filter(|s| s.usage_count > 0).count(),
            },
        })
    }

    /// Get budget status
    pub fn get_budget_status(&self) -> BudgetStatus {
        self.governor.get_budget_status()
    }

    /// Get tool lineage
    pub fn get_lineage(&self, tool_id: &str) -> Result<LineageGraph> {
        let ancestors = self.skill_registry.get_lineage(tool_id).unwrap_or_default();
        
        Ok(LineageGraph {
            tool_id: tool_id.to_string(),
            ancestors: ancestors.clone(),
            descendants: vec![], // Would need reverse lookup
            fitness_history: vec![], // Would need historical data
        })
    }

    /// Get subsystem map
    pub fn get_subsystem_map(&self) -> Result<SubsystemMap> {
        let subsystems = self.subsystem_registry.list_subsystems().unwrap_or_default();
        let capability_map = self.subsystem_registry.get_capability_map().unwrap_or_default();

        let nodes: Vec<SubsystemNode> = subsystems.iter().map(|s| SubsystemNode {
            id: s.id.clone(),
            name: s.name.clone(),
            category: s.category.clone(),
            fitness: s.fitness_score,
            tool_count: s.components.len(),
        }).collect();

        let connections: Vec<Connection> = capability_map.iter().map(|(cap, sys, tool)| {
            Connection {
                from: sys.clone(),
                to: tool.clone(),
                connection_type: cap.clone(),
            }
        }).collect();

        Ok(SubsystemMap {
            subsystems: nodes,
            connections,
        })
    }

    /// Get violations log
    pub fn get_violations(&self) -> Vec<governor::ViolationRecord> {
        self.governor.get_violations().to_vec()
    }

    /// Export system state as JSON
    pub fn export_state(&self) -> Result<String> {
        let overview = self.get_overview()?;
        let budget = self.get_budget_status();
        let subsystem_map = self.get_subsystem_map()?;

        let state = serde_json::json!({
            "overview": overview,
            "budget": budget,
            "subsystem_map": subsystem_map,
            "violations": self.get_violations(),
        });

        Ok(serde_json::to_string_pretty(&state)?)
    }
}

/// Create observatory from default registries
pub fn create_observatory() -> Result<Observatory> {
    let skill_registry = SkillRegistry::open(&std::path::PathBuf::from("skills.db"))?;
    let subsystem_registry = SubsystemRegistry::open(&std::path::PathBuf::from("subsystems.db"))?;
    let governor = Governor::new(Default::default());

    Ok(Observatory::new(skill_registry, subsystem_registry, governor))
}
