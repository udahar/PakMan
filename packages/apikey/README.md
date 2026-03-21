# apikey

API key management for PakMan-aware applications. Provides a shared, secure store for vendor credentials accessible to all installed packages.

## Status

`alpha` — core interface planned, not yet implemented. Tracked in Alfred's project backlog.

## Planned Features

- Encrypted local keystore (`~/.pakman/keys/`)
- Per-vendor key profiles (OpenAI, Anthropic, Ollama, etc.)
- Key rotation and expiry tracking
- PakMan package auto-discovery of available keys

## Install

```bash
pakman install apikey
```
