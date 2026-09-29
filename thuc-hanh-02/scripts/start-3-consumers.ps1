param(
    [ValidateSet("persistent", "transient")]
    [string]$Mode = "persistent"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
for ($index = 1; $index -le 3; $index++) {
    $command = "Set-Location -LiteralPath '$projectRoot'; python -m rabbitmq.consumer --name consumer-$index --mode $Mode"
    Start-Process powershell.exe -WindowStyle Normal -ArgumentList @(
        "-NoExit",
        "-Command",
        $command
    )
}

