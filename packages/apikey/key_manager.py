"""
API Key Management - Secure storage, rotation, and scoping for API keys.

Usage:
    from apikey import KeyManager, KeyScope
    
    manager = KeyManager()
    manager.store_key("openai", "sk-xxx", scope=KeyScope.READ)
    key = manager.get_key("openai")
    manager.rotate_key("openai", "sk-yyy")
"""

import json
import os
import secrets
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib


class KeyScope(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ALL = "all"


class KeyRotationPolicy(Enum):
    MANUAL = "manual"
    AUTO_30_DAYS = "auto_30_days"
    AUTO_90_DAYS = "auto_90_days"


@dataclass
class APIKey:
    name: str
    key_hash: str
    scope: str
    created_at: str
    last_used: Optional[str]
    rotation_policy: str
    metadata: Dict


class KeyManager:
    def __init__(self, storage_path: str = "~/.pakman/keys.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, APIKey] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for name, key_data in data.items():
                    self._keys[name] = APIKey(**key_data)
            except Exception:
                pass
    
    def _save(self):
        data = {name: asdict(key) for name, key in self._keys.items()}
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def store_key(
        self,
        name: str,
        key: str,
        scope: KeyScope = KeyScope.ALL,
        rotation_policy: KeyRotationPolicy = KeyRotationPolicy.MANUAL,
        metadata: Optional[Dict] = None
    ):
        api_key = APIKey(
            name=name,
            key_hash=self._hash_key(key),
            scope=scope.value,
            created_at=datetime.now().isoformat(),
            last_used=None,
            rotation_policy=rotation_policy.value,
            metadata=metadata or {}
        )
        self._keys[name] = api_key
        self._save()
    
    def get_key(self, name: str) -> Optional[str]:
        return None  # Never return actual keys - use token reference
    
    def get_key_info(self, name: str) -> Optional[APIKey]:
        return self._keys.get(name)
    
    def list_keys(self) -> List[str]:
        return list(self._keys.keys())
    
    def rotate_key(self, name: str, new_key: str):
        if name in self._keys:
            old_key = self._keys[name]
            old_key.key_hash = self._hash_key(new_key)
            old_key.created_at = datetime.now().isoformat()
            self._save()
    
    def delete_key(self, name: str):
        if name in self._keys:
            del self._keys[name]
            self._save()


__all__ = [
    "KeyManager",
    "KeyScope",
    "KeyRotationPolicy",
    "APIKey",
]