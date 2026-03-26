# -*- coding: utf-8 -*-
from .core import (
    PackageManager,
    get_package_manager,
    install,
    uninstall,
    list_packages,
    get_package,
    update,
    check_updates,
    rollback_to,
    list_versions,
    get_changelog,
    search,
    get_stats
)
from security import SecurityManager, trust_source

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
