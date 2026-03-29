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

$listening = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:11435\s+\S+\s+LISTENING\s+(\d+)\s*$" | Select-Object -First 1
if (-not $listening) {
    $stdout = Join-Path $AppRoot "logs\ollamabot_stdout.log"
    $stderr = Join-Path $AppRoot "logs\ollamabot_stderr.log"
    Start-Process -FilePath node `
        -ArgumentList "src/server.js" `
        -WorkingDirectory $AppRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr | Out-Null
    Start-Sleep -Seconds 3
}

Write-Output "started:$AppRoot"

