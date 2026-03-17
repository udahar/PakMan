"""
ModLib - Module Library Registry for Frank AI

Self-awareness layer for the Frank platform.
Introspects all available modules and their capabilities.

Inspired by ChatGPT's suggestion:
"Alfred.modules() returns: PromptRouter – online, FieldBench – online..."

Usage:
    from ModLib import get_registry

    registry = get_registry()
    modules = registry.list_modules()

    # Check status
    for module in modules:
        print(f"{module['name']} - {module['status']}")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import importlib


@dataclass
class ModuleInfo:
    """Information about a module"""

    name: str
    version: str
    path: str
    status: str  # online, offline, degraded, building
    capabilities: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    health_score: float = 1.0
    last_check: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "capabilities": self.capabilities,
            "endpoints": self.endpoints,
            "dependencies": self.dependencies,
            "health_score": self.health_score,
            "last_check": self.last_check.isoformat(),
        }


class ModuleRegistry:
    """
    Registry of all Frank AI modules.

    Provides self-awareness of the platform.
    """

    def __init__(self, frank_root: str = None):
        self.frank_root = Path(frank_root) if frank_root else self._detect_frank_root()
        self.modules: Dict[str, ModuleInfo] = {}
        self._last_scan: Optional[datetime] = None

    def _detect_frank_root(self) -> Path:
        """Detect Frank root directory"""
        # Try current file's parent hierarchy
        current = Path(__file__).parent

        # Look for Frank directory structure
        for parent in [current] + list(current.parents):
            if (parent / "Frank" / "PromptRD").exists():
                return parent / "Frank"
            if (parent / "PromptRD").exists():
                return parent

        return current.parent

    def scan_modules(self) -> List[str]:
        """
        Scan for all available modules.

        Returns:
            List of module names found
        """
        modules_found = []

        # Scan /src/modules/
        src_modules_dir = self.frank_root / "src" / "modules"
        if src_modules_dir.exists():
            for module_dir in src_modules_dir.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("_"):
                    module_info = self._inspect_module(module_dir, "src")
                    if module_info:
                        self.modules[module_info.name] = module_info
                        modules_found.append(module_info.name)

        # Scan /PromptRD/ as a module
        promptrd_dir = self.frank_root / "PromptRD"
        if promptrd_dir.exists():
            module_info = self._inspect_promptrd(promptrd_dir)
            if module_info:
                self.modules["PromptRD"] = module_info
                modules_found.append("PromptRD")

        # Scan other potential module locations
        for module_name, module_path in self._known_modules():
            if module_path.exists():
                module_info = self._inspect_path(module_path, module_name)
                if module_info:
                    self.modules[module_name] = module_info
                    modules_found.append(module_name)

        self._last_scan = datetime.now()
        return modules_found

    def _inspect_module(
        self, module_path: Path, module_type: str
    ) -> Optional[ModuleInfo]:
        """Inspect a module directory"""
        name = module_path.name

        # Check for __init__.py
        init_file = module_path / "__init__.py"
        has_init = init_file.exists()

        # Check for README.md
        readme_file = module_path / "README.md"
        has_readme = readme_file.exists()

        # Count Python files
        py_files = list(module_path.glob("*.py"))

        # Determine status
        status = "online" if has_init else "offline"

        # Extract capabilities from __init__.py
        capabilities = []
        endpoints = []

        if has_init:
            content = init_file.read_text()

            # Look for __all__ exports
            if "__all__" in content:
                capabilities = self._extract_exports(content)

            # Look for function definitions
            if "def create_" in content:
                endpoints = self._extract_factories(content)

        # Read metadata from docstring
        metadata = {}
        if has_init:
            metadata = self._parse_metadata(init_file.read_text())

        return ModuleInfo(
            name=name,
            version=metadata.get("version", "1.0"),
            path=str(module_path.relative_to(self.frank_root)),
            status=status,
            capabilities=capabilities or [f"{name} functions"],
            endpoints=endpoints,
            dependencies=self._detect_dependencies(module_path),
            health_score=1.0 if has_init else 0.0,
            metadata=metadata,
        )

    def _inspect_promptrd(self, promptrd_dir: Path) -> Optional[ModuleInfo]:
        """Inspect PromptRD as a module"""
        # Check key components
        has_skills = (promptrd_dir / "PromptSKLib").exists()
        has_planner = (promptrd_dir / "skill_planner.py").exists()
        has_executor = (promptrd_dir / "ticket_executor.py").exists()
        has_worker = (promptrd_dir / "frank_worker.py").exists()
        has_cli = (promptrd_dir / "frank.py").exists()

        capabilities = []
        if has_skills:
            capabilities.append("26 prompt engineering skills")
        if has_planner:
            capabilities.append("Multi-skill chain orchestration")
        if has_executor:
            capabilities.append("Ticket-based execution")
        if has_worker:
            capabilities.append("Autonomous background worker")
        if has_cli:
            capabilities.append("CLI interface")

        # Count skills
        skills_count = 0
        skills_dir = promptrd_dir / "PromptSKLib" / "skills"
        if skills_dir.exists():
            skills_count = len(list(skills_dir.glob("*.md")))

        return ModuleInfo(
            name="PromptRD",
            version="4.0",
            path="PromptRD",
            status="online" if has_cli else "offline",
            capabilities=capabilities,
            endpoints=[
                "./frank --execute",
                "./frank --map",
                "./frank --plan",
                "./frank --learning",
                "./frank --worker",
            ],
            dependencies=["qdrant", "postgres", "redis"],
            health_score=1.0,
            metadata={"skills_count": skills_count, "categories": 5},
        )

    def _inspect_path(self, path: Path, name: str) -> Optional[ModuleInfo]:
        """Inspect a path as a module"""
        return ModuleInfo(
            name=name,
            version="1.0",
            path=str(path),
            status="online",
            capabilities=[f"{name} module"],
            health_score=0.8,
        )

    def _known_modules(self) -> List[tuple]:
        """List of known modules to check"""
        base = self.frank_root
        return [
            ("PromptForge", base / "PromptRD" / "PromptForge"),
            ("PromptRouter", base / "PromptRD" / "PromptRouter"),
            ("PromptOS", base / "PromptRD" / "PromptOS"),
            ("FieldBench", base / "FieldBench"),
            ("BabbleBridge", base / "BabbleBridge"),
            ("CyberBridge", base / "CyberBridge"),
        ]

    def _extract_exports(self, content: str) -> List[str]:
        """Extract __all__ exports"""
        import re

        match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if match:
            items = match.group(1)
            return [
                item.strip().strip("\"'") for item in items.split(",") if item.strip()
            ]
        return []

    def _extract_factories(self, content: str) -> List[str]:
        """Extract factory functions"""
        import re

        matches = re.findall(r"def (create_\w+)\(", content)
        return matches

    def _parse_metadata(self, content: str) -> Dict:
        """Parse metadata from comments"""
        metadata = {}

        # Look for version
        import re

        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            metadata["version"] = version_match.group(1)

        # Look for docstring
        if '"""' in content:
            docstring = content.split('"""')[1] if len(content.split('"""')) > 1 else ""
            metadata["description"] = docstring.strip().split("\n")[0]

        return metadata

    def _detect_dependencies(self, module_path: Path) -> List[str]:
        """Detect module dependencies"""
        deps = []

        # Check for requirements.txt
        req_file = module_path / "requirements.txt"
        if req_file.exists():
            deps.append("requirements.txt")

        # Check imports in __init__.py
        init_file = module_path / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            if "langchain" in content:
                deps.append("langchain")
            if "ollama" in content:
                deps.append("ollama")

        return deps

    def list_modules(self, status_filter: str = None) -> List[Dict]:
        """
        List all modules.

        Args:
            status_filter: Optional filter by status

        Returns:
            List of module info dicts
        """
        modules = [m.to_dict() for m in self.modules.values()]

        if status_filter:
            modules = [m for m in modules if m["status"] == status_filter]

        return sorted(modules, key=lambda x: x["name"])

    def get_module(self, name: str) -> Optional[Dict]:
        """Get info for specific module"""
        if name in self.modules:
            return self.modules[name].to_dict()
        return None

    def check_health(self) -> Dict[str, float]:
        """
        Check health of all modules.

        Returns:
            Dict of module_name -> health_score
        """
        return {name: info.health_score for name, info in self.modules.items()}

    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get all capabilities by module.

        Returns:
            Dict of module_name -> capabilities
        """
        return {name: info.capabilities for name, info in self.modules.items()}

    def __repr__(self) -> str:
        online = sum(1 for m in self.modules.values() if m.status == "online")
        total = len(self.modules)
        return f"ModuleRegistry({online}/{total} modules online)"


# Global instance
_registry: Optional[ModuleRegistry] = None


def get_registry(frank_root: str = None) -> ModuleRegistry:
    """Get or create module registry"""
    global _registry
    if not _registry:
        _registry = ModuleRegistry(frank_root)
        _registry.scan_modules()
    return _registry


def modules() -> List[Dict]:
    """
    Quick access to all modules.

    Usage:
        from ModLib import modules

        for m in modules():
            print(f"{m['name']} - {m['status']}")
    """
    return get_registry().list_modules()


def status() -> str:
    """
    Get formatted status string.

    Usage:
        print(status())

    Output:
        PromptRD – online
        SkillsRegistry – online
        MultiModelOrchestrator – online
    """
    registry = get_registry()
    lines = []

    for module in registry.list_modules():
        icon = "🟢" if module["status"] == "online" else "🔴"
        lines.append(f"{icon} {module['name']} – {module['status']}")

    return "\n".join(lines)


# Auto-scan on import
if __name__ != "__main__":
    try:
        get_registry()
    except Exception:
        pass  # Silent fail on import


# Health check imports
from .health import (
    HealthChecker,
    get_checker,
    run_health_checks,
    check_module,
    get_compliance_report,
)

# Hot-reload imports
from . import hotload
from .hotload import (
    HotLoader,
    get_loader,
    load,
    unload,
    get,
    list_loaded,
    register_callback,
    start_watching,
    stop_watching,
    reload_module,
)

# Package manager imports
from .package_manager import (
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
    get_stats,
)

# Security imports
from .security import (
    SecurityManager,
    get_security_manager,
    trust_source,
    verify_hash,
    get_changelog as sec_get_changelog,
    create_backup,
    rollback,
    list_backups,
    check_updates as security_check_updates,
)

__all__ = [
    # Registry
    "ModuleRegistry",
    "ModuleInfo",
    "get_registry",
    "modules",
    "status",
    # Health
    "HealthChecker",
    "get_checker",
    "run_health_checks",
    "check_module",
    "get_compliance_report",
    # Hot-reload
    "hotload",
    "HotLoader",
    "get_loader",
    "load",
    "unload",
    "get",
    "list_loaded",
    "register_callback",
    "start_watching",
    "stop_watching",
    "reload_module",
    # Package Manager
    "PackageManager",
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
    # Security
    "SecurityManager",
    "get_security_manager",
    "trust_source",
    "verify_hash",
    "create_backup",
    "rollback",
    "list_backups",
]
