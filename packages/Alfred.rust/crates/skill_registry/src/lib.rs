//! Skill Registry and Tool Genome
//!
//! Provides:
//! - Skill storage and discovery
//! - Tool genome tracking (lineage, fitness, evolution)
//! - Usage statistics

use anyhow::Result;
use chrono::{DateTime, Local};
use rusqlite::{Connection, params};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::Mutex;

/// A skill (reusable pipeline/capability)
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Skill {
    pub id: String,
    pub name: String,
    pub description: String,
    pub pipeline: Pipeline,
    pub tags: Vec<String>,
    pub category: String,
    pub created_at: String,
    pub version: String,
    pub usage_count: u64,
    pub success_count: u64,
    pub failure_count: u64,
    pub avg_duration_ms: f64,
}

/// A pipeline of tool steps
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Pipeline {
    pub steps: Vec<PipelineStep>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PipelineStep {
    pub tool: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub parameters: serde_json::Value,
}

/// Tool Genome - tracks tool lineage and evolution
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ToolGenome {
    pub tool_id: String,
    pub version: String,
    pub parent: Option<String>,
    pub capability: String,
    pub category: String,
    pub created_by: String,  // "human" or "alfred"
    pub created_at: String,
    pub fitness_score: f32,
    pub usage_count: u64,
    pub success_count: u64,
    pub failure_count: u64,
    pub avg_runtime_ms: f64,
    pub mutation_type: Option<String>,
    pub is_deprecated: bool,
}

/// Skill Registry with SQLite storage
pub struct SkillRegistry {
    conn: Mutex<Connection>,
}

impl SkillRegistry {
    /// Open or create a skill registry database
    pub fn open(path: &Path) -> Result<Self> {
        let conn = Connection::open(path)?;
        
        // Create tables
        conn.execute(
            "CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                pipeline_json TEXT NOT NULL,
                tags TEXT,
                category TEXT,
                created_at TEXT,
                version TEXT,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_duration_ms REAL DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS tool_genome (
                tool_id TEXT PRIMARY KEY,
                version TEXT,
                parent TEXT,
                capability TEXT,
                category TEXT,
                created_by TEXT,
                created_at TEXT,
                fitness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_runtime_ms REAL DEFAULT 0,
                mutation_type TEXT,
                is_deprecated INTEGER DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS tool_lineage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id TEXT,
                parent_tool_id TEXT,
                relationship TEXT,
                created_at TEXT
            )",
            [],
        )?;

        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
                name, description, tags, content='skills', content_rowid='rowid'
            )",
            [],
        )?;

        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Create an in-memory registry (for testing)
    pub fn in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        // Same schema creation as above...
        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Register a new skill
    pub fn register_skill(&self, skill: Skill) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        let pipeline_json = serde_json::to_string(&skill.pipeline)?;
        let tags_json = serde_json::to_string(&skill.tags)?;

        conn.execute(
            "INSERT OR REPLACE INTO skills 
             (id, name, description, pipeline_json, tags, category, created_at, version, 
              usage_count, success_count, failure_count, avg_duration_ms)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0, 0, 0, 0)",
            params![
                skill.id,
                skill.name,
                skill.description,
                pipeline_json,
                tags_json,
                skill.category,
                skill.created_at,
                skill.version,
            ],
        )?;

        Ok(())
    }

    /// Get a skill by ID
    pub fn get_skill(&self, id: &str) -> Result<Option<Skill>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, description, pipeline_json, tags, category, 
                    created_at, version, usage_count, success_count, failure_count, avg_duration_ms
             FROM skills WHERE id = ?1"
        )?;

        let skill = stmt.query_row(params![id], |row| {
            let pipeline_json: String = row.get(3)?;
            let tags_json: String = row.get(4)?;
            
            Ok(Skill {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                pipeline: serde_json::from_str(&pipeline_json)?,
                tags: serde_json::from_str(&tags_json)?,
                category: row.get(5)?,
                created_at: row.get(6)?,
                version: row.get(7)?,
                usage_count: row.get(8)?,
                success_count: row.get(9)?,
                failure_count: row.get(10)?,
                avg_duration_ms: row.get(11)?,
            })
        })?;

        Ok(Some(skill))
    }

    /// Search skills by query
    pub fn search_skills(&self, query: &str) -> Result<Vec<Skill>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, description, pipeline_json, tags, category,
                    created_at, version, usage_count, success_count, failure_count, avg_duration_ms
             FROM skills 
             WHERE name LIKE ?1 OR description LIKE ?1 OR tags LIKE ?1
             ORDER BY usage_count DESC"
        )?;

        let search_pattern = format!("%{}%", query);
        let skills = stmt.query_map(params![search_pattern], |row| {
            let pipeline_json: String = row.get(3)?;
            let tags_json: String = row.get(4)?;
            
            Ok(Skill {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                pipeline: serde_json::from_str(&pipeline_json)?,
                tags: serde_json::from_str(&tags_json)?,
                category: row.get(5)?,
                created_at: row.get(6)?,
                version: row.get(7)?,
                usage_count: row.get(8)?,
                success_count: row.get(9)?,
                failure_count: row.get(10)?,
                avg_duration_ms: row.get(11)?,
            })
        })?;

        let mut result = Vec::new();
        for skill in skills {
            result.push(skill?);
        }

        Ok(result)
    }

    /// List all skills
    pub fn list_skills(&self) -> Result<Vec<Skill>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, description, pipeline_json, tags, category,
                    created_at, version, usage_count, success_count, failure_count, avg_duration_ms
             FROM skills ORDER BY name"
        )?;

        let skills = stmt.query_map([], |row| {
            let pipeline_json: String = row.get(3)?;
            let tags_json: String = row.get(4)?;
            
            Ok(Skill {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                pipeline: serde_json::from_str(&pipeline_json)?,
                tags: serde_json::from_str(&tags_json)?,
                category: row.get(5)?,
                created_at: row.get(6)?,
                version: row.get(7)?,
                usage_count: row.get(8)?,
                success_count: row.get(9)?,
                failure_count: row.get(10)?,
                avg_duration_ms: row.get(11)?,
            })
        })?;

        let mut result = Vec::new();
        for skill in skills {
            result.push(skill?);
        }

        Ok(result)
    }

    /// Record skill usage
    pub fn record_usage(&self, skill_id: &str, success: bool, duration_ms: f64) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        if success {
            conn.execute(
                "UPDATE skills SET usage_count = usage_count + 1, success_count = success_count + 1
                 WHERE id = ?1",
                params![skill_id],
            )?;
        } else {
            conn.execute(
                "UPDATE skills SET usage_count = usage_count + 1, failure_count = failure_count + 1
                 WHERE id = ?1",
                params![skill_id],
            )?;
        }

        // Update average duration
        conn.execute(
            "UPDATE skills SET avg_duration_ms = (
                SELECT (avg_duration_ms * (usage_count - 1) + ?2) / usage_count FROM skills WHERE id = ?1
            ) WHERE id = ?1",
            params![skill_id, duration_ms],
        )?;

        Ok(())
    }

    /// Register a tool in the genome
    pub fn register_tool(&self, genome: ToolGenome) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        conn.execute(
            "INSERT OR REPLACE INTO tool_genome 
             (tool_id, version, parent, capability, category, created_by, created_at,
              fitness_score, usage_count, success_count, failure_count, avg_runtime_ms,
              mutation_type, is_deprecated)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0, 0, 0, 0, ?9, 0)",
            params![
                genome.tool_id,
                genome.version,
                genome.parent,
                genome.capability,
                genome.category,
                genome.created_by,
                genome.created_at,
                genome.fitness_score,
                genome.mutation_type,
            ],
        )?;

        // Record lineage
        if let Some(parent) = &genome.parent {
            conn.execute(
                "INSERT INTO tool_lineage (tool_id, parent_tool_id, relationship, created_at)
                 VALUES (?1, ?2, 'child', ?3)",
                params![genome.tool_id, parent, Local::now().to_rfc3339()],
            )?;
        }

        Ok(())
    }

    /// Get tool genome by ID
    pub fn get_tool_genome(&self, tool_id: &str) -> Result<Option<ToolGenome>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT tool_id, version, parent, capability, category, created_by,
                    created_at, fitness_score, usage_count, success_count, failure_count,
                    avg_runtime_ms, mutation_type, is_deprecated
             FROM tool_genome WHERE tool_id = ?1"
        )?;

        let genome = stmt.query_row(params![tool_id], |row| {
            Ok(ToolGenome {
                tool_id: row.get(0)?,
                version: row.get(1)?,
                parent: row.get(2)?,
                capability: row.get(3)?,
                category: row.get(4)?,
                created_by: row.get(5)?,
                created_at: row.get(6)?,
                fitness_score: row.get(7)?,
                usage_count: row.get(8)?,
                success_count: row.get(9)?,
                failure_count: row.get(10)?,
                avg_runtime_ms: row.get(11)?,
                mutation_type: row.get(12)?,
                is_deprecated: row.get::<_, i32>(13)? != 0,
            })
        })?;

        Ok(Some(genome))
    }

    /// Update tool fitness after execution
    pub fn update_tool_fitness(&self, tool_id: &str, success: bool, runtime_ms: f64) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        if success {
            conn.execute(
                "UPDATE tool_genome SET 
                    usage_count = usage_count + 1,
                    success_count = success_count + 1,
                    fitness_score = MIN(1.0, fitness_score + 0.01)
                 WHERE tool_id = ?1",
                params![tool_id],
            )?;
        } else {
            conn.execute(
                "UPDATE tool_genome SET 
                    usage_count = usage_count + 1,
                    failure_count = failure_count + 1,
                    fitness_score = MAX(0.0, fitness_score - 0.05)
                 WHERE tool_id = ?1",
                params![tool_id],
            )?;
        }

        // Update average runtime
        conn.execute(
            "UPDATE tool_genome SET avg_runtime_ms = (
                SELECT (avg_runtime_ms * (usage_count - 1) + ?2) / usage_count FROM tool_genome WHERE tool_id = ?1
            ) WHERE tool_id = ?1",
            params![tool_id, runtime_ms],
        )?;

        Ok(())
    }

    /// Get tools by capability
    pub fn get_tools_by_capability(&self, capability: &str) -> Result<Vec<ToolGenome>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT tool_id, version, parent, capability, category, created_by,
                    created_at, fitness_score, usage_count, success_count, failure_count,
                    avg_runtime_ms, mutation_type, is_deprecated
             FROM tool_genome 
             WHERE capability = ?1 AND is_deprecated = 0
             ORDER BY fitness_score DESC"
        )?;

        let genomes = stmt.query_map(params![capability], |row| {
            Ok(ToolGenome {
                tool_id: row.get(0)?,
                version: row.get(1)?,
                parent: row.get(2)?,
                capability: row.get(3)?,
                category: row.get(4)?,
                created_by: row.get(5)?,
                created_at: row.get(6)?,
                fitness_score: row.get(7)?,
                usage_count: row.get(8)?,
                success_count: row.get(9)?,
                failure_count: row.get(10)?,
                avg_runtime_ms: row.get(11)?,
                mutation_type: row.get(12)?,
                is_deprecated: row.get::<_, i32>(13)? != 0,
            })
        })?;

        let mut result = Vec::new();
        for genome in genomes {
            result.push(genome?);
        }

        Ok(result)
    }

    /// Check if capability exists
    pub fn has_capability(&self, capability: &str) -> Result<bool> {
        let tools = self.get_tools_by_capability(capability)?;
        Ok(!tools.is_empty())
    }

    /// Get tool lineage (ancestors and descendants)
    pub fn get_lineage(&self, tool_id: &str) -> Result<Vec<String>> {
        let conn = self.conn.lock().unwrap();
        
        let mut lineage = Vec::new();
        
        // Get ancestors
        let mut current = tool_id.to_string();
        loop {
            let genome = self.get_tool_genome(&current)?;
            if let Some(g) = genome {
                if let Some(parent) = g.parent {
                    lineage.push(parent.clone());
                    current = parent;
                } else {
                    break;
                }
            } else {
                break;
            }
        }

        // Get descendants
        let mut stmt = conn.prepare(
            "SELECT tool_id FROM tool_genome WHERE parent = ?1"
        )?;
        
        let descendants = stmt.query_map(params![tool_id], |row| {
            row.get::<_, String>(0)
        })?;
        
        for desc in descendants {
            lineage.push(desc?);
        }

        Ok(lineage)
    }

    /// Deprecate a low-fitness tool
    pub fn deprecate_tool(&self, tool_id: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        conn.execute(
            "UPDATE tool_genome SET is_deprecated = 1 WHERE tool_id = ?1",
            params![tool_id],
        )?;

        Ok(())
    }

    /// Get all tool categories
    pub fn get_categories(&self) -> Result<Vec<String>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT DISTINCT category FROM tool_genome ORDER BY category"
        )?;
        
        let categories = stmt.query_map([], |row| {
            row.get::<_, String>(0)
        })?;
        
        let mut result = Vec::new();
        for cat in categories {
            result.push(cat?);
        }

        Ok(result)
    }
}

/// Create a default skill registry at the default path
pub fn create_registry() -> Result<SkillRegistry> {
    let path = std::env::current_dir()?.join("skills.db");
    SkillRegistry::open(&path)
}
