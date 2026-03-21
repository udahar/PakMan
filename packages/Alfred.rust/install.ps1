#!/usr/bin/env powershell
# Rust Utilities Installer
# Installs all Rust utilities to the specified directory

param(
    [string]$InstallDir = "$env:USERPROFILE\.cargo\bin",
    [switch]$BuildRelease,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "  Rust Utilities Installer"
Write-Host "========================================"
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RustDir = $ScriptDir

# Check if Rust directory exists
if (-not (Test-Path $RustDir)) {
    Write-Host "Error: Rust directory not found: $RustDir" -ForegroundColor Red
    exit 1
}

# Check if cargo is available
try {
    $cargoVersion = cargo --version 2>&1
    Write-Host "Cargo found: $cargoVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Cargo not found. Please install Rust first." -ForegroundColor Red
    exit 1
}

# Create install directory if it doesn't exist
if (-not (Test-Path $InstallDir)) {
    Write-Host "Creating install directory: $InstallDir"
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

# Build all utilities
Write-Host ""
Write-Host "Building utilities..." -ForegroundColor Cyan

$buildArgs = @("build")
if ($BuildRelease) {
    $buildArgs += "--release"
}

Set-Location $RustDir
& cargo @buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Determine target directory
$targetDir = if ($BuildRelease) { "release" } else { "debug" }
$targetPath = Join-Path $RustDir "target\$targetDir"

# Get all executables
$executables = Get-ChildItem -Path $targetPath -Filter *.exe | 
    Where-Object { $_.Name -ne "build.rs" }

Write-Host ""
Write-Host "Found $($executables.Count) utilities:" -ForegroundColor Green

foreach ($exe in $executables) {
    Write-Host "  - $($exe.BaseName)"
}

# Install utilities
if (-not $DryRun) {
    Write-Host ""
    Write-Host "Installing to: $InstallDir" -ForegroundColor Cyan
    
    foreach ($exe in $executables) {
        $dest = Join-Path $InstallDir $exe.Name
        Copy-Item -Path $exe.FullName -Destination $dest -Force
        Write-Host "  ✓ Installed: $($exe.BaseName)" -ForegroundColor Green
    }
    
    # Add to PATH if not already there
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$InstallDir*") {
        Write-Host ""
        Write-Host "Adding $InstallDir to PATH..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable(
            "Path",
            "$currentPath;$InstallDir",
            "User"
        )
        Write-Host "PATH updated. Restart your terminal for changes to take effect."
    }
} else {
    Write-Host ""
    Write-Host "DRY RUN - No files installed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage examples:" -ForegroundColor Cyan
Write-Host "  fs_scan C:\path\to\scan --json"
Write-Host "  json_fmt input.json --output formatted.json"
Write-Host "  queue_processor tasks.json --interval 5"
Write-Host "  file_watch C:\path\to\watch --command 'cargo build'"
Write-Host ""
