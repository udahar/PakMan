# PkgMan - Publishing Strategy

**Vision:** One command to install all of udahar's AI tools

```bash
pip install pkgman
pkgman install-all
```

**Boom!** 50+ AI-powered tools ready to go.

---

## The Master Plan

### Phase 1: Make PkgMan Itself pip-installable

**Goal:** Users can `pip install pkgman`

**Steps:**

1. **Add setup.py to ModLib/**
   ```python
   from setuptools import setup, find_packages
   
   setup(
       name="pkgman",
       version="1.0.0",
       author="udahar",
       description="Package Manager for AI Tools",
       packages=find_packages(),
       install_requires=[
           "networkx",
           "qdrant-client",
           "requests",
       ],
   )
   ```

2. **Publish to PyPI**
   ```bash
   # Build
   python -m build
   
   # Upload
   twine upload dist/*
   ```

3. **Users install**
   ```bash
   pip install pkgman
   ```

---

### Phase 2: Package All AI Tools

**Goal:** Each tool is installable via PkgMan

**Tools to Package:**

```
browser_memory/       # Web browsing knowledge graph
memory_graph/         # Hybrid vector + graph DB
AiOSKernel/           # AI task orchestration
pip_boy/              # Package discovery (835+ packages)
ModLib/               # Module registry
PromptRD/             # Prompt engineering
Frank/                # Main AI platform
Browser/              # Browser scraper
... (50+ more)
```

**Each gets:**
- `setup.py` (for pip install)
- `README.md` (documentation)
- `requirements.txt` (dependencies)

---

### Phase 3: PkgMan Manifest

**Goal:** One command installs everything

**Create:** `pkgman_manifest.json`

```json
{
  "name": "udahar-ai-collection",
  "version": "1.0.0",
  "description": "Complete AI toolkit by udahar",
  "packages": [
    {
      "name": "browser_memory",
      "source": "github.com/udahar/browser_memory",
      "required": true,
      "description": "Web browsing knowledge graph"
    },
    {
      "name": "memory_graph",
      "source": "github.com/udahar/memory_graph",
      "required": true,
      "description": "Hybrid vector + graph database"
    },
    {
      "name": "AiOSKernel",
      "source": "github.com/udahar/AiOSKernel",
      "required": true,
      "description": "AI task orchestration"
    },
    ... (50+ more)
  ]
}
```

**Usage:**

```python
from PkgMan import install_manifest

# Install everything
install_manifest("udahar-ai-collection")

# Or interactively
from PkgMan import browse_catalog

catalog = browse_catalog()
# Shows all 50+ tools with descriptions
# User picks what to install
```

---

### Phase 4: Open Source Everything

**Goal:** Community can contribute

**Steps:**

1. **Make all repos public**
   - github.com/udahar/browser_memory
   - github.com/udahar/memory_graph
   - github.com/udahar/AiOSKernel
   - ... (all 50+)

2. **Add LICENSE to each**
   ```
   MIT License
   Copyright (c) 2026 udahar
   ```

3. **Add CONTRIBUTING.md**
   ```markdown
   # How to Contribute
   
   1. Fork the repo
   2. Create branch: `feature/awesome-feature`
   3. Make changes
   4. Submit PR
   5. Get merged!
   ```

4. **Add issues template**
   - Bug report
   - Feature request
   - Tool suggestion

---

### Phase 5: Community Growth

**Goal:** Others help maintain and add tools

**Strategies:**

1. **Easy to add new tools**
   ```python
   # Community member creates new tool
   # They add it to manifest:
   
   {
     "name": "community_tool",
     "source": "github.com/community/community_tool",
     "required": false,
     "description": "Cool community contribution"
   }
   ```

2. **PkgMan discovers community tools**
   ```python
   from PkgMan import discover_community
   
   tools = discover_community()
   # Finds all community-contributed tools
   ```

3. **Rating system**
   ```python
   from PkgMan import rate_tool
   
   rate_tool("browser_memory", stars=5)
   ```

4. **Auto-updates**
   ```python
   from PkgMan import enable_auto_update
   
   enable_auto_update()  # Keeps all tools updated
   ```

---

## The User Experience

### New User

```bash
# Step 1: Install PkgMan
pip install pkgman

# Step 2: See what's available
pkgman list-available

# Output:
# 🤖 udahar's AI Toolkit (50+ tools)
# 
# 🔥 Popular:
#    - browser_memory: Web browsing knowledge graph
#    - memory_graph: Hybrid vector + graph DB
#    - AiOSKernel: AI task orchestration
#    - pip_boy: Discover 835+ Python packages
#
# 📊 Data Tools:
#    - ... (10 more)
#
# 🤖 AI Tools:
#    - ... (20 more)
#
# Run: pkgman install <tool-name>

# Step 3: Install all
pkgman install-all

# Or pick individual
pkgman install browser_memory memory_graph
```

### Existing User

```python
# In Python
from PkgMan import install, list_packages, update

# Check what's new
new_tools = check_new_tools()

# Install new ones
for tool in new_tools:
    print(f"🆕 {tool['name']}: {tool['description']}")
    install(tool['source'])

# Update everything
update()
```

---

## Technical Requirements

### For PkgMan (Main Package)

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="pkgman",
    version="1.0.0",
    author="udahar",
    author_email="udahar@example.com",
    description="Package Manager for AI Tools",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/udahar/pkgman",
    packages=find_packages(),
    install_requires=[
        "networkx>=2.8",
        "qdrant-client>=1.7.0",
        "requests>=2.28.0",
        "gitpython>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "pkgman=pkgman.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
```

### For Each Tool Package

**Minimal setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="browser-memory",
    version="1.0.0",
    author="udahar",
    description="Web browsing knowledge graph",
    packages=find_packages(),
    install_requires=[
        "networkx",
        "qdrant-client",
    ],
)
```

---

## Publishing Checklist

### For PkgMan:

- [ ] Create setup.py
- [ ] Create pyproject.toml
- [ ] Create LICENSE (MIT)
- [ ] Create README.md
- [ ] Test local install: `pip install -e .`
- [ ] Create PyPI account
- [ ] Build: `python -m build`
- [ ] Upload: `twine upload dist/*`
- [ ] Test: `pip install pkgman`

### For Each Tool:

- [ ] Add setup.py
- [ ] Add LICENSE
- [ ] Make repo public
- [ ] Test: `pip install git+https://github.com/udahar/tool`

### For Manifest:

- [ ] Create pkgman_manifest.json
- [ ] List all 50+ tools
- [ ] Add descriptions
- [ ] Test: `pkgman install-all`

---

## The Dream

```
1. pip install pkgman
2. pkgman install-all
3. 50+ AI tools ready
4. Community contributes more
5. Alfred autogenerates new tools
6. ???
7. Profit!
```

---

## Next Steps

1. **Create setup.py for PkgMan**
2. **Publish PkgMan to PyPI**
3. **Create manifest with all tools**
4. **Make all repos public**
5. **Add LICENSE to each**
6. **Write CONTRIBUTING.md**
7. **Launch!**

---

**Version:** 1.0
**Status:** Planning
**Goal:** Make udahar's AI toolkit accessible to everyone
