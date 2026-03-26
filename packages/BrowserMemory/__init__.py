"""
Browser Memory - Personal Knowledge Graph from Web Browsing.

A module that turns browser history and scraped content into a queryable
knowledge graph with vector search and relationship tracking.

Features:
- Vector search for semantic similarity
- Graph relationships (link structure, research paths)
- SQLite persistence
- Tag-based organization
- Research path discovery

Usage:
    from browser_memory import BrowserMemory
    
    bm = BrowserMemory()
    
    # Add pages
    bm.add_page(
        "https://example.com",
        "Page Title",
        "Page content..."
    )
    
    # Query
    results = bm.search("authentication")
    path = bm.research_path("OAuth")
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BrowserMemoryError(Exception):
    """Base exception for browser memory operations."""
    pass


class StorageError(BrowserMemoryError):
    """Raised when storage operations fail."""
    pass


@dataclass
class ScrapedPage:
    """A scraped web page."""
    url: str
    title: str
    content: str
    scraped_at: datetime = field(default_factory=datetime.now)
    time_spent: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entity_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "time_spent": self.time_spent,
            "tags": self.tags,
            "metadata": self.metadata,
            "entity_id": self.entity_id,
        }


class BrowserMemory:
    """
    Personal knowledge graph from web browsing.
    
    Combines:
    - Vector search (find similar pages)
    - Graph relationships (link structure, research paths)
    - SQLite persistence (save/load)
    """
    
    DEFAULT_DB_PATH = "browser_memory.db"
    
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        memory_graph_url: Optional[str] = None,
        enable_memory_graph: bool = True
    ) -> None:
        self.db_path = db_path
        self.memory_graph_url = memory_graph_url or "http://localhost:6333"
        self._memory_graph = None
        
        if enable_memory_graph:
            try:
                from memory_graph import MemoryGraph
                self._memory_graph = MemoryGraph(qdrant_url=self.memory_graph_url)
                logger.info("MemoryGraph integration enabled")
            except ImportError:
                logger.warning("MemoryGraph not available, running in SQLite-only mode")
            except Exception as e:
                logger.warning("Failed to initialize MemoryGraph: %s", e)
        
        self.pages: Dict[str, ScrapedPage] = {}
        
        self._init_db()
        
        if db_path != ":memory:":
            self._load_from_db()
        
        logger.info("BrowserMemory initialized (db=%s, pages=%d)",
                    db_path, len(self.pages))
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    scraped_at TEXT,
                    time_spent INTEGER,
                    tags TEXT,
                    metadata TEXT,
                    entity_id TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TEXT,
                    topic TEXT,
                    page_urls TEXT
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pages_scraped_at
                ON pages(scraped_at)
            """)
            
            conn.commit()
            conn.close()
            
            logger.debug("Database initialized at %s", self.db_path)
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize database: {e}") from e
    
    def _load_from_db(self) -> None:
        """Load pages from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM pages")
            for row in cursor.fetchall():
                page = ScrapedPage(
                    url=row[0],
                    title=row[1],
                    content=row[2],
                    scraped_at=datetime.fromisoformat(row[3]) if row[3] else None,
                    time_spent=row[4] or 0,
                    tags=json.loads(row[5]) if row[5] else [],
                    metadata=json.loads(row[6]) if row[6] else {},
                    entity_id=row[7]
                )
                self.pages[page.url] = page
            
            conn.close()
            
            logger.debug("Loaded %d pages from database", len(self.pages))
        except sqlite3.Error as e:
            logger.error("Failed to load from database: %s", e)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse stored data: %s", e)
    
    def _save_page(self, page: ScrapedPage) -> None:
        """Save page to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO pages
                (url, title, content, scraped_at, time_spent, tags, metadata, entity_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page.url,
                page.title,
                page.content,
                page.scraped_at.isoformat() if page.scraped_at else None,
                page.time_spent,
                json.dumps(page.tags),
                json.dumps(page.metadata),
                page.entity_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug("Saved page: %s", page.url)
        except sqlite3.Error as e:
            logger.error("Failed to save page: %s", e)
    
    def add_page(
        self,
        url: str,
        title: str,
        content: str,
        time_spent: int = 0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a scraped page to memory.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content (text)
            time_spent: Time spent on page (seconds)
            tags: Optional tags
            metadata: Optional metadata
        
        Returns:
            Entity ID in graph (or generated ID if graph not available)
        """
        page = ScrapedPage(
            url=url,
            title=title,
            content=content,
            time_spent=time_spent,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        if self._memory_graph:
            try:
                entity_id = self._memory_graph.add_entity(
                    type="page",
                    name=title,
                    content=content,
                    metadata={
                        "url": url,
                        "scraped_at": datetime.now().isoformat(),
                        "time_spent": time_spent,
                        "tags": page.tags
                    }
                )
                page.entity_id = entity_id
                
                for tag in page.tags:
                    tag_id = self._memory_graph.add_entity(
                        type="tag",
                        name=tag,
                        content=f"Tag: {tag}"
                    )
                    self._memory_graph.add_relationship(entity_id, tag_id, "tagged_with")
            except Exception as e:
                logger.warning("Failed to add to memory graph: %s", e)
        
        self.pages[url] = page
        self._save_page(page)
        
        logger.info("Added page: %s", url)
        
        return page.entity_id or url
    
    def add_relationship(
        self,
        from_url: str,
        to_url: str,
        rel_type: str
    ) -> None:
        """
        Add relationship between pages.
        
        Args:
            from_url: Source page URL
            to_url: Target page URL
            rel_type: Relationship type (links_to, visited_before, related_to, etc.)
        """
        from_page = self.pages.get(from_url)
        to_page = self.pages.get(to_url)
        
        if not from_page or not to_page:
            logger.warning("One or both pages not found: %s, %s", from_url, to_url)
            return
        
        if self._memory_graph and from_page.entity_id and to_page.entity_id:
            try:
                self._memory_graph.add_relationship(
                    from_page.entity_id,
                    to_page.entity_id,
                    rel_type
                )
            except Exception as e:
                logger.warning("Failed to add relationship: %s", e)
        
        logger.debug("Added relationship: %s --[%s]--> %s", from_url, rel_type, to_url)
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search pages by semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of matching pages
        """
        if self._memory_graph:
            try:
                results = self._memory_graph.similar_to(query, top_k=top_k, filter_type="page")
                
                enriched = []
                for r in results:
                    entity_id = r.get("entity_id")
                    
                    for page in self.pages.values():
                        if page.entity_id == entity_id:
                            enriched.append({
                                **r,
                                "url": page.url,
                                "title": page.title,
                                "scraped_at": page.scraped_at,
                                "time_spent": page.time_spent,
                                "tags": page.tags
                            })
                            break
                
                return enriched
            except Exception as e:
                logger.warning("Memory graph search failed: %s", e)
        
        return self._text_search(query, top_k)
    
    def _text_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Simple text-based search fallback."""
        query_lower = query.lower()
        results = []
        
        for page in self.pages.values():
            score = 0
            if query_lower in page.title.lower():
                score += 2
            if query_lower in page.content.lower():
                score += 1
            if any(query_lower in tag.lower() for tag in page.tags):
                score += 3
            
            if score > 0:
                results.append({
                    "url": page.url,
                    "title": page.title,
                    "content": page.content[:200],
                    "score": score,
                    "tags": page.tags,
                    "scraped_at": page.scraped_at
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def research_path(
        self,
        topic: str,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get research path on a topic.
        
        Args:
            topic: Research topic
            max_depth: How many hops to follow
        
        Returns:
            Research path with pages and relationships
        """
        if self._memory_graph:
            try:
                results = self._memory_graph.hybrid_query(
                    text=topic,
                    relationships=["links_to", "visited_before", "related_to", "tagged_with"],
                    max_depth=max_depth,
                    top_k=5
                )
                
                path = {
                    "topic": topic,
                    "pages": [],
                    "tags": [],
                    "total": results["total_results"]
                }
                
                for item in results.get("similar", []) + results.get("expanded", []):
                    entity_type = item.get("type")
                    
                    if entity_type == "page":
                        for page in self.pages.values():
                            if page.entity_id == item.get("entity_id"):
                                path["pages"].append({
                                    "url": page.url,
                                    "title": page.title,
                                    "scraped_at": page.scraped_at,
                                    "relevance": item.get("score", 0)
                                })
                                break
                    elif entity_type == "tag":
                        path["tags"].append(item.get("name"))
                
                return path
            except Exception as e:
                logger.warning("Memory graph research failed: %s", e)
        
        return {
            "topic": topic,
            "pages": [],
            "tags": [],
            "total": 0,
            "message": "Memory graph not available"
        }
    
    def get_linked_pages(self, url: str) -> List[Dict[str, Any]]:
        """
        Get pages linked from/to a specific page.
        
        Args:
            url: Page URL
        
        Returns:
            List of linked pages
        """
        page = self.pages.get(url)
        if not page:
            return []
        
        if self._memory_graph and page.entity_id:
            try:
                relationships = self._memory_graph.get_relationships(
                    page.entity_id,
                    rel_types=["links_to", "visited_before", "related_to"]
                )
                
                linked = []
                for rel in relationships:
                    other_id = rel.get("to") if rel.get("from") == page.entity_id else rel.get("from")
                    
                    for p in self.pages.values():
                        if p.entity_id == other_id:
                            linked.append({
                                "url": p.url,
                                "title": p.title,
                                "relationship": rel.get("type"),
                                "direction": "outgoing" if rel.get("from") == page.entity_id else "incoming"
                            })
                            break
                
                return linked
            except Exception as e:
                logger.warning("Failed to get linked pages: %s", e)
        
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        all_tags: Set[str] = set()
        for page in self.pages.values():
            all_tags.update(page.tags)
        
        stats = {
            "total_pages": len(self.pages),
            "total_tags": len(all_tags),
            "database": self.db_path
        }
        
        if self._memory_graph:
            try:
                graph_stats = self._memory_graph.get_stats()
                stats["graph_entities"] = graph_stats.get("entities", 0)
                stats["graph_relationships"] = graph_stats.get("relationships", 0)
            except Exception as e:
                logger.debug("Failed to get graph stats: %s", e)
        
        return stats
    
    def export(self, format: str = "json") -> str:
        """Export all data."""
        if format == "json":
            data = {
                "pages": [p.to_dict() for p in self.pages.values()],
            }
            
            if self._memory_graph:
                data["graph"] = self._memory_graph.export_graph(format="json")
            
            return json.dumps(data, indent=2, default=str)
        
        return ""
    
    def close(self) -> None:
        """Cleanup resources."""
        logger.info("BrowserMemory closed")
        pass


_memory: Optional[BrowserMemory] = None


def get_memory(
    db_path: str = BrowserMemory.DEFAULT_DB_PATH,
    memory_graph_url: Optional[str] = None
) -> BrowserMemory:
    """Get or create browser memory instance."""
    global _memory
    if _memory is None:
        _memory = BrowserMemory(db_path=db_path, memory_graph_url=memory_graph_url)
    return _memory


def add_page(*args: Any, **kwargs: Any) -> str:
    """Add a page to memory."""
    return get_memory().add_page(*args, **kwargs)


def search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Search pages."""
    return get_memory().search(query, top_k)


def research_path(topic: str, max_depth: int = 5) -> Dict[str, Any]:
    """Get research path."""
    return get_memory().research_path(topic, max_depth)


def get_stats() -> Dict[str, Any]:
    """Get stats."""
    return get_memory().get_stats()
