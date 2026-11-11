# Chạy Sổ điểm DS: 3 node ở 9001-9003, độc lập với demo TrustMesh (8001-8003).
# Dừng một node để thử partial failure: đóng cửa sổ của node đó.
# Khóa node lưu ở .data-sodiem\ để restart vẫn giữ danh tính (peer đã ghim khóa cũ).
# Đường dẫn tuyệt đối: "& '.venv\...'" bị PowerShell hiểu là tên module.
$venv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$py = if (Test-Path $venv) { $venv } else { "python" }
$nodes = @{ "node-a" = 9001; "node-b" = 9002; "node-c" = 9003 }
foreach ($n in $nodes.Keys) {
    $peers = ($nodes.Keys | Where-Object { $_ -ne $n } | ForEach-Object { "$_=http://localhost:$($nodes[$_])" }) -join ","
    # Set-Location trong lệnh: -WorkingDirectory với đường dẫn có dấu đôi khi không áp dụng → "No module named sodiem".
    $cmd = "Set-Location -LiteralPath '$PSScriptRoot'; `$env:NODE_ID='$n'; `$env:PEERS='$peers'; `$env:DATA_DIR='.data-sodiem'; & '$py' -m uvicorn sodiem.main:app --port $($nodes[$n])"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WorkingDirectory $PSScriptRoot
}
Write-Host "Mở http://localhost:9001"
