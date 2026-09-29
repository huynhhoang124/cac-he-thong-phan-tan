$projectRoot = Split-Path -Parent $PSScriptRoot
$logsPath = Join-Path $projectRoot "logs"
$resolvedRoot = [System.IO.Path]::GetFullPath($projectRoot)
$resolvedLogs = [System.IO.Path]::GetFullPath($logsPath)

if (-not $resolvedLogs.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Duong dan logs nam ngoai project: $resolvedLogs"
}

Get-ChildItem -LiteralPath $resolvedLogs -Filter "*.jsonl" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
Write-Host "Da xoa cac file .jsonl trong $resolvedLogs"

