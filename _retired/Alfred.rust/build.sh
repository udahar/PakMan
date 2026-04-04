#!/bin/bash
# Rust Utilities Build Script (Linux/Mac)

set -e

echo "========================================"
echo "  Rust Utilities - Build Script"
echo "  Building 48 crates..."
echo "========================================"
echo ""

# Check for Rust
if ! command -v rustc &> /dev/null; then
    echo "✗ Rust not found. Please install Rust first."
    echo "  https://rustup.rs/"
    exit 1
fi

rustc --version
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Build all crates
echo "Building all crates..."
echo ""

cargo build --release

echo ""
echo "✓ Build successful!"
echo ""

# Count binaries
binary_count=$(ls target/release/ | grep -v "\.d\|build" | wc -l)
echo "Built $binary_count binaries"
echo ""

echo "========================================"
echo "  Quick Start Guide"
echo "========================================"
echo ""
echo "1. Test rustutils:"
echo "   ./target/release/rustutils --version"
echo ""
echo "2. List all tools:"
echo "   ./target/release/rustutils list"
echo ""
echo "3. Get tool schemas:"
echo "   ./target/release/rustutils schema"
echo ""
echo "4. Register a skill:"
echo "   ./target/release/rustutils skill register crates/skill_registry/examples/analyze_repo.json"
echo ""
echo "5. List skills:"
echo "   ./target/release/rustutils skill list"
echo ""
echo "6. Run a pipeline:"
echo "   ./target/release/rustutils pipe '{\"steps\":[{\"tool\":\"fs_scan\",\"args\":[\".\",\"--json\"]}]}'"
echo ""
echo "7. Store memory:"
echo "   ./target/release/rustutils memory store test_key '{\"value\":\"hello\"}'"
echo ""
echo "8. Recall memory:"
echo "   ./target/release/rustutils memory recall test_key"
echo ""
echo "========================================"
echo ""
