# ZolaPress

Documentation and site generation utilities for ZolaPress static site generator.

## Overview

ZolaPress provides Python utilities and a command-line interface for managing ZolaPress sites, including building, serving, checking, and managing content and configuration.

## Installation

```bash
# Install from local source
pip install ./path/to/zolapress

# Or install via pip (when published)
pip install zolapress
```

## Usage

### Command-Line Interface

```bash
# Build a ZolaPress site
zolapress build /path/to/site

# Serve a ZolaPress site locally
zolapress serve /path/to/site --port 1111

# Check a site for errors
zolapress check /path/to/site

# Initialize a new ZolaPress site
zolapress init /path/to/new/site --theme terra

# Manage configuration
zolapress config /path/to/site --get --key title
zolapress config /path/to/site --set base_url="https://example.com"

# Manage content
zolapress content /path/to/site --list
zolapress content /path/to/site --create "blog/post.md" --title "My Post" --date "2023-01-01" --tags "tutorial,example"
```

### Python Library

```python
from zolapress import ZolaPressBuilder, build_site, serve_site

# Using the builder class
builder = ZolaPressBuilder("/path/to/site")
builder.build()

# Using convenience functions
build_site("/path/to/site")
serve_site("/path/to/site", port=1111)
```

## Features

- Site building and serving
- Configuration management
- Content creation and listing
- Site validation and checking
- Both CLI and Python library interfaces
- MIT licensed

## Documentation

For detailed documentation, see the [ZolaPress documentation](content/_index.md).

## License

MIT License