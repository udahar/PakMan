//! Governor - Safety constraints and build budgets
//!
//! The governor prevents runaway tool creation and maintains system stability.
//! It enforces rules without doing creative work.

use anyhow::Result;
use chrono::{DateTime, Duration, Local};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::sync::{Arc, Mutex};

/// Governor configuration
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GovernorConfig {
    /// Maximum new tools per day
    pub max_new_tools_per_day: u32,
    /// Maximum new subsystems per week
    pub max_new_subsystems_per_week: u32,
    /// Maximum compile attempts per tool
    pub max_compile_attempts: u32,
    /// Minimum fitness score for tools
    pub minimum_fitness: f32,
    /// Minimum runs before fitness evaluation
    pub minimum_runs: u32,
    /// Maximum mutations per tool lineage
    pub max_mutations_per_tool: u32,
    /// Cooldown period between mutations (hours)
    pub mutation_cooldown_hours: u32,
    /// Allowed capabilities
    pub allowed_capabilities: Vec<String>,
}

impl Default for GovernorConfig {
    fn default() -> Self {
        Self {
            max_new_tools_per_day: 3,
            max_new_subsystems_per_week: 1,
            max_compile_attempts: 5,
            minimum_fitness: 0.65,
            minimum_runs: 10,
            max_mutations_per_tool: 3,
            mutation_cooldown_hours: 24,
            allowed_capabilities: vec![
                "filesystem".to_string(),
                "network".to_string(),
                "ai".to_string(),
                "data".to_string(),
                "security".to_string(),
                "automation".to_string(),
                "analysis".to_string(),
            ],
        }
    }
}

/// System state
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum SystemState {
    Normal,
    SafeMode,
    Locked,
}

/// Build budget tracker
#[derive(Serialize, Deserialize, Debug)]
pub struct BuildBudget {
    pub tools_created_today: u32,
    pub subsystems_created_this_week: u32,
    pub last_reset: String,
    pub compile_attempts: HashMap<String, u32>,
}

impl BuildBudget {
    pub fn new() -> Self {
        Self {
            tools_created_today: 0,
            subsystems_created_this_week: 0,
            last_reset: Local::now().to_rfc3339(),
            compile_attempts: HashMap::new(),
        }
    }

    pub fn reset_if_needed(&mut self) {
        let now = Local::now();
        let last_reset: DateTime<Local> = DateTime::parse_from_rfc3339(&self.last_reset)
            .unwrap_or_else(|_| now.into())
            .into();

        // Reset daily counter
        if now.date_naive() > last_reset.date_naive() {
            self.tools_created_today = 0;
            self.last_reset = now.to_rfc3339();
        }

        // Reset weekly counter
        let week_ago = now - Duration::weeks(1);
        if last_reset < week_ago {
            self.subsystems_created_this_week = 0;
        }
    }
}

impl Default for BuildBudget {
    fn default() -> Self {
        Self::new()
    }
}

/// Governor - enforces rules and limits
pub struct Governor {
    config: GovernorConfig,
    budget: Arc<Mutex<BuildBudget>>,
    state: Arc<Mutex<SystemState>>,
    violation_log: Vec<ViolationRecord>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ViolationRecord {
    pub timestamp: String,
    pub violation_type: String,
    pub details: String,
    pub action: String,
}

impl Governor {
    pub fn new(config: GovernorConfig) -> Self {
        Self {
            config,
            budget: Arc::new(Mutex::new(BuildBudget::new())),
            state: Arc::new(Mutex::new(SystemState::Normal)),
            violation_log: Vec::new(),
        }
    }

    /// Check if a capability is allowed
    pub fn check_capability(&self, capability: &str) -> GovernorDecision {
        if self.config.allowed_capabilities.contains(&capability.to_lowercase()) {
            GovernorDecision::Allow
        } else {
            GovernorDecision::Reject {
                reason: format!("Capability '{}' is not in allowed list", capability),
                requires_review: true,
            }
        }
    }

    /// Check if we can create a new tool
    pub fn check_tool_creation(&self) -> GovernorDecision {
        let budget = self.budget.lock().unwrap();
        
        if budget.tools_created_today >= self.config.max_new_tools_per_day {
            return GovernorDecision::Reject {
                reason: format!(
                    "Daily tool creation limit reached ({}/{})",
                    budget.tools_created_today, self.config.max_new_tools_per_day
                ),
                requires_review: false,
            };
        }

        GovernorDecision::Allow
    }

    /// Check if we can create a new subsystem
    pub fn check_subsystem_creation(&self) -> GovernorDecision {
        let budget = self.budget.lock().unwrap();
        
        if budget.subsystems_created_this_week >= self.config.max_new_subsystems_per_week {
            return GovernorDecision::Reject {
                reason: format!(
                    "Weekly subsystem creation limit reached ({}/{})",
                    budget.subsystems_created_this_week, self.config.max_new_subsystems_per_week
                ),
                requires_review: false,
            };
        }

        GovernorDecision::Allow
    }

