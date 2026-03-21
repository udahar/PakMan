"""
LinkedIn Network - Import and Query Your Network
"""

import csv
import os
from typing import List, Dict, Optional
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


COLLECTION_NAME = "linkedin_connections"


class LinkedInImporter:
    """
    Import LinkedIn connections into Qdrant for intelligent search.

    Usage:
        importer = LinkedInImporter()
        importer.import_connections("path/to/Connections.csv")

        results = importer.find_by_role("recruiter")
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Qdrant."""
        if not HAS_QDRANT:
            print("✗ qdrant-client not installed")
            return False

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._connected = True
            self._ensure_collection()
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False

    def _ensure_collection(self):
        """Ensure collection exists."""
        if not self.client:
            return

        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if COLLECTION_NAME not in names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=8, distance=Distance.EUCLID),
            )

    def import_connections(self, csv_path: str) -> int:
        """Import connections from LinkedIn CSV."""
        if not self._connected:
            self.connect()

        if not self.client:
            return 0

        count = 0

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    first = row.get("First Name", "").strip()
                    last = row.get("Last Name", "").strip()
                    name = f"{first} {last}".strip()

                    if not name or name == " ":
                        continue

                    url = row.get("URL", "").strip()
                    company = row.get("Company", "").strip()
                    position = row.get("Position", "").strip()
                    connected = row.get("Connected On", "").strip()

                    text_for_embedding = f"{name} {position} {company}".lower()
                    embedding = self._create_embedding(text_for_embedding)

                    payload = {
                        "name": name,
                        "url": url,
                        "company": company,
                        "position": position,
                        "connected_on": connected,
                    }

                    point = PointStruct(
                        id=hash(name) % 1000000, vector=embedding, payload=payload
                    )

                    self.client.upsert(collection_name=COLLECTION_NAME, points=[point])
                    count += 1

                except Exception as e:
                    print(f"Error importing {name}: {e}")

        print(f"✓ Imported {count} connections")
        return count

    def _create_embedding(self, text: str) -> List[float]:
        """Create simple embedding from text."""
        keywords = [
            "recruiter",
            "talent",
            "hr",
            "hiring",
            "engineer",
            "developer",
            "programmer",
            "software",
            "manager",
            "director",
            "vp",
            "chief",
            "founder",
            "ceo",
            "cto",
            "co-founder",
            "analyst",
            "consultant",
            "advisor",
            "startup",
            "tech",
            "ai",
            "ml",
            "data",
            "sales",
            "marketing",
            "business",
            "growth",
            "security",
            "cybersecurity",
            "devops",
            "cloud",
        ]

        vec = [0.0] * 8
        text_lower = text.lower()

        for i, kw in enumerate(keywords[:8]):
            vec[i] = 1.0 if kw in text_lower else 0.0

        return vec

    def find_by_role(self, role: str, limit: int = 10) -> List[Dict]:
        """Find connections by role."""
        return self._search(f"{role} engineer manager director", limit)

    def find_by_company(self, company: str, limit: int = 10) -> List[Dict]:
        """Find connections at a company."""
        return self._search(company, limit)

    def find_by_skill(self, skill: str, limit: int = 10) -> List[Dict]:
        """Find connections with skill."""
        return self._search(f"{skill} python ai security", limit)

    def _search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search connections."""
        if not self.client:
            return []

        embedding = self._create_embedding(query)

        results = self.client.search(
            collection_name=COLLECTION_NAME, query_vector=embedding, limit=limit
        )

        return [
            {
                "name": r.payload.get("name"),
                "url": r.payload.get("url"),
                "company": r.payload.get("company"),
                "position": r.payload.get("position"),
                "score": r.score,
            }
            for r in results
        ]

    def count(self) -> int:
        """Count imported connections."""
        if not self.client:
            return 0

        info = self.client.get_collection(COLLECTION_NAME)
        return info.vectors_count


def import_linkedin_data(
    data_dir: str, qdrant_host: str = "localhost", qdrant_port: int = 6333
):
    """Import all LinkedIn data."""
    importer = LinkedInImporter(host=qdrant_host, port=qdrant_port)

    if not importer.connect():
        print("Failed to connect to Qdrant")
        return 0

    connections_file = os.path.join(data_dir, "Connections.csv")

    if not os.path.exists(connections_file):
        print(f"Connections.csv not found in {data_dir}")
        return 0

    return importer.import_connections(connections_file)
