$projectRoot = Split-Path -Parent $PSScriptRoot
$documentPath = Join-Path $projectRoot "Bao_cao_thuc_hanh_02.docx"
$renderDirectory = Join-Path $projectRoot "tmp\report-render"
$pdfPath = Join-Path $renderDirectory "Bao_cao_thuc_hanh_02.pdf"

New-Item -ItemType Directory -Force -Path $renderDirectory | Out-Null
Get-ChildItem -LiteralPath $renderDirectory -Filter "page-*.png" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
if (Test-Path -LiteralPath $pdfPath) {
    Remove-Item -LiteralPath $pdfPath -Force
}

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($documentPath, $false, $true)
    $document.ExportAsFixedFormat($pdfPath, 17)
}
finally {
    if ($null -ne $document) {
        try { $document.Close($false) } catch {}
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch {}
    }
}

pdftoppm -png -r 120 $pdfPath (Join-Path $renderDirectory "page") | Out-Null
Get-ChildItem -LiteralPath $renderDirectory | Sort-Object Name | Select-Object Name, Length

