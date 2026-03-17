"""
PkgMan Security Features

- Hash verification
- Changelog display
- Rollback support
- Trusted sources
- Update notifications
"""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import subprocess
import os


class SecurityManager:
    """
    Security features for PkgMan.
    
    Features:
    - Hash verification
    - Changelog tracking
    - Rollback support
    - Trusted source validation
    """
    
    def __init__(self, packages_dir: str, db_path: str):
        self.packages_dir = Path(packages_dir)
        self.db_path = Path(db_path)
        self.security_dir = self.packages_dir.parent / "pkgman_security"
        # Lazy — only created on first actual security write (backup, hash, etc.)

        # Only udahar's repos are trusted. Hard-coded by design — not user-configurable.
        # This prevents third parties from tricking end-users into installing untrusted packages.
        self.trusted_sources = [
            "github.com/udahar/",
            "github.com/udahar",
        ]

    def _ensure_security_dir(self):
        """Create security dir only when a write operation actually needs it."""
        self.security_dir.mkdir(exist_ok=True)

    def add_trusted_source(self, pattern: str):
        """No-op: trusted sources are hard-coded to github.com/udahar/ only.
        This method exists for API compatibility but cannot extend trust."""
        pass  # intentionally locked — see __init__ comment
    
    def is_trusted_source(self, source: str) -> bool:
        """Check if source is trusted"""
        for pattern in self.trusted_sources:
            if pattern.endswith("*"):
                # Wildcard match
                prefix = pattern[:-1]
                if source.startswith(prefix):
                    return True
            else:
                # Exact match
                if source == pattern or source.startswith(pattern + "/"):
                    return True
        
        return False
    
    def compute_hash(self, path: Path) -> str:
        """Compute SHA256 hash of directory"""
        hasher = hashlib.sha256()
        
        for file in sorted(path.rglob("*")):
            if file.is_file() and not file.name.startswith('.'):
                hasher.update(str(file.relative_to(path)).encode())
                try:
                    hasher.update(file.read_bytes())
                except:
                    pass
        
        return hasher.hexdigest()
    
    def save_version_hash(self, package_name: str, version: str, file_hash: str):
        """Save hash for a specific version"""
        self._ensure_security_dir()
        hash_file = self.security_dir / f"{package_name}_hashes.json"
        
        hashes = {}
        if hash_file.exists():
            try:
                hashes = json.loads(hash_file.read_text())
            except:
                pass
        
        hashes[version] = {
            "hash": file_hash,
            "saved_at": datetime.now().isoformat()
        }
        
        hash_file.write_text(json.dumps(hashes, indent=2))
    
    def get_version_hash(self, package_name: str, version: str) -> Optional[str]:
        """Get stored hash for version"""
        hash_file = self.security_dir / f"{package_name}_hashes.json"
        
        if hash_file.exists():
            try:
                hashes = json.loads(hash_file.read_text())
                return hashes.get(version, {}).get("hash")
            except:
                pass
        
        return None
    
    def verify_hash(self, package_name: str, version: str, install_path: Path) -> bool:
        """Verify installed package matches expected hash"""
        expected_hash = self.get_version_hash(package_name, version)
        
        if not expected_hash:
            return True  # No hash to verify against
        
        actual_hash = self.compute_hash(install_path)
        return actual_hash == expected_hash
    
    def save_changelog(self, package_name: str, version: str, changelog: str):
        """Save changelog for version"""
        self._ensure_security_dir()
        changelog_file = self.security_dir / f"{package_name}_changelog.md"
        
        # Append to changelog
        content = ""
        if changelog_file.exists():
            content = changelog_file.read_text()
        
        content = f"\n\n## v{version}\n{changelog}\n" + content
        
        changelog_file.write_text(content)
    
    def get_changelog(self, package_name: str, version: str = None) -> str:
        """Get changelog for package"""
        changelog_file = self.security_dir / f"{package_name}_changelog.md"
        
        if changelog_file.exists():
            content = changelog_file.read_text()
            
            if version:
                # Extract specific version
                lines = content.split("\n")
                in_version = False
                result = []
                
                for line in lines:
                    if line.startswith(f"## v{version}"):
                        in_version = True
                    elif in_version and line.startswith("## v"):
                        break
                    
                    if in_version:
                        result.append(line)
                
                return "\n".join(result) if result else "No changelog for this version"
            
            return content
        
        return "No changelog available"
    
    def create_backup(self, package_name: str, version: str) -> Path:
        """Create backup before update"""
        self._ensure_security_dir()
        backup_dir = self.security_dir / "backups" / package_name / version
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        install_path = self.packages_dir / package_name
        
        if install_path.exists():
            # Copy current version to backup
            import shutil
            def ignore_patterns(path, names):
                ignored = []
                for name in names:
                    if name.startswith('.') or name.endswith('.pyc') or name == '__pycache__':
                        ignored.append(name)
                return ignored
            
            shutil.copytree(install_path, backup_dir, ignore=ignore_patterns)
            
            # Save metadata
            metadata = {
                "package": package_name,
                "version": version,
                "backed_up_at": datetime.now().isoformat(),
                "hash": self.compute_hash(install_path)
            }
            
            (backup_dir / "backup_metadata.json").write_text(
                json.dumps(metadata, indent=2)
            )
        
        return backup_dir
    
    def rollback(self, package_name: str, version: str) -> bool:
        """Rollback to previous version"""
        backup_dir = self.security_dir / "backups" / package_name / version
        
        if not backup_dir.exists():
            return False
        
        install_path = self.packages_dir / package_name
        
        # Remove current
        if install_path.exists():
            import shutil
            shutil.rmtree(install_path)
        
        # Restore backup
        import shutil
        shutil.copytree(backup_dir, install_path, 
                       ignore=lambda p, n: ['backup_metadata.json'] if 'backup_metadata.json' in n else [])
        
        return True
    
    def list_backups(self, package_name: str) -> List[Dict]:
        """List available backups for package"""
        backup_dir = self.security_dir / "backups" / package_name
        
        if not backup_dir.exists():
            return []
        
        backups = []
        for version_dir in backup_dir.iterdir():
            if version_dir.is_dir():
                metadata_file = version_dir / "backup_metadata.json"
                
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    backups.append(metadata)
        
        return sorted(backups, key=lambda x: x.get("backed_up_at", ""), reverse=True)
    
    def check_updates(self, packages: List[Dict]) -> List[Dict]:
        """Check for available updates"""
        updates = []
        
        for pkg in packages:
            if pkg.get("source", "").startswith("github.com"):
                try:
                    # Get latest version from GitHub
                    repo_url = pkg["source"]
                    latest = self._get_github_latest_version(repo_url)
                    
                    if latest and latest != pkg.get("version"):
                        updates.append({
                            "name": pkg["name"],
                            "current": pkg.get("version", "unknown"),
                            "latest": latest,
                            "source": pkg["source"]
                        })
                except:
                    pass
        
        return updates
    
    def _get_github_latest_version(self, url: str) -> Optional[str]:
        """Get latest version from GitHub repo"""
        try:
            # Parse repo info
            parts = url.replace("github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                
                # Try to get __version__ from __init__.py
                import requests
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/__init__.py"
                
                response = requests.get(raw_url, timeout=10)
                if response.status_code == 200:
                    import re
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', response.text)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return None


# === Global Instance ===

_security_manager = None


def get_security_manager(packages_dir: str, db_path: str) -> SecurityManager:
    """Get or create security manager"""
    global _security_manager
    if not _security_manager:
        _security_manager = SecurityManager(packages_dir, db_path)
    return _security_manager


# === Convenience Functions ===

def trust_source(pattern: str):
    """Add trusted source"""
    get_security_manager("", "").add_trusted_source(pattern)


def verify_hash(name: str, version: str, path: Path) -> bool:
    """Verify package hash"""
    return get_security_manager("", "").verify_hash(name, version, path)


def get_changelog(name: str, version: str = None) -> str:
    """Get changelog"""
    return get_security_manager("", "").get_changelog(name, version)


def create_backup(name: str, version: str) -> Path:
    """Create backup"""
    return get_security_manager("", "").create_backup(name, version)


def rollback(name: str, version: str) -> bool:
    """Rollback to version"""
    return get_security_manager("", "").rollback(name, version)


def list_backups(name: str) -> List[Dict]:
    """List backups"""
    return get_security_manager("", "").list_backups(name)


def check_updates(packages: List[Dict]) -> List[Dict]:
    """Check for updates"""
    return get_security_manager("", "").check_updates(packages)


__all__ = [
    "SecurityManager",
    "get_security_manager",
    "trust_source",
    "verify_hash",
    "get_changelog",
    "create_backup",
    "rollback",
    "list_backups",
    "check_updates",
]
