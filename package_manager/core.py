# -*- coding: utf-8 -*-
"""
PkgMan - Package Manager for Paks

Install and manage AI capability packages.
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

from security import (
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


from .installer import InstallerMixin
from .registry import RegistryMixin

class PackageManager(InstallerMixin, RegistryMixin):
    """Package manager for custom modules."""

    def __init__(self, packages_dir: str = None, db_path: str = None):
        """Initialize package manager."""
        pakman_home = Path(os.environ.get("PAKMAN_HOME", str(Path.home() / ".pakman")))
        pakman_home.mkdir(parents=True, exist_ok=True)

        if packages_dir:
            self.packages_dir = Path(packages_dir)
        else:
            self.packages_dir = pakman_home / "packages"

        self.packages_dir.mkdir(exist_ok=True)

        if str(self.packages_dir) not in sys.path:
            sys.path.insert(0, str(self.packages_dir))

        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = pakman_home / "pakman.db"

        self.security = get_security_manager(str(self.packages_dir), str(self.db_path))
        self.security.add_trusted_source("github.com/udahar/*")
        self.security.add_trusted_source("github.com/udahar")

        self._init_db()

        # Load hotload if available (watchfiles dep may not be installed)
        try:
            import hotload
            self.hotload = hotload
        except (ImportError, Exception):
            self.hotload = None


_package_manager: Optional[PackageManager] = None


def get_package_manager() -> PackageManager:
    """Get or create package manager"""
    global _package_manager
    if not _package_manager:
        _package_manager = PackageManager()
    return _package_manager


def install(source: str, upgrade: bool = False, verify: bool = True, allow_untrusted: bool = False) -> str:
    """Install a package"""
    return get_package_manager().install(source, upgrade, verify, allow_untrusted)


def uninstall(name: str) -> bool:
    """Uninstall a package"""
    return get_package_manager().uninstall(name)


def list_packages() -> List[Dict]:
    """List installed packages"""
    return get_package_manager().list_packages()


def get_package(name: str):
    """Get installed package module"""
    return get_package_manager().get_package(name)


def update(name: str = None, show_changelog: bool = True, auto_confirm: bool = False) -> List[str]:
    """Update packages"""
    return get_package_manager().update(name, show_changelog, auto_confirm)


def check_updates() -> List[Dict]:
    """Check for updates"""
    return get_package_manager().check_updates()


def rollback_to(name: str, version: str) -> bool:
    """Rollback to version"""
    return get_package_manager().rollback_to(name, version)


def list_versions(name: str) -> List[Dict]:
    """List available versions"""
    return get_package_manager().list_versions(name)


def get_changelog(name: str, version: str = None) -> str:
    """Get changelog"""
    return get_package_manager().get_changelog(name, version)


def search(query: str) -> List[Dict]:
    """Search packages"""
    return get_package_manager().search(query)


def get_stats() -> Dict:
    """Get stats"""
    return get_package_manager().get_stats()


# Deferred: PackageManager is initialized on first use, not on import.
# Auto-init at import time caused CLI commands (pakman list, etc.) to hang
# if any package initialization blocked or threw during module load.


__all__ = [
    "PackageManager",
    "SecurityManager",
    "get_package_manager",
    "install",
    "uninstall",
    "list_packages",
    "get_package",
    "update",
    "check_updates",
    "rollback_to",
    "list_versions",
    "get_changelog",
    "search",
    "get_stats",
    "trust_source",
]
