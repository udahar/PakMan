param(
    [string]$AppRoot = "C:\Users\Richard\clawd\OllamaBot",
    [int]$CheckIntervalSeconds = 15
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $AppRoot "logs"
$stateDir = Join-Path $AppRoot "state"
$logFile = Join-Path $logDir "ollamabot_watchdog.log"
$stateFile = Join-Path $stateDir "ollamabot_watchdog_state.json"

New-Item -ItemType Directory -Force -Path $logDir, $stateDir | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [WATCHDOG] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

function Get-HealthSnapshot {
    $script = "C:\Users\Richard\clawd\PakMan\packages\OllamaBotApp\scripts\health.ps1"
    $raw = & $script -AppRoot $AppRoot
    return $raw | ConvertFrom-Json
}

function Save-State {
    param([object]$State)
    $State | ConvertTo-Json -Depth 5 | Set-Content -Path $stateFile -Encoding UTF8
}

$failureCount = 0
Write-Log "watchdog started for $AppRoot"

while ($true) {
    try {
        $snapshot = Get-HealthSnapshot
        $bad = @($snapshot | Where-Object { -not $_.ok })
        if ($bad.Count -eq 0) {
            if ($failureCount -gt 0) {
                Write-Log "stack recovered"
            }
            $failureCount = 0
            Save-State @{
                last_check = (Get-Date).ToString("o")
                failure_count = 0
                status = "healthy"
                bad_urls = @()
            }
        } else {
            $failureCount += 1
            $badUrls = @($bad | ForEach-Object { $_.url })
            Write-Log ("unhealthy endpoints: " + ($badUrls -join ", ")) "WARN"
            Save-State @{
                last_check = (Get-Date).ToString("o")
                failure_count = $failureCount
                status = "degraded"
                bad_urls = $badUrls
            }
            if ($failureCount -ge 2) {
                Write-Log "restarting stack after repeated unhealthy checks" "WARN"
                & "C:\Users\Richard\clawd\PakMan\packages\OllamaBotApp\scripts\start_stack.ps1" -AppRoot $AppRoot | Out-Null
                $failureCount = 0
            }
        }
    } catch {
        $failureCount += 1
        Write-Log ("health probe failed: " + $_.Exception.Message) "ERROR"
    }
    Start-Sleep -Seconds $CheckIntervalSeconds
}
