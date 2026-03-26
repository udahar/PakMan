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
    Package manager for custom modules.

    Features:
    - Install from GitHub or local path
    - Track installed packages (SQLite)
    - Hot-reload support
    - Dependency management via pip
    - Security: hash verification, changelogs, rollback
    """

    def __init__(self, packages_dir: str = None, db_path: str = None):
        """
        Initialize package manager.

        Default install location is ~/.pakman/ — clean, per-user, survives pip upgrades.
        Override with PAKMAN_HOME env var or explicit args.

        Args:
            packages_dir: Where to install packages (default: ~/.pakman/packages/)
            db_path: SQLite database path (default: ~/.pakman/pakman.db)
        """
        # ~/.pakman/ is the user's home for all PakMan data.
        # PAKMAN_HOME env var lets power users point it elsewhere (e.g. a shared drive).
        pakman_home = Path(os.environ.get("PAKMAN_HOME", str(Path.home() / ".pakman")))
        pakman_home.mkdir(parents=True, exist_ok=True)

        # Set packages directory
        if packages_dir:
            self.packages_dir = Path(packages_dir)
        else:
            self.packages_dir = pakman_home / "packages"

        # Create packages directory
        self.packages_dir.mkdir(exist_ok=True)

        # Add to sys.path so imports work
        if str(self.packages_dir) not in sys.path:
            sys.path.insert(0, str(self.packages_dir))

        # Set database path
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = pakman_home / "pakman.db"

        # Initialize security manager
        self.security = get_security_manager(str(self.packages_dir), str(self.db_path))

        # Set trusted source for udahar
        self.security.add_trusted_source("github.com/udahar/*")
        self.security.add_trusted_source("github.com/udahar")

        # Initialize database
        self._init_db()

        # Load hotload if available
        try:
            import hotload

            self.hotload = hotload
        except ImportError:
            self.hotload = None


# === Global Instance ===

_package_manager: Optional[PackageManager] = None


def get_package_manager() -> PackageManager:
    """Get or create package manager"""
    global _package_manager
    if not _package_manager:
        _package_manager = PackageManager()
    return _package_manager


# === Convenience Functions ===


def install(
    source: str,
    upgrade: bool = False,
    verify: bool = True,
    allow_untrusted: bool = False,
) -> str:
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


def update(
    name: str = None, show_changelog: bool = True, auto_confirm: bool = False
) -> List[str]:
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


# === Auto-init ===

# Make packages importable on import
get_package_manager()


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
