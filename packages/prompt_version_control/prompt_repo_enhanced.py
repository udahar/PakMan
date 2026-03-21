"""
Prompt Version Control - Git for Prompts

Enhanced version with proper branching, merging, and benchmarking.
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid
import hashlib


@dataclass
class PromptVersion:
    """A versioned prompt."""
    id: str
    prompt: str
    system: str
    model: str
    branch: str
    created_at: str
    parent_id: Optional[str]
    commit_message: str
    tags: List[str]
    metrics: Optional[Dict[str, Any]]
    config_hash: str  # For deduplication


class PromptRepo:
    """
    Git-like version control for prompts.
    
    Features:
    - Branching and merging
    - Commit history
    - Benchmark integration
    - Tagging
    - Diff comparison
    """
    
    def __init__(self, db_path: str = ".prompt_repo.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Commits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                system TEXT,
                model TEXT NOT NULL,
                branch TEXT NOT NULL,
                parent_id TEXT,
                commit_message TEXT,
                tags TEXT,
                metrics TEXT,
                config_hash TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES commits(id)
            )
        """)
        
        # Branches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                name TEXT PRIMARY KEY,
                head_commit_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (head_commit_id) REFERENCES commits(id)
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                name TEXT PRIMARY KEY,
                commit_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (commit_id) REFERENCES commits(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_branch ON commits(branch)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent ON commits(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON commits(config_hash)")
        
        self.conn.commit()
    
    def init(self, name: str = "main") -> str:
        """Initialize repo with first commit on main branch."""
        # Create main branch
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO branches (name, created_at) VALUES (?, ?)",
            (name, datetime.now().isoformat())
        )
        self.conn.commit()
        return name
    
    def commit(
        self,
        prompt: str,
        system: str = "",
        model: str = "qwen2.5:7b",
        message: str = "",
        branch: str = "main",
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new commit.
        
        Args:
            prompt: The prompt text
            system: System prompt
            model: Target model
            message: Commit message
            branch: Branch to commit to
            parent_id: Parent commit ID
            tags: Optional tags
        
        Returns:
            Commit ID
        """
        version_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()
        
        # Calculate config hash for deduplication
        config = f"{prompt}|{system}|{model}"
        config_hash = hashlib.sha256(config.encode()).hexdigest()[:16]
        
        # Check for duplicate
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM commits WHERE config_hash = ?",
            (config_hash,)
        )
        existing = cursor.fetchone()
        if existing:
            print(f"⚠️  Identical prompt exists: {existing['id']}")
            return existing['id']
        
        # Insert commit
        cursor.execute(
            """INSERT INTO commits 
               (id, prompt, system, model, branch, parent_id, commit_message, tags, metrics, config_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                version_id, prompt, system, model, branch, parent_id,
                message, json.dumps(tags or []), None, config_hash, created_at
            )
        )
        
        # Update branch head
        cursor.execute(
            "INSERT OR REPLACE INTO branches (name, head_commit_id, created_at) VALUES (?, ?, ?)",
            (branch, version_id, created_at)
        )
        
        self.conn.commit()
        return version_id
    
    def branch(self, name: str, from_commit: Optional[str] = None) -> str:
        """Create a new branch."""
        cursor = self.conn.cursor()
        
        # Get source commit
        if from_commit:
            cursor.execute("SELECT * FROM commits WHERE id = ?", (from_commit,))
            source = cursor.fetchone()
            if not source:
                raise ValueError(f"Commit not found: {from_commit}")
        else:
            # Use current branch head
            cursor.execute("SELECT head_commit_id FROM branches WHERE name = 'main'")
            source = cursor.fetchone()
            if not source:
                raise ValueError("No commits yet. Create one first.")
            from_commit = source['head_commit_id']
        
        # Create branch
        cursor.execute(
            "INSERT OR IGNORE INTO branches (name, head_commit_id, created_at) VALUES (?, ?, ?)",
            (name, from_commit, datetime.now().isoformat())
        )
        
        self.conn.commit()
        return name
    
    def checkout(self, version_id: str) -> PromptVersion:
        """Get a specific version."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM commits WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Version not found: {version_id}")
        
        return PromptVersion(
            id=row['id'],
            prompt=row['prompt'],
            system=row['system'],
            model=row['model'],
            branch=row['branch'],
            created_at=row['created_at'],
            parent_id=row['parent_id'],
            commit_message=row['commit_message'],
            tags=json.loads(row['tags']),
            metrics=json.loads(row['metrics']) if row['metrics'] else None,
            config_hash=row['config_hash'],
        )
    
    def log(self, branch: str = "main", limit: int = 20) -> List[PromptVersion]:
        """Get commit history for a branch."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM commits 
               WHERE branch = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (branch, limit)
        )
        
        return [
            PromptVersion(
                id=row['id'],
                prompt=row['prompt'],
                system=row['system'],
                model=row['model'],
                branch=row['branch'],
                created_at=row['created_at'],
                parent_id=row['parent_id'],
                commit_message=row['commit_message'],
                tags=json.loads(row['tags']),
                metrics=json.loads(row['metrics']) if row['metrics'] else None,
                config_hash=row['config_hash'],
            )
            for row in cursor.fetchall()
        ]
    
    def diff(self, id1: str, id2: str) -> Dict[str, Any]:
        """Compare two versions."""
        v1 = self.checkout(id1)
        v2 = self.checkout(id2)
        
        return {
            "id1": id1,
            "id2": id2,
            "prompt_changed": v1.prompt != v2.prompt,
            "system_changed": v1.system != v2.system,
            "model_changed": v1.model != v2.model,
            "prompt_diff": self._text_diff(v1.prompt, v2.prompt),
            "system_diff": self._text_diff(v1.system, v2.system),
            "metrics_diff": self._metrics_diff(v1.metrics, v2.metrics),
        }
    
    def _text_diff(self, text1: str, text2: str) -> Dict[str, Any]:
        """Simple text diff."""
        return {
            "added": len(text2) - len(text1),
            "changed": text1 != text2,
        }
    
    def _metrics_diff(self, m1: Optional[Dict], m2: Optional[Dict]) -> Dict[str, Any]:
        """Compare metrics."""
        if not m1 or not m2:
            return {"comparable": False}
        
        return {
            "latency_change": m2.get("latency_ms", 0) - m1.get("latency_ms", 0),
            "quality_change": m2.get("quality_score", 0) - m1.get("quality_score", 0),
        }
    
    def tag(self, name: str, commit_id: str) -> str:
        """Create a tag."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO tags (name, commit_id, created_at) VALUES (?, ?, ?)",
            (name, commit_id, datetime.now().isoformat())
        )
        self.conn.commit()
        return name
    
    def update_metrics(self, commit_id: str, metrics: Dict[str, Any]):
        """Update metrics for a commit."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE commits SET metrics = ? WHERE id = ?",
            (json.dumps(metrics), commit_id)
        )
        self.conn.commit()
    
    def get_branch(self, name: str) -> Optional[str]:
        """Get head commit of a branch."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT head_commit_id FROM branches WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row['head_commit_id'] if row else None
    
    def list_branches(self) -> List[str]:
        """List all branches."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM branches")
        return [row['name'] for row in cursor.fetchall()]
    
    def list_tags(self) -> List[str]:
        """List all tags."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM tags")
        return [row['name'] for row in cursor.fetchall()]
    
    def merge(self, source_branch: str, target_branch: str = "main") -> str:
        """
        Merge source branch into target branch.
        
        Creates a new commit on target branch with same prompt.
        """
        source_head = self.get_branch(source_branch)
        if not source_head:
            raise ValueError(f"Branch not found: {source_branch}")
        
        source_commit = self.checkout(source_head)
        
        # Create new commit on target branch
        new_id = self.commit(
            prompt=source_commit.prompt,
            system=source_commit.system,
            model=source_commit.model,
            message=f"Merged from {source_branch}",
            branch=target_branch,
            parent_id=self.get_branch(target_branch),
            tags=source_commit.tags,
        )
        
        return new_id
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        cursor = self.conn.cursor()
        
        # Count commits
        cursor.execute("SELECT COUNT(*) FROM commits")
        total_commits = cursor.fetchone()[0]
        
        # Count branches
        cursor.execute("SELECT COUNT(*) FROM branches")
        total_branches = cursor.fetchone()[0]
        
        # Count tags
        cursor.execute("SELECT COUNT(*) FROM tags")
        total_tags = cursor.fetchone()[0]
        
        # Get models used
        cursor.execute("SELECT DISTINCT model FROM commits")
        models = [row['model'] for row in cursor.fetchall()]
        
        return {
            "total_commits": total_commits,
            "total_branches": total_branches,
            "total_tags": total_tags,
            "models_used": models,
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()
