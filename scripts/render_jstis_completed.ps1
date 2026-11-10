$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPath = Join-Path $taskRoot 'output/jstis_revision_2026_11_10/X_SENTINEL_Anonymous_Completed_M3_2026_11_10.docx'
$taskPdf = Join-Path $taskRoot 'output/jstis_revision_2026_11_10/native_preview.pdf'
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
$app.AutomationSecurity = 3
$doc = $null
try {
    $doc = $app.Documents.Open($taskPath, $false, $true)
    $doc.ExportAsFixedFormat($taskPdf, 17)
    $doc.Close(0)
    $doc = $null
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    $app.Quit()
}
