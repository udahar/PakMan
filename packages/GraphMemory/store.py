"""
GraphMemory - store.py
SQLite-backed graph store. Persists nodes and edges, enables path queries.
Zero external dependencies.
"""
import json
import sqlite3
from typing import List, Optional
from .models import Edge, Node


class GraphStore:
    """
    Persistent knowledge graph backed by SQLite.

    Supports:
    - Upsert nodes and edges
    - Find neighbors (1-hop) of any entity
    - Path queries (BFS, 2–3 hops)
    - Full-text node search
    """

    def __init__(self, db_path: str = "graph_memory.db"):
        self.db_path = db_path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id          TEXT PRIMARY KEY,
                    label       TEXT NOT NULL,
                    kind        TEXT,
                    properties  TEXT,
                    created_at  TEXT,
                    mentions    INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id          TEXT PRIMARY KEY,
                    src_id      TEXT NOT NULL,
                    rel         TEXT NOT NULL,
                    dst_id      TEXT NOT NULL,
                    weight      REAL DEFAULT 1.0,
                    created_at  TEXT,
                    context     TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_node_label ON nodes(label)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_src ON edges(src_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_dst ON edges(dst_id)")
            conn.commit()

    # ── Upsert ────────────────────────────────────────────────────────────────

    def upsert_node(self, node: Node) -> None:
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id, mentions FROM nodes WHERE label=? COLLATE NOCASE", (node.label,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE nodes SET mentions=mentions+1, kind=? WHERE id=?",
                    (node.kind, existing["id"])
                )
            else:
                conn.execute("""
                    INSERT INTO nodes (id, label, kind, properties, created_at, mentions)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (node.id, node.label, node.kind,
                      json.dumps(node.properties), node.created_at, node.mentions))
            conn.commit()

    def upsert_edge(self, edge: Edge) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO edges (id, src_id, rel, dst_id, weight, created_at, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (edge.id, edge.src_id, edge.rel, edge.dst_id,
                  edge.weight, edge.created_at, edge.context))
            conn.commit()

    def bulk_upsert(self, nodes: List[Node], edges: List[Edge]) -> None:
        for n in nodes:
            self.upsert_node(n)
        for e in edges:
            self.upsert_edge(e)

    # ── Queries ───────────────────────────────────────────────────────────────

    def find_node(self, label: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE label=? COLLATE NOCASE", (label,)
            ).fetchone()
            return dict(row) if row else None

    def search_nodes(self, query: str, kind: str = None, limit: int = 20) -> List[dict]:
        """Full-text node search by label substring."""
        with self._conn() as conn:
            sql = "SELECT * FROM nodes WHERE label LIKE ? "
            params = [f"%{query}%"]
            if kind:
                sql += "AND kind=? "
                params.append(kind)
            sql += "ORDER BY mentions DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def neighbors(self, label: str) -> List[dict]:
        """Return all nodes connected to the given label (1-hop)."""
        node = self.find_node(label)
        if not node:
            return []
        nid = node["id"]
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT n.label, n.kind, e.rel, 'outgoing' as direction
                FROM edges e JOIN nodes n ON n.id = e.dst_id
                WHERE e.src_id=?
                UNION
                SELECT n.label, n.kind, e.rel, 'incoming' as direction
                FROM edges e JOIN nodes n ON n.id = e.src_id
                WHERE e.dst_id=?
            """, (nid, nid)).fetchall()
            return [dict(r) for r in rows]

    def path(self, src_label: str, dst_label: str, max_hops: int = 3) -> List[List[str]]:
        """BFS path search between two nodes. Returns list of label paths."""
        src = self.find_node(src_label)
        dst = self.find_node(dst_label)
        if not src or not dst:
            return []

        # BFS
        queue = [[src["id"]]]
        visited = {src["id"]}
        found = []

        while queue and max_hops > 0:
            next_queue = []
            for path in queue:
                current = path[-1]
                for nbr in self.neighbors_by_id(current):
                    nid = nbr["id"]
                    if nid in visited:
                        continue
                    new_path = path + [nid]
                    if nid == dst["id"]:
                        found.append(new_path)
                    else:
                        next_queue.append(new_path)
                    visited.add(nid)
            queue = next_queue
            max_hops -= 1

        # Resolve IDs → labels
        with self._conn() as conn:
            label_map = {
                r["id"]: r["label"]
                for r in conn.execute("SELECT id, label FROM nodes").fetchall()
            }
        return [[label_map.get(nid, nid) for nid in p] for p in found]

    def neighbors_by_id(self, node_id: str) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT n.id, n.label FROM edges e
                JOIN nodes n ON n.id=e.dst_id WHERE e.src_id=?
                UNION
                SELECT n.id, n.label FROM edges e
                JOIN nodes n ON n.id=e.src_id WHERE e.dst_id=?
            """, (node_id, node_id)).fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._conn() as conn:
            nc = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            ec = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            top = conn.execute(
                "SELECT label, mentions FROM nodes ORDER BY mentions DESC LIMIT 5"
            ).fetchall()
            return {
                "nodes": nc, "edges": ec,
                "top_entities": [dict(r) for r in top],
            }
