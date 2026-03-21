# WikiPak

Unified documentation generator for PakMan packages.

## Overview

WikiPak collects documentation from all PakMan packages and generates a unified wiki using ZolaPress.

## Installation

```bash
# Install from local source
pip install ./path/to/wikipak

# Or install via pip (when published)
pip install wikipak
```

## Usage

### Command-Line Interface

```bash
# Build a unified wiki from all PakMan packages
wikipak build ./path/to/wiki ./path/to/pakman/packages

# Serve the wiki locally
wikipak serve ./path/to/wiki ./path/to/pakman/packages --port 1111
```

### Python Library

```python
from wikipak import build_wiki, serve_wiki

# Build the wiki
build_wiki("./path/to/wiki", "./path/to/pakman/packages")

# Serve the wiki
serve_wiki("./path/to/wiki", "./path/to/pakman/packages", port=1111)
```

## Features

- Collects documentation from all PakMan packages
- Generates a unified markdown wiki
- Integrates with ZolaPress for building and serving
- Both CLI and Python library interfaces
- MIT licensed

## Documentation

For detailed documentation, see the [WikiPak documentation](content/_index.md).

## License

MIT License