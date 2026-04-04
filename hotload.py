# -*- coding: utf-8 -*-
"""
ModLib Hot-Reload Module Loader

Dynamically loads, reloads, and unloads modules without restarting.

Usage:
    from ModLib import hotload
    
    # Load a module
    mod = hotload("PromptRD")
    
    # Reload with fresh code
    mod = hotload("PromptRD", reload=True)
    
    # Unload
    hotload.unload("PromptRD")
    
    # List loaded modules
    print(hotload.list_loaded())
"""

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import watchfiles
import asyncio


@dataclass
class LoadedModule:
    """Information about a loaded module"""
    name: str
    path: Path
    module: Any
    loaded_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    file_hash: str = ""
    reload_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "loaded_at": self.loaded_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "reload_count": self.reload_count,
            "is_active": self.is_active
        }


class HotLoader:
    """
    Hot-reload module loader.
    
    Watches for file changes and reloads modules automatically.
    """
    
    def __init__(self, frank_root: str = None):
        self.frank_root = Path(frank_root) if frank_root else Path(__file__).parent.parent
        self.loaded: Dict[str, LoadedModule] = {}
        self._watch_task: Optional[asyncio.Task] = None
        self._watch_paths: List[Path] = []
        self._callbacks: Dict[str, List[callable]] = {}
    
    def _find_module_path(self, module_name: str) -> Optional[Path]:
        """Find module directory by name"""
        # Check common locations
        locations = [
            self.frank_root / module_name,
            self.frank_root.parent / "src" / "modules" / module_name,
            self.frank_root / "PromptRD" / module_name,
            Path.cwd() / module_name,
        ]
        
        for loc in locations:
            if loc.exists() and (loc / "__init__.py").exists():
                return loc
        
        return None
    
    def _compute_file_hash(self, path: Path) -> str:
        """Compute hash of all Python files in module"""
        hasher = hashlib.md5()
        
        for py_file in path.rglob("*.py"):
            if not py_file.name.startswith("_"):
                hasher.update(py_file.read_bytes())
        
        return hasher.hexdigest()
    
    def _get_last_modified(self, path: Path) -> datetime:
        """Get most recent modification time"""
        mtimes = [f.stat().st_mtime for f in path.rglob("*.py")]
        if mtimes:
            return datetime.fromtimestamp(max(mtimes))
        return datetime.now()
    
    def load(self, module_name: str, force: bool = False) -> Optional[Any]:
        """
        Load a module dynamically.
        
        Args:
            module_name: Name of module to load
            force: Force reload even if already loaded
        
        Returns:
            Loaded module or None
        """
        # Check if already loaded
        if module_name in self.loaded and not force:
            return self.loaded[module_name].module
        
        # Find module path
        module_path = self._find_module_path(module_name)
        
        if not module_path:
            print(f"❌ Module '{module_name}' not found")
            return None
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path / "__init__.py"
            )
            
            if not spec or not spec.loader:
                print(f"❌ Cannot load module '{module_name}'")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules so imports work
            sys.modules[module_name] = module
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Track loaded module
            loaded_mod = LoadedModule(
                name=module_name,
                path=module_path,
                module=module,
                last_modified=self._get_last_modified(module_path),
                file_hash=self._compute_file_hash(module_path)
            )
            
            self.loaded[module_name] = loaded_mod
            
            # Add to watch paths
            if module_path not in self._watch_paths:
                self._watch_paths.append(module_path)
            
            print(f"✅ Loaded: {module_name} from {module_path}")
            
            # Trigger callbacks
            self._trigger_callback("loaded", module_name)
            
            return module
            
        except Exception as e:
            print(f"❌ Failed to load '{module_name}': {e}")
            if module_name in sys.modules:
                del sys.modules[module_name]
            return None
    
    def reload(self, module_name: str) -> Optional[Any]:
        """
        Reload a module with fresh code.
        
        Args:
            module_name: Name of module to reload
        
        Returns:
            Reloaded module or None
        """
        if module_name not in self.loaded:
            print(f"⚠️  Module '{module_name}' not loaded, loading...")
            return self.load(module_name)
        
        loaded_mod = self.loaded[module_name]
        
        # Check if files changed
        current_hash = self._compute_file_hash(loaded_mod.path)
        
        if current_hash == loaded_mod.file_hash:
            print(f"ℹ️  No changes detected in '{module_name}'")
            return loaded_mod.module
        
        print(f"🔄 Reloading '{module_name}'...")
        
        try:
            # Remove old module
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Reload
            spec = importlib.util.spec_from_file_location(
                module_name,
                loaded_mod.path / "__init__.py"
            )
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Update tracking
            loaded_mod.module = module
            loaded_mod.reload_count += 1
            loaded_mod.last_modified = datetime.now()
            loaded_mod.file_hash = current_hash
            
            print(f"✅ Reloaded: {module_name} (reload #{loaded_mod.reload_count})")
            
            # Trigger callbacks
            self._trigger_callback("reloaded", module_name)
            
            return module
            
        except Exception as e:
            print(f"❌ Failed to reload '{module_name}': {e}")
            return None
    
    def unload(self, module_name: str) -> bool:
        """
        Unload a module.
        
        Args:
            module_name: Name of module to unload
        
        Returns:
            True if successful
        """
        if module_name not in self.loaded:
            print(f"⚠️  Module '{module_name}' not loaded")
            return False
        
        loaded_mod = self.loaded[module_name]
        
        # Remove from sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Mark as inactive
        loaded_mod.is_active = False
        
        # Remove from tracking
        del self.loaded[module_name]
        
        print(f"✅ Unloaded: {module_name}")
        
        # Trigger callbacks
        self._trigger_callback("unloaded", module_name)
        
        return True
    
    def list_loaded(self) -> List[dict]:
        """List all loaded modules"""
        return [mod.to_dict() for mod in self.loaded.values()]
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a loaded module"""
        if module_name in self.loaded:
            return self.loaded[module_name].module
        return None
    
    def register_callback(self, event: str, callback: callable):
        """
        Register callback for module events.
        
        Events: loaded, reloaded, unloaded
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, module_name: str):
        """Trigger callbacks for an event"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(module_name)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    async def start_watching(self, auto_reload: bool = True):
        """
        Start watching for file changes.
        
        Args:
            auto_reload: Automatically reload changed modules
        """
        print("👁️  Starting module watcher...")
        
        async def watch_loop():
            while True:
                try:
                    # Watch all module paths
                    watch_paths = [str(p) for p in self._watch_paths if p.exists()]
                    
                    if not watch_paths:
                        await asyncio.sleep(5)
                        continue
                    
                    # Watch for changes
                    async for changes in watchfiles.awatch(*watch_paths, debounce=2000):
                        for change_type, path in changes:
                            if path.endswith('.py'):
                                # Find which module this belongs to
                                for mod_name, mod in self.loaded.items():
                                    if str(mod.path) in path:
                                        print(f"📝 Detected change in {mod_name}")
                                        
                                        if auto_reload:
                                            await asyncio.sleep(0.5)  # Wait for write to complete
                                            self.reload(mod_name)
                                        
                                        break
                    
                except Exception as e:
                    print(f"Watcher error: {e}")
                    await asyncio.sleep(5)
        
        self._watch_task = asyncio.create_task(watch_loop())
    
    async def stop_watching(self):
        """Stop watching for changes"""
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None
            print("⏹️  Module watcher stopped")


# Global instance
_hotloader: Optional[HotLoader] = None


def get_loader() -> HotLoader:
    """Get or create hot loader"""
    global _hotloader
    if not _hotloader:
        _hotloader = HotLoader()
    return _hotloader


def load(module_name: str, reload: bool = False) -> Optional[Any]:
    """
    Load or reload a module.
    
    Usage:
        from ModLib import hotload
        
        # Load
        mod = hotload.load("PromptRD")
        
        # Reload
        mod = hotload.load("PromptRD", reload=True)
    """
    loader = get_loader()
    if reload:
        return loader.reload(module_name)
    return loader.load(module_name)


def unload(module_name: str) -> bool:
    """Unload a module"""
    return get_loader().unload(module_name)


def get(module_name: str) -> Optional[Any]:
    """Get a loaded module"""
    return get_loader().get_module(module_name)


def list_loaded() -> List[dict]:
    """List all loaded modules"""
    return get_loader().list_loaded()


def register_callback(event: str, callback: callable):
    """Register callback for module events"""
    get_loader().register_callback(event, callback)


async def start_watching(auto_reload: bool = True):
    """Start watching for file changes"""
    await get_loader().start_watching(auto_reload)


async def stop_watching():
    """Stop watching"""
    await get_loader().stop_watching()


# Convenience aliases
reload_module = lambda name: load(name, reload=True)


__all__ = [
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
]
