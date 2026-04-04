//! Subsystem Registry - Architecture-level capability organization
//!
//! Subsystems bundle related tools and pipelines into cohesive modules.
//! This keeps complexity manageable as the system grows.

use anyhow::Result;
use chrono::Local;
use rusqlite::{Connection, params};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::Mutex;

/// A subsystem - a coordinated cluster of tools and pipelines
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Subsystem {
    pub id: String,
    pub name: String,
    pub purpose: String,
    pub description: String,
    pub components: Vec<String>,  // Tool names
    pub pipelines: Vec<SubsystemPipeline>,
    pub category: String,
    pub created_at: String,
    pub version: String,
    pub fitness_score: f32,
    pub usage_count: u64,
    pub is_active: bool,
}

/// A pipeline within a subsystem
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SubsystemPipeline {
    pub id: String,
    pub name: String,
    pub description: String,
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

/// Subsystem registry with SQLite storage
pub struct SubsystemRegistry {
    conn: Mutex<Connection>,
}

impl SubsystemRegistry {
    /// Open or create a subsystem registry
    pub fn open(path: &Path) -> Result<Self> {
        let conn = Connection::open(path)?;
        
        // Create subsystems table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS subsystems (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                purpose TEXT,
                description TEXT,
                components_json TEXT,
                pipelines_json TEXT,
                category TEXT,
                created_at TEXT,
                version TEXT,
                fitness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )",
            [],
        )?;

        // Create capability map table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS capability_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capability TEXT NOT NULL,
                subsystem_id TEXT,
                tool_id TEXT,
                UNIQUE(capability, subsystem_id, tool_id)
            )",
            [],
        )?;

        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Create an in-memory registry
    pub fn in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Register a new subsystem
    pub fn register_subsystem(&self, subsystem: Subsystem) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        let components_json = serde_json::to_string(&subsystem.components)?;
        let pipelines_json = serde_json::to_string(&subsystem.pipelines)?;

        conn.execute(
            "INSERT OR REPLACE INTO subsystems 
             (id, name, purpose, description, components_json, pipelines_json, 
              category, created_at, version, fitness_score, usage_count, is_active)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, 0.5, 0, 1)",
            params![
                subsystem.id,
                subsystem.name,
                subsystem.purpose,
                subsystem.description,
                components_json,
                pipelines_json,
                subsystem.category,
                subsystem.created_at,
                subsystem.version,
            ],
        )?;

        // Register capabilities
        for component in &subsystem.components {
            conn.execute(
                "INSERT OR IGNORE INTO capability_map (capability, subsystem_id, tool_id)
                 VALUES (?1, ?2, ?3)",
                params![subsystem.category, subsystem.id, component],
            )?;
        }

        Ok(())
    }

    /// Get a subsystem by ID
    pub fn get_subsystem(&self, id: &str) -> Result<Option<Subsystem>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, purpose, description, components_json, pipelines_json,
                    category, created_at, version, fitness_score, usage_count, is_active
             FROM subsystems WHERE id = ?1"
        )?;

        let subsystem = stmt.query_row(params![id], |row| {
            let components_json: String = row.get(4)?;
            let pipelines_json: String = row.get(5)?;
            
            Ok(Subsystem {
                id: row.get(0)?,
                name: row.get(1)?,
                purpose: row.get(2)?,
                description: row.get(3)?,
                components: serde_json::from_str(&components_json)?,
                pipelines: serde_json::from_str(&pipelines_json)?,
                category: row.get(6)?,
                created_at: row.get(7)?,
                version: row.get(8)?,
                fitness_score: row.get(9)?,
                usage_count: row.get(10)?,
                is_active: row.get::<_, i32>(11)? != 0,
            })
        })?;

        Ok(Some(subsystem))
    }

    /// List all subsystems
    pub fn list_subsystems(&self) -> Result<Vec<Subsystem>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, purpose, description, components_json, pipelines_json,
                    category, created_at, version, fitness_score, usage_count, is_active
             FROM subsystems ORDER BY name"
        )?;

        let subsystems = stmt.query_map([], |row| {
            let components_json: String = row.get(4)?;
            let pipelines_json: String = row.get(5)?;
            
            Ok(Subsystem {
                id: row.get(0)?,
                name: row.get(1)?,
                purpose: row.get(2)?,
                description: row.get(3)?,
                components: serde_json::from_str(&components_json)?,
                pipelines: serde_json::from_str(&pipelines_json)?,
                category: row.get(6)?,
                created_at: row.get(7)?,
                version: row.get(8)?,
                fitness_score: row.get(9)?,
                usage_count: row.get(10)?,
                is_active: row.get::<_, i32>(11)? != 0,
            })
        })?;

        let mut result = Vec::new();
        for subsystem in subsystems {
            result.push(subsystem?);
        }

        Ok(result)
    }

    /// Get subsystems by category
    pub fn get_by_category(&self, category: &str) -> Result<Vec<Subsystem>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, name, purpose, description, components_json, pipelines_json,
                    category, created_at, version, fitness_score, usage_count, is_active
             FROM subsystems WHERE category = ?1 ORDER BY fitness_score DESC"
        )?;

        let subsystems = stmt.query_map(params![category], |row| {
            let components_json: String = row.get(4)?;
            let pipelines_json: String = row.get(5)?;
            
            Ok(Subsystem {
                id: row.get(0)?,
                name: row.get(1)?,
                purpose: row.get(2)?,
                description: row.get(3)?,
                components: serde_json::from_str(&components_json)?,
                pipelines: serde_json::from_str(&pipelines_json)?,
                category: row.get(6)?,
                created_at: row.get(7)?,
                version: row.get(8)?,
                fitness_score: row.get(9)?,
                usage_count: row.get(10)?,
                is_active: row.get::<_, i32>(11)? != 0,
            })
        })?;

        let mut result = Vec::new();
        for subsystem in subsystems {
            result.push(subsystem?);
        }

        Ok(result)
    }

    /// Update subsystem fitness
    pub fn update_fitness(&self, subsystem_id: &str, success: bool) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        if success {
            conn.execute(
                "UPDATE subsystems SET 
                    usage_count = usage_count + 1,
                    fitness_score = MIN(1.0, fitness_score + 0.01)
                 WHERE id = ?1",
                params![subsystem_id],
            )?;
        } else {
            conn.execute(
                "UPDATE subsystems SET 
                    usage_count = usage_count + 1,
                    fitness_score = MAX(0.0, fitness_score - 0.02)
                 WHERE id = ?1",
                params![subsystem_id],
            )?;
        }

        Ok(())
    }

    /// Activate/deactivate a subsystem
    pub fn set_active(&self, subsystem_id: &str, active: bool) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        
        conn.execute(
            "UPDATE subsystems SET is_active = ?1 WHERE id = ?2",
            params![if active { 1 } else { 0 }, subsystem_id],
        )?;

        Ok(())
    }

    /// Get capability map
    pub fn get_capability_map(&self) -> Result<Vec<(String, String, String)>> {
        let conn = self.conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT capability, subsystem_id, tool_id FROM capability_map"
        )?;
        
        let capabilities = stmt.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
            ))
        })?;
        
        let mut result = Vec::new();
        for cap in capabilities {
            result.push(cap?);
        }

        Ok(result)
    }

    /// Check if capability exists
    pub fn has_capability(&self, capability: &str) -> Result<bool> {
        let caps = self.get_capability_map()?;
        Ok(caps.iter().any(|(c, _, _)| c == capability))
    }
}

/// Create default subsystem registry
pub fn create_registry() -> Result<SubsystemRegistry> {
    let path = std::env::current_dir()?.join("subsystems.db");
    SubsystemRegistry::open(&path)
}
