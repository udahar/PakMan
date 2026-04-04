#!/usr/bin/env bash
# Rust Utilities Installer (Linux/Mac)

#!/bin/bash

INSTALL_DIR="${HOME}/.cargo/bin"
BUILD_RELEASE=false
DRY_RUN=false

echo "========================================"
echo "  Rust Utilities Installer"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUST_DIR="$SCRIPT_DIR"

# Check if Rust directory exists
if [ ! -d "$RUST_DIR" ]; then
    echo "Error: Rust directory not found: $RUST_DIR"
    exit 1
fi

# Check if cargo is available
if ! command -v cargo &> /dev/null; then
    echo "Error: Cargo not found. Please install Rust first."
    exit 1
fi

cargo --version

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --release)
            BUILD_RELEASE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create install directory
mkdir -p "$INSTALL_DIR"

# Build
echo ""
echo "Building utilities..."

if [ "$BUILD_RELEASE" = true ]; then
    cargo build --release
else
    cargo build
fi

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Determine target directory
if [ "$BUILD_RELEASE" = true ]; then
    TARGET_DIR="release"
else
    TARGET_DIR="debug"
fi

TARGET_PATH="$RUST_DIR/target/$TARGET_DIR"

# Get all executables
echo ""
echo "Found utilities:"

for exe in "$TARGET_PATH"/*; do
    if [ -x "$exe" ] && [ -f "$exe" ]; then
        basename "$exe"
    fi
done

# Install
if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "Installing to: $INSTALL_DIR"
    
    for exe in "$TARGET_PATH"/*; do
        if [ -x "$exe" ] && [ -f "$exe" ]; then
            name=$(basename "$exe")
            cp "$exe" "$INSTALL_DIR/$name"
            echo "  ✓ Installed: $name"
        fi
    done
    
    # Add to PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo ""
        echo "Add to your PATH in ~/.bashrc or ~/.zshrc:"
        echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    fi
else
    echo ""
    echo "DRY RUN - No files installed"
fi

echo ""
echo "Installation complete!"
