param(
    [string]$AppRoot = "C:\Users\Richard\clawd\OllamaBot"
)

$ErrorActionPreference = "Stop"

$urls = @(
    "http://127.0.0.1:11434/api/tags",
    "http://127.0.0.1:11437/api/tags",
    "http://127.0.0.1:8772/health"
)

$results = @()
foreach ($url in $urls) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5 -ErrorAction Stop
        $results += [PSCustomObject]@{
            url = $url
            status = $resp.StatusCode
            ok = $true
        }
    } catch {
        $results += [PSCustomObject]@{
            url = $url
            status = $null
            ok = $false
        }
    }
}

$results | ConvertTo-Json -Depth 3
