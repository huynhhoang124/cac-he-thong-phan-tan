# Chạy 3 node TrustMesh không cần Docker (dự phòng khi Docker Desktop lỗi).
# Dừng một node để thử partial failure: đóng cửa sổ của node đó.
# Khóa node lưu ở .data\ để restart vẫn giữ danh tính (peer đã ghim khóa cũ).
# Đường dẫn tuyệt đối: "& '.venv\...'" bị PowerShell hiểu là tên module.
$venv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$py = if (Test-Path $venv) { $venv } else { "python" }
$nodes = @{ "node-a" = 8001; "node-b" = 8002; "node-c" = 8003 }
foreach ($n in $nodes.Keys) {
    $peers = ($nodes.Keys | Where-Object { $_ -ne $n } | ForEach-Object { "$_=http://localhost:$($nodes[$_])" }) -join ","
    # Set-Location trong lệnh: -WorkingDirectory với đường dẫn có dấu đôi khi không áp dụng → "No module named demo".
    $cmd = "Set-Location -LiteralPath '$PSScriptRoot'; `$env:NODE_ID='$n'; `$env:PEERS='$peers'; `$env:DATA_DIR='.data'; & '$py' -m uvicorn demo.main:app --port $($nodes[$n])"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WorkingDirectory $PSScriptRoot
}
Write-Host "Mở http://localhost:8001"
