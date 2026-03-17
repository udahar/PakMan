# PkgMan - Package Manager with Security

**Personal package manager for Richard's custom modules with enterprise-grade security.**

---

## Quick Start

```python
from PkgMan import install, list_packages, get_package, update, check_updates

# Check for updates
updates = check_updates()
if updates:
    print(f"🔔 {len(updates)} updates available")

# Install from GitHub (udahar's packages are trusted by default)
install("github.com/udahar/browser_memory")

# List installed
packages = list_packages()

# Get and use
bm = get_package("browser_memory")
```

---

## Security Features

### 1. **Trusted Sources**

```python
from PkgMan import trust_source

# udahar's packages are trusted by default
trust_source("github.com/udahar/*")

# Add more trusted sources
trust_source("github.com/alfred-ai/*")

# Untrusted sources show warning
install("github.com/unknown/package")  # ⚠️ Warning prompt
```

### 2. **Hash Verification**

```python
# Every install computes SHA256 hash
# Stored for version verification

# Verify integrity
from PkgMan import verify_hash

is_valid = verify_hash("browser_memory", "1.0.0", install_path)
```

### 3. **Changelog Display**

```python
from PkgMan import get_changelog

# Show what changed
print(get_changelog("browser_memory", "1.1.0"))

# Output:
# ## v1.1.0
# - Added search feature
# - Fixed bug #42
# - Updated dependencies
```

### 4. **Rollback Support**

```python
from PkgMan import rollback_to, list_versions

# List available versions
versions = list_versions("browser_memory")

# Rollback if update breaks
rollback_to("browser_memory", "1.0.0")
```

### 5. **Update Notifications**

```python
from PkgMan import check_updates

# Check for updates (doesn't install)
updates = check_updates()

for pkg in updates:
    print(f"🔔 {pkg['name']}: {pkg['current']} → {pkg['latest']}")
    print(f"   Changelog: {get_changelog(pkg['name'], pkg['latest'])}")
    print(f"   Run: update('{pkg['name']}')")
```

---

## Usage Examples

### Example 1: Safe Update Workflow (Interactive)

```python
from PkgMan import check_updates, get_changelog, update

# Weekly check
updates = check_updates()

if updates:
    print("🔔 Updates available:")
    for pkg in updates:
        print(f"\n{pkg['name']}: {pkg['current']} → {pkg['latest']}")
        print(get_changelog(pkg['name']))

# User decides (interactive)
update()  # Shows prompts
```

### Example 2: Automated Update (Non-Interactive)

```python
from PkgMan import update

# Auto-update all (no prompts - for Alfred/automation)
update(auto_confirm=True)

# Auto-update specific package
update("browser_memory", auto_confirm=True)
```

### Example 3: Alfred Auto-Install

```python
from PkgMan import install

# Alfred can install without blocking
install("github.com/udahar/browser_memory", allow_untrusted=False)

# Install from new source (automation mode)
install("github.com/new/package", allow_untrusted=True)  # Warns but continues
```

### Example 2: Emergency Rollback

```python
from PkgMan import rollback_to, list_versions

# Update broke something
update("browser_memory")  # Oops!

# List backups
versions = list_versions("browser_memory")
print(f"Available versions: {[v['version'] for v in versions]}")

# Rollback
rollback_to("browser_memory", "1.0.0")  # Back to working version
```

### Example 3: Install with Verification

```python
from PkgMan import install

# Install with hash verification (default)
install("github.com/udahar/browser_memory", verify=True)

# Install without verification (faster, less secure)
install("github.com/udahar/browser_memory", verify=False)
```

---

## Default Trusted Sources

**Pre-configured:**
- `github.com/udahar/*` - All udahar's packages
- `github.com/udahar` - udahar's main repos

**Add more:**
```python
trust_source("github.com/my-org/*")
```

---

## Commands

| Function | Description |
|----------|-------------|
| `install(source, upgrade, verify)` | Install package |
| `uninstall(name)` | Remove package |
| `list_packages()` | List installed |
| `get_package(name)` | Get module |
| `update(name, show_changelog)` | Update packages |
| `check_updates()` | Check for updates |
| `rollback_to(name, version)` | Rollback |
| `list_versions(name)` | List backups |
| `get_changelog(name, version)` | Show changelog |
| `search(query)` | Search packages |
| `get_stats()` | Statistics |
| `trust_source(pattern)` | Add trusted source |

---

## Security Workflow

```
1. User runs: install("github.com/udahar/package")
              ↓
2. Check if source is trusted
   - Trusted (udahar/*) → Continue
   - Untrusted → Show warning, ask confirmation
              ↓
3. Clone/Copy package
              ↓
4. Install dependencies (pip)
              ↓
5. Compute SHA256 hash
              ↓
6. Save hash for version
              ↓
7. Create backup (if upgrade)
              ↓
8. Register in database
              ↓
9. Hot-reload module
              ↓
10. ✅ Installed & verified!
```

---

## File Structure

```
ModLib/
├── __init__.py          # PkgMan exports
├── package_manager.py   # Core package manager
├── security.py          # Security features
└── packages/            # Installed packages
    ├── browser_memory/
    ├── memory_graph/
    └── AiOSKernel/

pkgman_security/
├── trusted_sources.json # Trusted source list
├── backups/             # Version backups
│   └── browser_memory/
│       ├── 1.0.0/
│       └── 1.1.0/
├── browser_memory_hashes.json  # Version hashes
└── browser_memory_changelog.md # Changelogs
```

---

## Status

**✅ Implemented:**
- GitHub/local install
- Trusted source validation
- Hash verification
- Changelog tracking
- Rollback support
- Update notifications
- Hot-reload integration
- SQLite persistence

**🔧 TODO:**
- CLI interface
- Automatic changelog fetching from GitHub
- Version pinning (`@v1.0.0`)
- Signature verification (GPG)

---

**Version:** 3.0 (with security)
**Author:** udahar
**License:** Personal use
