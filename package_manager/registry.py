# -*- coding: utf-8 -*-
"""
PkgMan - Package Manager for Richard's Custom Modules

Install, manage, and hot-reload custom packages with security features.

Usage:
    from PkgMan import install, list_packages, get_package, update, check_updates

    # Check for updates
    updates = check_updates()

    # Install from GitHub
    install("github.com/udahar/browser_memory")
"""

import sqlite3
import subprocess
import shutil
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

from ..security import (
    get_security_manager,
    SecurityManager,
    trust_source,
    verify_hash,
    get_changelog,
    create_backup,
    rollback,
    list_backups,
    check_updates as security_check_updates,
)


class RegistryMixin:
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packages (
                name TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                version TEXT,
                installed_at TEXT,
                updated_at TEXT,
                status TEXT DEFAULT 'active',
                requirements TEXT,
                metadata TEXT,
                hash TEXT
            )
        """)

        conn.commit()
        conn.close()


    def _register_package(self, name: str, source: str, version: str):
        """Register package in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get requirements
        requirements = self._get_requirements(name)

        # Compute hash
        install_path = self.packages_dir / name
        file_hash = self.security.compute_hash(install_path)

        now = datetime.now().isoformat()

        # Check if exists
        cursor.execute("SELECT 1 FROM packages WHERE name = ?", (name,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                """
                UPDATE packages
                SET source = ?, version = ?, updated_at = ?, requirements = ?, hash = ?, status = 'active'
                WHERE name = ?
            """,
                (source, version, now, json.dumps(requirements), file_hash, name),
            )
        else:
            cursor.execute(
                """
                INSERT INTO packages (name, source, version, installed_at, updated_at, requirements, hash, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """,
                (name, source, version, now, now, json.dumps(requirements), file_hash),
            )

        conn.commit()
        conn.close()

    def _get_version(self, name: str) -> str:
        """Get version from package"""
        pkg_path = self.packages_dir / name

        # Try __init__.py
        init_file = pkg_path / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text(encoding="utf-8")
                import re

                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except:
                pass

        # Try setup.py
        setup_file = pkg_path / "setup.py"
        if setup_file.exists():
            try:
                content = setup_file.read_text(encoding="utf-8")
                import re

                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except:
                pass

        return "unknown"

    def _get_requirements(self, name: str) -> List[str]:
        """Get requirements from package"""
        req_file = self.packages_dir / name / "requirements.txt"

        if req_file.exists():
            return [
                line.strip()
                for line in req_file.read_text().split("\n")
                if line.strip() and not line.startswith("#")
            ]

        return []

    def _get_package(self, name: str) -> Optional[Dict]:
        """Get package info from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM packages WHERE name = ?", (name,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def list_packages(self) -> List[Dict]:
        """List all installed packages"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM packages WHERE status = 'active' ORDER BY name")
        packages = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Enrich with module info
        for pkg in packages:
            pkg["importable"] = self._is_importable(pkg["name"])

        return packages

    def _is_importable(self, name: str) -> bool:
        """Check if package files are present on disk (does not execute the package)."""
        pkg_dir = self.packages_dir / name
        return (pkg_dir / "__init__.py").exists()

    def get_package(self, name: str):
        """
        Get installed package module.

        Args:
            name: Package name

        Returns:
            Imported module

        Raises:
            ImportError: If not installed
        """
        pkg_info = self._get_package(name)

        if not pkg_info:
            raise ImportError(f"Package '{name}' not installed")

        try:
            module = __import__(name)
            return module
        except ImportError as e:
            raise ImportError(
                f"Package '{name}' is installed but cannot be imported: {e}"
            )


    def check_updates(self) -> List[Dict]:
        """Check for available updates"""
        packages = self.list_packages()
        return security_check_updates(packages)


    def list_versions(self, name: str) -> List[Dict]:
        """
        List available backup versions.

        Args:
            name: Package name

        Returns:
            List of available versions
        """
        return list_backups(name)

    def get_changelog(self, name: str, version: str = None) -> str:
        """Get changelog for package"""
        return get_changelog(name, version)

    def search(self, query: str) -> List[Dict]:
        """
        Search installed packages.

        Args:
            query: Search query

        Returns:
            List of matching packages
        """
        packages = self.list_packages()

        # Simple search (name, source)
        results = []
        query_lower = query.lower()

        for pkg in packages:
            if (
                query_lower in pkg["name"].lower()
                or query_lower in pkg["source"].lower()
            ):
                results.append(pkg)

        return results

    def get_stats(self) -> Dict:
        """Get package manager statistics"""
        packages = self.list_packages()

        return {
            "total_packages": len(packages),
            "importable": sum(1 for p in packages if p["importable"]),
            "packages_dir": str(self.packages_dir),
            "database": str(self.db_path),
        }