    /// Record tool creation
    pub fn record_tool_created(&self) {
        let mut budget = self.budget.lock().unwrap();
        budget.tools_created_today += 1;
    }

    /// Record subsystem creation
    pub fn record_subsystem_created(&self) {
        let mut budget = self.budget.lock().unwrap();
        budget.subsystems_created_this_week += 1;
    }

    /// Check compile attempts
    pub fn check_compile_attempts(&self, tool_id: &str) -> GovernorDecision {
        let budget = self.budget.lock().unwrap();
        let attempts = budget.compile_attempts.get(tool_id).copied().unwrap_or(0);
        
        if attempts >= self.config.max_compile_attempts {
            return GovernorDecision::Reject {
                reason: format!(
                    "Max compile attempts reached for {} ({}/{})",
                    tool_id, attempts, self.config.max_compile_attempts
                ),
                requires_review: true,
            };
        }

        GovernorDecision::Allow
    }

    /// Record compile attempt
    pub fn record_compile_attempt(&self, tool_id: &str) {
        let mut budget = self.budget.lock().unwrap();
        let attempts = budget.compile_attempts.entry(tool_id.to_string()).or_insert(0);
        *attempts += 1;
    }

    /// Check if tool fitness is acceptable
    pub fn check_fitness(&self, fitness_score: f32, run_count: u32) -> GovernorDecision {
        if run_count < self.config.minimum_runs {
            return GovernorDecision::Pending {
                reason: format!("Not enough runs for evaluation ({}/{})", 
                    run_count, self.config.minimum_runs),
            };
        }

        if fitness_score < self.config.minimum_fitness {
            GovernorDecision::Reject {
                reason: format!(
                    "Fitness score below threshold ({:.2} < {:.2})",
                    fitness_score, self.config.minimum_fitness
                ),
                requires_review: false,
            }
        } else {
            GovernorDecision::Allow
        }
    }

    /// Check mutation cooldown
    pub fn check_mutation(&self, tool_id: &str, last_mutation: Option<DateTime<Local>>) -> GovernorDecision {
        // Check mutation count
        // In production, this would query the genome registry
        
        if let Some(last_mut) = last_mutation {
            let now = Local::now();
            let cooldown = Duration::hours(self.config.mutation_cooldown_hours as i64);
            
            if now < last_mut + cooldown {
                let hours_left = ((last_mut + cooldown - now).num_seconds() / 3600) + 1;
                return GovernorDecision::Reject {
                    reason: format!("Mutation cooldown active ({} hours remaining)", hours_left),
                    requires_review: false,
                };
            }
        }

        GovernorDecision::Allow
    }

    /// Get current system state
    pub fn get_state(&self) -> SystemState {
        self.state.lock().unwrap().clone()
    }

    /// Set system state (e.g., safe mode)
    pub fn set_state(&self, state: SystemState) {
        let mut current = self.state.lock().unwrap();
        *current = state.clone();
        
        if state != SystemState::Normal {
            self.violation_log.push(ViolationRecord {
                timestamp: Local::now().to_rfc3339(),
                violation_type: "state_change".to_string(),
                details: format!("System state changed to {:?}", state),
                action: "automatic".to_string(),
            });
        }
    }

    /// Enter safe mode
    pub fn enter_safe_mode(&self, reason: &str) {
        self.set_state(SystemState::SafeMode);
        self.violation_log.push(ViolationRecord {
            timestamp: Local::now().to_rfc3339(),
            violation_type: "safe_mode_triggered".to_string(),
            details: reason.to_string(),
            action: "entered_safe_mode".to_string(),
        });
    }

    /// Check if system allows tool creation
    pub fn allows_creation(&self) -> bool {
        matches!(self.get_state(), SystemState::Normal)
    }

    /// Get violation log
    pub fn get_violations(&self) -> &[ViolationRecord] {
        &self.violation_log
    }

    /// Get budget status
    pub fn get_budget_status(&self) -> BudgetStatus {
        let budget = self.budget.lock().unwrap();
        BudgetStatus {
            tools_created_today: budget.tools_created_today,
            tools_remaining: self.config.max_new_tools_per_day - budget.tools_created_today,
            subsystems_created_this_week: budget.subsystems_created_this_week,
            subsystems_remaining: self.config.max_new_subsystems_per_week - budget.subsystems_created_this_week,
        }
    }
}

/// Governor decision
#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum GovernorDecision {
    Allow,
    Reject {
        reason: String,
        requires_review: bool,
    },
    Pending {
        reason: String,
    },
}

impl GovernorDecision {
    pub fn is_allowed(&self) -> bool {
        matches!(self, GovernorDecision::Allow)
    }

    pub fn is_rejected(&self) -> bool {
        matches!(self, GovernorDecision::Reject { .. })
    }
}

/// Budget status summary
#[derive(Serialize, Deserialize, Debug)]
pub struct BudgetStatus {
    pub tools_created_today: u32,
    pub tools_remaining: u32,
    pub subsystems_created_this_week: u32,
    pub subsystems_remaining: u32,
}

/// Create default governor
pub fn create_governor() -> Governor {
    Governor::new(GovernorConfig::default())
}
