# ModLib - Module Library & Package Manager

**Purpose:** Self-awareness layer + package manager for the Frank AI platform

**Features:**
- ✅ Module registry (auto-discovery)
- ✅ Health monitoring & compliance checks
- ✅ **Package Manager** (install from GitHub/local)
- ✅ **Hot-reload** (load/reload modules without restart)
- ✅ File watching (auto-reload on changes)
- ✅ Capability discovery

---

## Quick Start

### Install Packages

```python
from ModLib import install, list_packages, get_package

# Install from GitHub
install("github.com/richard/browser_memory")
install("github.com/richard/memory_graph")

# Install from local path
install("./browser_memory")

# List installed
packages = list_packages()
for pkg in packages:
    print(f"{pkg['name']} - {pkg['status']}")

# Get and use
bm = get_package("browser_memory")
memory = bm.BrowserMemory()
```

### Hot-Reload

```python
from ModLib import hotload

# Load without restart
mod = hotload.load("browser_memory")

# Auto-reload on file changes
import asyncio
asyncio.run(hotload.start_watching(auto_reload=True))
```

### Module Registry

```python
from ModLib import modules, status

# Quick status
print(status())

# Output:
# 🟢 browser_memory – online
# 🟢 memory_graph – online
# 🟢 AiOSKernel – online
```

---

## Package Manager Usage

### Install

```python
from ModLib import install

# From GitHub
install("github.com/richard/browser_memory")

# From local path
install("./my_package")

# Upgrade existing
install("github.com/richard/browser_memory", upgrade=True)
```

### List Packages

```python
from ModLib import list_packages

packages = list_packages()
for pkg in packages:
    print(f"{pkg['name']} v{pkg['version']} - {pkg['status']}")
    print(f"  Source: {pkg['source']}")
    print(f"  Importable: {pkg['importable']}")
```

### Get Package

```python
from ModLib import get_package

# Get module
bm = get_package("browser_memory")

# Use it
memory = bm.BrowserMemory()
```

### Update

```python
from ModLib import update

# Update all
update()

# Update specific
update("browser_memory")
```

### Uninstall

```python
from ModLib import uninstall

uninstall("browser_memory")
```

### Search

```python
from ModLib import search

results = search("memory")
for pkg in results:
    print(f"{pkg['name']}: {pkg['source']}")
```

### Stats

```python
from ModLib import get_stats

stats = get_stats()
print(f"Total packages: {stats['total_packages']}")
print(f"Importable: {stats['importable']}")
print(f"Packages dir: {stats['packages_dir']}")
```

---

## Hot-Reload Usage

### Manual Reload

```python
from ModLib import hotload

# Load
mod = hotload.load("MyModule")

# Reload
mod = hotload.reload("MyModule")

# Unload
hotload.unload("MyModule")
```

### Auto-Watch

```python
import asyncio
from ModLib import hotload

# Start watching
asyncio.run(hotload.start_watching(auto_reload=True))

# Stop watching
asyncio.run(hotload.stop_watching())
```

### Callbacks

```python
from ModLib import register_callback

def on_loaded(name):
    print(f"✅ {name} loaded")

def on_reloaded(name):
    print(f"🔄 {name} reloaded")

register_callback("loaded", on_loaded)
register_callback("reloaded", on_reloaded)
```

---

## Health Monitoring

```python
from ModLib import get_registry

registry = get_registry()

# Get health scores
health = registry.check_health()

for module, score in health.items():
    status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
    print(f"{status} {module}: {score*100:.0f}%")
```

---

## CLI Usage

```bash
# Show all modules
python -m ModLib

# Show online modules
python -m ModLib --status online

# Show capabilities
python -m ModLib --capabilities

# Health check
python -m ModLib --health

# List installed packages
python -m ModLib --packages

# Install package
python -m ModLib --install github.com/richard/browser_memory

# Update packages
python -m ModLib --update
```

---

## Architecture

```
Frank AI Platform
    │
    ├─ ModLib (Package Manager + Registry)
    │   ├─ Package Manager
    │   │   ├─ install() - from GitHub/local
    │   │   ├─ uninstall()
    │   │   ├─ update()
    │   │   └─ list_packages()
    │   │
    │   ├─ Hot-Loader
    │   │   ├─ load()
    │   │   ├─ reload()
    │   │   ├─ unload()
    │   │   └─ watch() [auto-reload]
    │   │
    │   ├─ Registry
    │   │   ├─ scan_modules()
    │   │   ├─ list_modules()
    │   │   └─ check_health()
    │   │
    │   └─ Health
    │       ├─ compliance checks
    │       └─ dependency tracking
    │
    └─ packages/ (installed packages)
        ├─ browser_memory/
        ├─ memory_graph/
        └─ AiOSKernel/
```

---

## Storage

### SQLite Database

**modlib_packages.db:**
```sql
CREATE TABLE packages (
    name TEXT PRIMARY KEY,
    source TEXT,
    version TEXT,
    installed_at TEXT,
    updated_at TEXT,
    status TEXT,
    requirements TEXT,
    metadata TEXT
)
```

### Packages Directory

```
ModLib/packages/
├── browser_memory/
│   ├── __init__.py
│   ├── README.md
│   └── requirements.txt
├── memory_graph/
└── AiOSKernel/
```

---

## GitHub Integration

### Supported URL Formats

```python
# Full URL
install("github.com/richard/browser_memory")

# With branch
install("github.com/richard/browser_memory/tree/main")

# Short form
install("richard/browser_memory")
```

### How It Works

1. Clone from GitHub to `ModLib/packages/`
2. Install `requirements.txt` dependencies via pip
3. Register in SQLite database
4. Hot-load the module
5. Ready to import!

---

## Examples

### Example 1: Install Browser Memory

```python
from ModLib import install, get_package

# Install
install("github.com/richard/browser_memory")

# Use
bm = get_package("browser_memory")
memory = bm.BrowserMemory()

# Add pages
memory.add_page(
    url="https://example.com",
    title="My Page",
    content="Content..."
)

# Search
results = memory.search("authentication")
```

### Example 2: Development Workflow

```python
from ModLib import hotload, install

# Install for first time
install("./browser_memory")

# Start watching
import asyncio
asyncio.run(hotload.start_watching(auto_reload=True))

# Now edit browser_memory files
# Changes auto-reload!
```

### Example 3: Update All Packages

```python
from ModLib import update, list_packages

# Update all
updated = update()
print(f"Updated {len(updated)} packages")

# Check versions
packages = list_packages()
for pkg in packages:
    print(f"{pkg['name']} v{pkg['version']}")
```

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Main exports | ~100 |
| `package_manager.py` | Package installer | ~400 |
| `hotload.py` | Hot-reload loader | ~300 |
| `health.py` | Health checks | ~250 |
| `README.md` | This documentation | - |

**Total:** ~1,050 lines

---

## Status

**✅ Implemented:**
- Module registry (auto-discovery)
- Health monitoring
- Package installer (GitHub/local)
- Hot-reload (manual + auto-watch)
- SQLite persistence
- Dependency management

**🔧 TODO:**
- CLI interface
- GitHub authentication (for private repos)
- Package versioning
- Dependency resolution
- Uninstall cleanup

---

**Version:** 2.0 (with package manager)
**Next:** CLI and versioning
