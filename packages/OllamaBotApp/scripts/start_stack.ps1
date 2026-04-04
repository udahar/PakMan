param(
    [string]$AppRoot = "C:\Users\Richard\clawd\OllamaBot",
    [switch]$SkipGuard
)

$ErrorActionPreference = "Stop"

$manager = "C:\Users\Richard\clawd\PakMan\packages\OllamaOps\ollama_manager.ps1"
$guardLauncher = "C:\Users\Richard\clawd\PakMan\packages\OllamaGuard\start_bridge.ps1"

if (-not (Test-Path $AppRoot)) {
    throw "App root not found: $AppRoot"
}

& $manager -Action start -Ports 11434,11436,11437
if ($LASTEXITCODE -ne 0) {
    throw "OllamaOps start failed"
}

if (-not $SkipGuard) {
    & $guardLauncher
    if ($LASTEXITCODE -ne 0) {
        throw "OllamaGuard bridge failed to start"
    }
}

Write-Output "started:$AppRoot"
