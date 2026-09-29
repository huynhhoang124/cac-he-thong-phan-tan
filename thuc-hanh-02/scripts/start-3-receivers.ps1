$projectRoot = Split-Path -Parent $PSScriptRoot
for ($index = 1; $index -le 3; $index++) {
    $command = "Set-Location -LiteralPath '$projectRoot'; python -m multicast.receiver --name receiver-$index"
    Start-Process powershell.exe -WindowStyle Normal -ArgumentList @(
        "-NoExit",
        "-Command",
        $command
    )
}

