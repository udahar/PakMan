"""
Browser Memory - Personal Knowledge Graph from Web Browsing

Standalone module that turns browser history + scraped content into a
queryable knowledge graph with vector search + relationships.

Usage:
    from browser_memory import BrowserMemory
    
    bm = BrowserMemory()
    
    # Add pages
    bm.add_page("https://example.com", "Page Title", "Page content...")
    
    # Query
    results = bm.search("authentication")
    path = bm.research_path("OAuth")
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from memory_graph import MemoryGraph
except ImportError:
    # Fallback if memory_graph not available
    MemoryGraph = None
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import sqlite3
from dataclasses import dataclass, field


@dataclass
class ScrapedPage:
    """A scraped web page"""
    url: str
    title: str
    content: str
    scraped_at: datetime = field(default_factory=datetime.now)
    time_spent: int = 0  # seconds
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entity_id: Optional[str] = None


class BrowserMemory:
    """
    Personal knowledge graph from web browsing.
    
    Combines:
    - Vector search (find similar pages)
    - Graph relationships (link structure, research paths)
    - SQLite persistence (save/load)
    """
    
    def __init__(
        self,
        db_path: str = "browser_memory.db",
        qdrant_url: str = "http://localhost:6333"
    ):
        self.db_path = db_path
        self.qdrant_url = qdrant_url
        
        # Initialize memory graph
        if MemoryGraph:
            self.mg = MemoryGraph(qdrant_url=qdrant_url)
        else:
            self.mg = None
        
        # Page cache
        self.pages: Dict[str, ScrapedPage] = {}
        
        # Initialize database
        self._init_db()
        
        # Load existing data (only if not :memory:)
        if db_path != ":memory:":
            self._load_from_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pages table
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
        
        # Research sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                started_at TEXT,
                topic TEXT,
                page_urls TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """Load pages from database"""
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
    
    def _save_page(self, page: ScrapedPage):
        """Save page to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO pages
            (url, title, content, scraped_at, time_spent, tags, metadata, entity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            page.url, page.title, page.content,
            page.scraped_at.isoformat() if page.scraped_at else None,
            page.time_spent,
            json.dumps(page.tags),
            json.dumps(page.metadata),
            page.entity_id
        ))
        
        conn.commit()
        conn.close()
    
    def add_page(
        self,
        url: str,
        title: str,
        content: str,
        time_spent: int = 0,
        tags: List[str] = None,
        metadata: Dict = None
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
            Entity ID in graph
        """
        # Create page object
        page = ScrapedPage(
            url=url,
            title=title,
            content=content,
            time_spent=time_spent,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Add to memory graph
        entity_id = self.mg.add_entity(
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
        
        # Add tags as entities
        for tag in page.tags:
            tag_id = self.mg.add_entity(
                type="tag",
                name=tag,
                content=f"Tag: {tag}"
            )
            self.mg.add_relationship(entity_id, tag_id, "tagged_with")
        
        # Cache
        self.pages[url] = page
        
        # Persist
        self._save_page(page)
        
        return entity_id
    
    def add_relationship(self, from_url: str, to_url: str, rel_type: str):
        """
        Add relationship between pages.
        
        Args:
            from_url: Source page URL
            to_url: Target page URL
            rel_type: Relationship type (links_to, visited_before, related_to, etc.)
        """
        from_page = self.pages.get(from_url)
        to_page = self.pages.get(to_url)
        
        if from_page and to_page and from_page.entity_id and to_page.entity_id:
            self.mg.add_relationship(
                from_page.entity_id,
                to_page.entity_id,
                rel_type
            )
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search pages by semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of matching pages
        """
        results = self.mg.similar_to(query, top_k=top_k, filter_type="page")
        
        # Enrich with page data
        enriched = []
        for r in results:
            entity_id = r.get("entity_id")
            
            # Find matching page
            for page in self.pages.values():
                if page.entity_id == entity_id:
                    enriched.append({
                        **r,
                        "url": page.url,
                        "scraped_at": page.scraped_at,
                        "time_spent": page.time_spent,
                        "tags": page.tags
                    })
                    break
        
        return enriched
    
    def research_path(self, topic: str, max_depth: int = 5) -> Dict:
        """
        Get your research path on a topic.
        
        Args:
            topic: Research topic
            max_depth: How many hops to follow
        
        Returns:
            Research path with pages and relationships
        """
        results = self.mg.hybrid_query(
            text=topic,
            relationships=["links_to", "visited_before", "related_to", "tagged_with"],
            max_depth=max_depth,
            top_k=5
        )
        
        # Enrich with page URLs
        path = {
            "topic": topic,
            "pages": [],
            "tags": [],
            "total": results["total_results"]
        }
        
        for item in results.get("similar", []) + results.get("expanded", []):
            entity_type = item.get("type")
            
            if entity_type == "page":
                # Find page by entity_id
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
    
    def get_linked_pages(self, url: str) -> List[Dict]:
        """
        Get pages linked from/to a specific page.
        
        Args:
            url: Page URL
        
        Returns:
            List of linked pages
        """
        page = self.pages.get(url)
        if not page or not page.entity_id:
            return []
        
        relationships = self.mg.get_relationships(
            page.entity_id,
            rel_types=["links_to", "visited_before", "related_to"]
        )
        
        linked = []
        for rel in relationships:
            # Find the other page
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
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        graph_stats = self.mg.get_stats()
        
        return {
            "total_pages": len(self.pages),
            "total_tags": len(set(tag for p in self.pages.values() for tag in p.tags)),
            "graph_entities": graph_stats["entities"],
            "graph_relationships": graph_stats["relationships"],
            "database": self.db_path
        }
    
    def export(self, format: str = "json") -> str:
        """Export all data"""
        if format == "json":
            data = {
                "pages": [
                    {
                        "url": p.url,
                        "title": p.title,
                        "content": p.content,
                        "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
                        "time_spent": p.time_spent,
                        "tags": p.tags,
                        "metadata": p.metadata
                    }
                    for p in self.pages.values()
                ],
                "graph": self.mg.export_graph(format="json")
            }
            return json.dumps(data, indent=2)
        
        return ""
    
    def close(self):
        """Cleanup"""
        pass  # Nothing to cleanup for now


# === Convenience Functions ===

_memory: Optional[BrowserMemory] = None


def get_memory(db_path: str = "browser_memory.db") -> BrowserMemory:
    """Get or create browser memory instance"""
    global _memory
    if not _memory:
        _memory = BrowserMemory(db_path)
    return _memory


def add_page(*args, **kwargs) -> str:
    """Add a page"""
    return get_memory().add_page(*args, **kwargs)


def search(query: str, top_k: int = 10) -> List[Dict]:
    """Search pages"""
    return get_memory().search(query, top_k)


def research_path(topic: str, max_depth: int = 5) -> Dict:
    """Get research path"""
    return get_memory().research_path(topic, max_depth)


def get_stats() -> Dict:
    """Get stats"""
    return get_memory().get_stats()


if __name__ == "__main__":
    print("🧠 Browser Memory Demo")
    print("=" * 60)
    
    # Create instance
    bm = BrowserMemory(db_path=":memory:")
    
    # Add sample pages
    print("\n📄 Adding pages...")
    
    bm.add_page(
        url="https://oauth.net/2/",
        title="OAuth 2.0 Tutorial",
        content="OAuth 2.0 is the industry-standard protocol for authorization...",
        time_spent=300,
        tags=["oauth", "auth", "security"]
    )
    
    bm.add_page(
        url="https://jwt.io/introduction",
        title="JWT Introduction",
        content="JSON Web Tokens are an open, industry standard RFC 7519 method...",
        time_spent=180,
        tags=["jwt", "auth", "tokens"]
    )
    
    bm.add_page(
        url="https://github.com/auth0",
        title="Auth0 GitHub",
        content="Auth0 - identity management platform...",
        time_spent=120,
        tags=["auth0", "github", "identity"]
    )
    
    # Add relationships
    print("\n🔗 Adding relationships...")
    bm.add_relationship(
        "https://oauth.net/2/",
        "https://jwt.io/introduction",
        "visited_before"
    )
    bm.add_relationship(
        "https://oauth.net/2/",
        "https://github.com/auth0",
        "links_to"
    )
    
    # Search
    print("\n🔍 Search: 'authentication'")
    results = bm.search("authentication", top_k=3)
    for r in results:
        print(f"   [{r.get('score', 0):.3f}] {r['title']}")
        print(f"        URL: {r['url']}")
        print(f"        Tags: {', '.join(r.get('tags', []))}")
    
    # Research path
    print("\n🛤️  Research path: 'OAuth'")
    path = bm.research_path("OAuth", max_depth=2)
    print(f"   Topic: {path['topic']}")
    print(f"   Pages found: {len(path['pages'])}")
    for p in path['pages']:
        print(f"     - {p['title']} ({p['url']})")
    print(f"   Tags: {', '.join(path['tags'])}")
    
    # Linked pages
    print("\n🔗 Pages linked from OAuth tutorial:")
    linked = bm.get_linked_pages("https://oauth.net/2/")
    for l in linked:
        print(f"   {l['relationship']}: {l['title']} ({l['direction']})")
    
    # Stats
    print("\n📊 Statistics")
    stats = bm.get_stats()
    print(f"   Total pages: {stats['total_pages']}")
    print(f"   Total tags: {stats['total_tags']}")
    print(f"   Graph entities: {stats['graph_entities']}")
    print(f"   Graph relationships: {stats['graph_relationships']}")
    
    print("\n✅ Demo complete!")
