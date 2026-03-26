"""
AgentBazaar - registry.py
Stores agent capability manifests and provides skill-based lookups.
SQLite-backed, thread-safe, zero dependencies.
"""
import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


AGENT_TTL_SECONDS = 60  # Agents are considered stale after 60s without heartbeat


class AgentRegistry:
    """
    SQLite-backed registry of agent capabilities.

    Agents self-register by posting a manifest. Other agents/brokers
    query for agents that advertise specific skills.
    """

    def __init__(self, db_path: str = "agent_bazaar.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id    TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    skills      TEXT NOT NULL,      -- JSON list
                    endpoint    TEXT,               -- Optional HTTP URL
                    metadata    TEXT,               -- JSON dict of extras
                    status      TEXT DEFAULT 'idle',
                    last_seen   TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON agents(status)"
            )
            conn.commit()

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        agent_id: str,
        name: str,
        skills: List[str],
        endpoint: str = "",
        metadata: Dict[str, Any] = None,
        status: str = "idle",
    ) -> None:
        """
        Register or update an agent's capability manifest.

        Args:
            agent_id: Unique identifier for the agent.
            name:     Human-readable name (e.g., "CoderAgent").
            skills:   List of capability tags, e.g. ["python", "code_review"].
            endpoint: Optional HTTP URL if the agent exposes an API.
            metadata: Any extra key/value info.
            status:   "idle" | "busy" | "offline"
        """
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO agents
                (agent_id, name, skills, endpoint, metadata, status, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, name,
                json.dumps([s.lower() for s in skills]),
                endpoint or "",
                json.dumps(metadata or {}),
                status,
                datetime.utcnow().isoformat(),
            ))
            conn.commit()

    def heartbeat(self, agent_id: str, status: str = "idle") -> None:
        """Keep an agent alive by updating its last_seen timestamp."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE agents SET last_seen=?, status=? WHERE agent_id=?",
                (datetime.utcnow().isoformat(), status, agent_id)
            )
            conn.commit()

    def deregister(self, agent_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM agents WHERE agent_id=?", (agent_id,))
            conn.commit()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def find_by_skill(self, skill: str, only_idle: bool = True) -> List[dict]:
        """
        Return all agents that advertise a specific skill.

        Args:
            skill:     Skill tag to search for (case-insensitive).
            only_idle: If True, only return agents with status='idle'.
        """
        with self._conn() as conn:
            sql = "SELECT * FROM agents WHERE skills LIKE ?"
            params = [f'%"{skill.lower()}"%']
            if only_idle:
                sql += " AND status='idle'"
            sql += " ORDER BY last_seen DESC"
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def find_best(self, skill: str) -> Optional[dict]:
        """Return the single best (most recently seen, idle) agent for a skill."""
        results = self.find_by_skill(skill, only_idle=True)
        return results[0] if results else None

    def list_all(self, include_offline: bool = False) -> List[dict]:
        with self._conn() as conn:
            sql = "SELECT * FROM agents"
            if not include_offline:
                sql += " WHERE status != 'offline'"
            sql += " ORDER BY last_seen DESC"
            return [self._row_to_dict(r) for r in conn.execute(sql).fetchall()]

    def all_skills(self) -> List[str]:
        """Return a deduplicated list of all advertised skills."""
        with self._conn() as conn:
            rows = conn.execute("SELECT skills FROM agents").fetchall()
        skills = set()
        for row in rows:
            for s in json.loads(row["skills"] or "[]"):
                skills.add(s)
        return sorted(skills)

    def get(self, agent_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE agent_id=?", (agent_id,)
            ).fetchone()
            return self._row_to_dict(row) if row else None

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        d["skills"] = json.loads(d.get("skills") or "[]")
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d
