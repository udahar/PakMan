#!/usr/bin/env powershell
# Rust Utilities Build Script
# Builds all 48 crates and installs rustutils

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Rust Utilities - Build Script" -ForegroundColor Cyan
Write-Host "  Building 48 crates..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Rust
try {
    $rustVersion = rustc --version
    Write-Host "✓ Rust found: $rustVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Rust not found. Please install Rust first." -ForegroundColor Red
    Write-Host "  https://rustup.rs/" -ForegroundColor Yellow
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Build all crates
Write-Host ""
Write-Host "Building all crates..." -ForegroundColor Cyan
Write-Host ""

cargo build --release

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Build successful!" -ForegroundColor Green
Write-Host ""

# Count binaries
$binaries = Get-ChildItem -Path "target\release\*.exe" | Where-Object { $_.Name -notlike "build*" }
Write-Host "Built $($binaries.Count) binaries:" -ForegroundColor Cyan

foreach ($bin in $binaries | Select-Object -First 20) {
    Write-Host "  - $($bin.BaseName)"
}

if ($binaries.Count -gt 20) {
    Write-Host "  ... and $($binaries.Count - 20) more"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Quick Start Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test rustutils:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe --version" -ForegroundColor White
Write-Host ""
Write-Host "2. List all tools:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe list" -ForegroundColor White
Write-Host ""
Write-Host "3. Get tool schemas:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe schema" -ForegroundColor White
Write-Host ""
Write-Host "4. Register a skill:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe skill register crates\skill_registry\examples\analyze_repo.json" -ForegroundColor White
Write-Host ""
Write-Host "5. List skills:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe skill list" -ForegroundColor White
Write-Host ""
Write-Host "6. Run a pipeline:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe pipe '{`"steps`":[{`"tool`":`"fs_scan`",`"args`":[`".`",`"--json`"]}]}'" -ForegroundColor White
Write-Host ""
Write-Host "7. Store memory:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe memory store test_key '{`"value`":`"hello`"}'" -ForegroundColor White
Write-Host ""
Write-Host "8. Recall memory:" -ForegroundColor Yellow
Write-Host "   .\target\release\rustutils.exe memory recall test_key" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
