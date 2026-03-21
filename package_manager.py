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


class PackageManager:
    """
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

    def install(
        self,
        source: str,
        upgrade: bool = False,
        verify: bool = True,
        allow_untrusted: bool = False,
    ) -> str:
        """
        Install a package from GitHub or local path.

        Args:
            source: GitHub URL (github.com/user/repo) or local path
            upgrade: Upgrade if already installed
            verify: Verify hash after install
            allow_untrusted: Allow installation from untrusted sources (for automation)

        Returns:
            Package name

        Raises:
            ValueError: If source is invalid or untrusted
            RuntimeError: If installation fails
        """
        # Check if source is trusted
        if source.startswith("github.com") and not self.security.is_trusted_source(
            source
        ):
            if not allow_untrusted:
                raise ValueError(
                    f"Untrusted source: {source}. Use allow_untrusted=True or add to trusted sources."
                )
            # Log warning but continue (automation-safe)
            print(f"  Installing from untrusted source: {source}")

        # Parse source
        if source.startswith("github.com"):
            # GitHub URL
            name = self._parse_github_name(source)
            is_github = True
        elif Path(source).exists():
            # Local path
            name = Path(source).name
            is_github = False
        else:
            raise ValueError(f"Invalid source: {source}")

        # Check if already installed
        existing = self._get_package(name)
        if existing and not upgrade:
            print(f"  Package '{name}' already installed (use upgrade=True to update)")
            return name

        # Install
        install_path = self.packages_dir / name

        try:
            if is_github:
                print(f" Installing {name} from GitHub...")
                self._install_from_github(source, install_path, upgrade)
            else:
                print(f" Installing {name} from local path...")
                self._install_from_local(source, install_path, upgrade)

            # Install dependencies
            self._install_dependencies(install_path)

            # Get version
            version = self._get_version(name)

            # Create backup before installing (if upgrade)
            if upgrade and existing:
                print(f"   Creating backup...")
                create_backup(name, existing["version"])

            # Verify hash
            if verify:
                print(f"   Verifying integrity...")
                file_hash = self.security.compute_hash(install_path)
                self.security.save_version_hash(name, version, file_hash)

            # Register in database
            self._register_package(name, source, version)

            # Hot-reload
            if self.hotload:
                try:
                    self.hotload.load(name, reload=upgrade)
                except Exception as e:
                    print(f"     Hot-load warning: {e}")

            print(f" Installed '{name}' to {install_path}")

            # Build wiki after successful install
            try:
                wiki_dir = os.path.join(os.path.dirname(__file__), "pakman_wiki")
                pakman_packages_dir = os.path.join(
                    os.path.dirname(__file__), "packages"
                )
                # Ensure wiki directory exists
                os.makedirs(wiki_dir, exist_ok=True)
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "wikipak",
                        "build",
                        wiki_dir,
                        pakman_packages_dir,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(
                    f"📚 Wiki built/updated at {wiki_dir}. Run 'pakman wiki' to serve it."
                )
            except Exception as e:
                print(f"⚠️ Failed to build wiki after install: {e}")

            return name

        except UnicodeDecodeError as e:
            # Cleanup on failure
            if install_path.exists():
                shutil.rmtree(install_path)
            raise RuntimeError(
                f"Installation failed (encoding error - try copying manually): {e}"
            )
        except Exception as e:
            # Cleanup on failure
            if install_path.exists():
                shutil.rmtree(install_path)
            raise RuntimeError(f"Installation failed: {e}")

    def _parse_github_name(self, url: str) -> str:
        """Extract package name from GitHub URL.

        Supports two formats:
          github.com/udahar/MyRepo          -> "MyRepo"
          github.com/udahar/PakMan#packages/PromptSKLib  -> "PromptSKLib"
        """
        # Subfolder syntax: repo#path/to/subfolder  -> name is last path segment
        if "#" in url:
            _, subfolder = url.split("#", 1)
            return subfolder.rstrip("/").split("/")[-1]
        parts = url.split("/")
        if len(parts) >= 3:
            return parts[2]
        return url.replace("github.com/", "").split("/")[0]

    def _install_from_github(self, url: str, dest: Path, upgrade: bool):
        """Clone from GitHub, or sparse-checkout a subfolder via # syntax.

        Full repo:   github.com/udahar/MyRepo
        Subfolder:   github.com/udahar/PakMan#packages/PromptSKLib
        """
        if "#" in url:
            repo_url, subfolder = url.split("#", 1)
            self._install_github_sparse(repo_url, subfolder.strip("/"), dest, upgrade)
        elif upgrade and dest.exists():
            subprocess.run(["git", "pull"], cwd=dest, check=True, capture_output=True)
        else:
            subprocess.run(
                ["git", "clone", f"https://{url}", str(dest)],
                check=True,
                capture_output=True,
            )

    def _install_github_sparse(
        self, repo_url: str, subfolder: str, dest: Path, upgrade: bool
    ):
        """Pull only a subfolder from a repo using git sparse-checkout.

        No full repo clone — downloads just the files you need.
        Works on git >= 2.25 (sparse-checkout) and >= 2.27 (--filter=blob:none).
        """
        import tempfile

        if upgrade and dest.exists():
            shutil.rmtree(dest)

        full_url = f"https://{repo_url}"

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # Init a bare-minimum repo, configure sparse, then fetch
            subprocess.run(["git", "init", str(tmp)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(tmp), "remote", "add", "origin", full_url],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(tmp), "config", "core.sparseCheckout", "true"],
                check=True,
                capture_output=True,
            )
            sparse_file = tmp / ".git" / "info" / "sparse-checkout"
            sparse_file.write_text(subfolder + "/\n")
            subprocess.run(
                ["git", "-C", str(tmp), "pull", "--depth=1", "origin", "HEAD"],
                check=True,
                capture_output=True,
            )
            # Move the subfolder into place
            src = tmp / subfolder
            if not src.exists():
                raise RuntimeError(
                    f"Subfolder '{subfolder}' not found in {repo_url}. "
                    "Check registry.json path field."
                )
            shutil.copytree(str(src), str(dest))

    def _install_from_local(self, source: str, dest: Path, upgrade: bool):
        """Copy from local path"""
        if dest.exists():
            shutil.rmtree(dest)

        # Copy with ignore for problematic files
        def ignore_patterns(path, names):
            ignored = []
            for name in names:
                # Skip cache and temp files
                if (
                    name.startswith(".")
                    or name.endswith(".pyc")
                    or name == "__pycache__"
                ):
                    ignored.append(name)
            return ignored

        shutil.copytree(source, dest, ignore=ignore_patterns)

    def _install_dependencies(self, install_path: Path):
        """Install requirements.txt if exists"""
        req_file = install_path / "requirements.txt"

        if req_file.exists():
            print(f"   Installing dependencies...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    check=True,
                    capture_output=True,
                )
                print(f"    Dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"     Dependency install warning: {e.stderr.decode()[:200]}")

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
        """Check if package can be imported"""
        try:
            __import__(name)
            return True
        except ImportError:
            return False

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

    def uninstall(self, name: str) -> bool:
        """
        Uninstall a package.

        Args:
            name: Package name

        Returns:
            True if successful
        """
        pkg_info = self._get_package(name)

        if not pkg_info:
            print(f"  Package '{name}' not installed")
            return False

        # Remove from filesystem
        pkg_path = self.packages_dir / name
        if pkg_path.exists():
            shutil.rmtree(pkg_path)

        # Remove from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE packages SET status = 'uninstalled' WHERE name = ?", (name,)
        )
        conn.commit()
        conn.close()

        # Remove from sys.modules
        if name in sys.modules:
            del sys.modules[name]

        print(f" Uninstalled '{name}'")
        return True

    def update(
        self, name: str = None, show_changelog: bool = True, auto_confirm: bool = False
    ) -> List[str]:
        """
        Update packages from their sources.

        Args:
            name: Specific package to update (None for all)
            show_changelog: Show changelog before update
            auto_confirm: Auto-confirm updates (for automation)

        Returns:
            List of updated package names
        """
        # Check for updates first
        updates = self.check_updates()

        if not updates:
            print(" All packages are up to date")
            return []

        if name:
            updates = [u for u in updates if u["name"] == name]

        updated = []

        for pkg in updates:
            pkg_name = pkg["name"]
            current = pkg["current"]
            latest = pkg["latest"]

            print(f"\n {pkg_name}: {current}  {latest}")

            # Show changelog
            if show_changelog:
                changelog = get_changelog(pkg_name, latest)
                if changelog and "No changelog" not in changelog:
                    print(f"\n Changelog:\n{changelog}")

                # Automation-safe: skip prompt if auto_confirm
                if not auto_confirm:
                    response = input(f"Update {pkg_name}? (y/n): ")
                    if response.lower() != "y":
                        continue

            try:
                print(f"   Updating...")
                self.install(pkg["source"], upgrade=True, verify=True)
                updated.append(pkg_name)
            except Exception as e:
                print(f"     Failed to update {pkg_name}: {e}")
                print(f"   Rolling back...")
                rollback(pkg_name, current)

        return updated

    def check_updates(self) -> List[Dict]:
        """Check for available updates"""
        packages = self.list_packages()
        return security_check_updates(packages)

    def rollback_to(self, name: str, version: str) -> bool:
        """
        Rollback package to specific version.

        Args:
            name: Package name
            version: Version to rollback to

        Returns:
            True if successful
        """
        print(f" Rolling back {name} to v{version}...")

        if rollback(name, version):
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE packages
                SET version = ?, updated_at = ?
                WHERE name = ?
            """,
                (version, datetime.now().isoformat(), name),
            )
            conn.commit()
            conn.close()

            # Hot-reload
            if self.hotload:
                self.hotload.load(name, reload=True)

            print(f" Rolled back {name} to v{version}")
            return True

        print(f" Rollback failed")
        return False

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
