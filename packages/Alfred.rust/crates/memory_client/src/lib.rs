//! Memory Client - Wrapper for Postgres and Qdrant
//!
//! Provides a unified interface for:
//! - Structured storage (Postgres)
//! - Vector search (Qdrant)
//! - Key-value cache

use anyhow::Result;
use chrono::{DateTime, Local};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Memory entry for storage
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MemoryEntry {
    pub key: String,
    pub value: serde_json::Value,
    pub metadata: MemoryMetadata,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MemoryMetadata {
    pub created_at: String,
    pub updated_at: String,
    pub tags: Vec<String>,
    pub ttl_seconds: Option<u64>,
}

/// Memory client trait
pub trait Memory {
    /// Store a value
    fn store(&self, key: &str, value: serde_json::Value) -> Result<()>;
    
    /// Retrieve a value
    fn recall(&self, key: &str) -> Result<Option<serde_json::Value>>;
    
    /// Search by query
    fn search(&self, query: &str) -> Result<Vec<MemoryEntry>>;
    
    /// Delete a value
    fn delete(&self, key: &str) -> Result<()>;
}

/// In-memory storage (fallback when Postgres/Qdrant unavailable)
pub struct InMemoryStorage {
    data: std::sync::RwLock<HashMap<String, MemoryEntry>>,
}

impl InMemoryStorage {
    pub fn new() -> Self {
        Self {
            data: std::sync::RwLock::new(HashMap::new()),
        }
    }
}

impl Default for InMemoryStorage {
    fn default() -> Self {
        Self::new()
    }
}

impl Memory for InMemoryStorage {
    fn store(&self, key: &str, value: serde_json::Value) -> Result<()> {
        let now = Local::now().to_rfc3339();
        let entry = MemoryEntry {
            key: key.to_string(),
            value,
            metadata: MemoryMetadata {
                created_at: now.clone(),
                updated_at: now,
                tags: vec![],
                ttl_seconds: None,
            },
        };
        
        let mut data = self.data.write().unwrap();
        data.insert(key.to_string(), entry);
        Ok(())
    }

    fn recall(&self, key: &str) -> Result<Option<serde_json::Value>> {
        let data = self.data.read().unwrap();
        Ok(data.get(key).map(|e| e.value.clone()))
    }

    fn search(&self, query: &str) -> Result<Vec<MemoryEntry>> {
        let data = self.data.read().unwrap();
        let query_lower = query.to_lowercase();
        
        let results: Vec<MemoryEntry> = data
            .values()
            .filter(|entry| {
                entry.key.to_lowercase().contains(&query_lower) ||
                entry.value.to_string().to_lowercase().contains(&query_lower)
            })
            .cloned()
            .collect();
        
        Ok(results)
    }

    fn delete(&self, key: &str) -> Result<()> {
        let mut data = self.data.write().unwrap();
        data.remove(key);
        Ok(())
    }
}

/// Postgres client for structured storage
pub struct PostgresClient {
    #[allow(dead_code)]
    connection_string: String,
}

impl PostgresClient {
    pub fn new(connection_string: &str) -> Self {
        Self {
            connection_string: connection_string.to_string(),
        }
    }

    pub fn store_context(&self, ticket_id: &str, context: &serde_json::Value) -> Result<()> {
        // In production, this would execute:
        // INSERT INTO ticket_context (ticket_id, context, created_at)
        // VALUES ($1, $2, NOW())
        // ON CONFLICT (ticket_id) DO UPDATE SET context = $2, updated_at = NOW()
        
        eprintln!("Postgres: Storing context for ticket {}", ticket_id);
        Ok(())
    }

    pub fn get_context(&self, ticket_id: &str) -> Result<Option<serde_json::Value>> {
        // In production:
        // SELECT context FROM ticket_context WHERE ticket_id = $1
        
        eprintln!("Postgres: Getting context for ticket {}", ticket_id);
        Ok(None)
    }

    pub fn store_decision(&self, decision: &serde_json::Value) -> Result<()> {
        eprintln!("Postgres: Storing decision");
        Ok(())
    }

    pub fn get_history(&self, ticket_id: &str, limit: i32) -> Result<Vec<serde_json::Value>> {
        eprintln!("Postgres: Getting history for ticket {}", ticket_id);
        Ok(vec![])
    }
}

/// Qdrant client for vector storage
pub struct QdrantClient {
    #[allow(dead_code)]
    url: String,
}

impl QdrantClient {
    pub fn new(url: &str) -> Self {
        Self {
            url: url.to_string(),
        }
    }

    pub fn store_embedding(&self, collection: &str, id: &str, vector: &[f32], payload: &serde_json::Value) -> Result<()> {
        eprintln!("Qdrant: Storing embedding in collection {}", collection);
        Ok(())
    }

    pub fn search_similar(&self, collection: &str, vector: &[f32], limit: usize) -> Result<Vec<(String, f32, serde_json::Value)>> {
        eprintln!("Qdrant: Searching similar in collection {}", collection);
        Ok(vec![])
    }

    pub fn create_embedding(&self, text: &str) -> Result<Vec<f32>> {
        // In production, call Ollama or other embedding model
        // For now, return a dummy vector
        Ok(vec![0.0; 384])
    }
}

/// Unified memory interface
pub struct MemoryClient {
    postgres: Option<PostgresClient>,
    qdrant: Option<QdrantClient>,
    fallback: InMemoryStorage,
}

impl MemoryClient {
    pub fn new(postgres_url: Option<&str>, qdrant_url: Option<&str>) -> Self {
        Self {
            postgres: postgres_url.map(PostgresClient::new),
            qdrant: qdrant_url.map(QdrantClient::new),
            fallback: InMemoryStorage::new(),
        }
    }

    /// Store structured data
    pub fn store(&self, key: &str, value: serde_json::Value) -> Result<()> {
        if let Some(pg) = &self.postgres {
            // Try postgres first
            if let Err(e) = pg.store_context(key, &value) {
                eprintln!("Postgres failed, using fallback: {}", e);
            } else {
                return Ok(());
            }
        }
        
        // Fallback to in-memory
        self.fallback.store(key, value)
    }

    /// Recall structured data
    pub fn recall(&self, key: &str) -> Result<Option<serde_json::Value>> {
        if let Some(pg) = &self.postgres {
            if let Ok(Some(value)) = pg.get_context(key) {
                return Ok(Some(value));
            }
        }
        
        self.fallback.recall(key)
    }

    /// Search memory
    pub fn search(&self, query: &str) -> Result<Vec<MemoryEntry>> {
        self.fallback.search(query)
    }

    /// Store embedding with payload
    pub fn store_embedding(&self, collection: &str, id: &str, text: &str, metadata: serde_json::Value) -> Result<()> {
        if let Some(qdrant) = &self.qdrant {
            let vector = qdrant.create_embedding(text)?;
            qdrant.store_embedding(collection, id, &vector, &metadata)?;
        }
        
        // Also store in fallback
        self.fallback.store(id, metadata)?;
        Ok(())
    }

    /// Search by similarity
    pub fn search_similar(&self, collection: &str, query: &str, limit: usize) -> Result<Vec<(String, f32, serde_json::Value)>> {
        if let Some(qdrant) = &self.qdrant {
            let vector = qdrant.create_embedding(query)?;
            return qdrant.search_similar(collection, &vector, limit);
        }
        
        // Fallback to text search
        let entries = self.fallback.search(query)?;
        Ok(entries.into_iter().map(|e| (e.key, 1.0, e.value)).collect())
    }

    /// Store ticket context (shared context per ticket)
    pub fn store_ticket_context(&self, ticket_id: &str, model: &str, content: &str) -> Result<()> {
        let context = serde_json::json!({
            "ticket_id": ticket_id,
            "model": model,
            "content": content,
            "timestamp": Local::now().to_rfc3339()
        });

        self.store(&format!("ticket:{}", ticket_id), context)
    }

    /// Get ticket context (all models)
    pub fn get_ticket_context(&self, ticket_id: &str) -> Result<Vec<serde_json::Value>> {
        if let Some(context) = self.recall(&format!("ticket:{}", ticket_id))? {
            Ok(vec![context])
        } else {
            Ok(vec![])
        }
    }
}

impl Default for MemoryClient {
    fn default() -> Self {
        Self::new(None, None)
    }
}

/// Create a memory client from environment
pub fn create_memory_client() -> MemoryClient {
    let postgres_url = std::env::var("DATABASE_URL").ok();
    let qdrant_url = std::env::var("QDRANT_URL").ok();
    
    MemoryClient::new(postgres_url.as_deref(), qdrant_url.as_deref())
}
