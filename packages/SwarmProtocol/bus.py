"""
SwarmProtocol - bus.py
SQLite-backed event bus for inter-agent messaging.
Zero external dependencies. For multi-process use, set bus_path to a shared path.
"""
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional
from .models import SwarmMessage, MessageType


class SwarmBus:
    """
    Lightweight SQLite pub/sub event bus for SwarmProtocol.

    Each agent connects to the same bus_path (a .db file).
    Messages are stored in a queue table and polled by recipients.

    Usage:
        bus = SwarmBus()
        bus.publish(msg)
        msgs = bus.poll("my_agent_id", timeout=5.0)
    """

    def __init__(self, bus_path: str = ":memory:"):
        self.bus_path = bus_path
        self._local = threading.local()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.bus_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_messages (
                id          TEXT PRIMARY KEY,
                recipient   TEXT NOT NULL,
                sender      TEXT NOT NULL,
                msg_type    TEXT NOT NULL,
                payload     TEXT,
                ref_id      TEXT,
                timestamp   TEXT,
                ttl         INTEGER DEFAULT 300,
                delivered   INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_registry (
                agent_id    TEXT PRIMARY KEY,
                name        TEXT,
                skills      TEXT,
                status      TEXT DEFAULT 'idle',
                last_seen   TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipient ON swarm_messages(recipient, delivered)")
        conn.commit()

    # ── Publishing ────────────────────────────────────────────────────────────

    def publish(self, msg: SwarmMessage) -> str:
        """Push a message onto the bus. Returns the message id."""
        conn = self._conn()
        conn.execute("""
            INSERT OR REPLACE INTO swarm_messages
            (id, recipient, sender, msg_type, payload, ref_id, timestamp, ttl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg.id, msg.recipient, msg.sender, msg.msg_type.value,
            json.dumps(msg.payload), msg.ref_id, msg.timestamp, msg.ttl
        ))
        conn.commit()
        return msg.id

    # ── Polling ───────────────────────────────────────────────────────────────

    def poll(
        self,
        agent_id: str,
        timeout: float = 0.0,
        include_broadcast: bool = True,
    ) -> List[SwarmMessage]:
        """
        Retrieve undelivered messages for an agent.
        If timeout > 0, waits up to that many seconds for at least one message.
        """
        deadline = time.monotonic() + timeout
        while True:
            msgs = self._fetch(agent_id, include_broadcast)
            if msgs or time.monotonic() >= deadline:
                return msgs
            time.sleep(0.1)

    def _fetch(self, agent_id: str, include_broadcast: bool) -> List[SwarmMessage]:
        conn = self._conn()
        recipients = [agent_id]
        if include_broadcast:
            recipients.append("broadcast")

        placeholders = ",".join("?" * len(recipients))
        rows = conn.execute(f"""
            SELECT * FROM swarm_messages
            WHERE recipient IN ({placeholders})
              AND delivered = 0
            ORDER BY timestamp ASC
        """, recipients).fetchall()

        msgs = []
        ids = []
        for row in rows:
            d = dict(row)
            d["payload"] = json.loads(d.get("payload") or "{}")
            d["type"] = d.pop("msg_type")
            msgs.append(SwarmMessage.from_dict(d))
            ids.append(row["id"])

        if ids:
            conn.executemany(
                "UPDATE swarm_messages SET delivered=1 WHERE id=?",
                [(i,) for i in ids]
            )
            conn.commit()

        return msgs

    # ── Registry ──────────────────────────────────────────────────────────────

    def register_agent(self, capability) -> None:
        """Announce an agent's capabilities to the bus."""
        from datetime import datetime
        conn = self._conn()
        conn.execute("""
            INSERT OR REPLACE INTO swarm_registry
            (agent_id, name, skills, status, last_seen)
            VALUES (?, ?, ?, ?, ?)
        """, (
            capability.agent_id, capability.name,
            json.dumps(capability.skills),
            capability.status.value,
            datetime.utcnow().isoformat()
        ))
        conn.commit()

    def find_agents_with_skill(self, skill: str) -> List[dict]:
        """Return all idle agents that advertise a given skill."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM swarm_registry WHERE status='idle'"
        ).fetchall()
        return [
            dict(r) for r in rows
            if skill.lower() in json.loads(r["skills"] or "[]")
        ]

    def heartbeat(self, agent_id: str, status: str = "idle") -> None:
        from datetime import datetime
        conn = self._conn()
        conn.execute(
            "UPDATE swarm_registry SET status=?, last_seen=? WHERE agent_id=?",
            (status, datetime.utcnow().isoformat(), agent_id)
        )
        conn.commit()
