param([int]$Iteration = 1)
$ErrorActionPreference = 'Stop'
if ($Iteration -lt 1) { throw 'Iteration must be positive' }
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskSource = Join-Path $taskRoot 'output\repair_2026_10_23\X_SENTINEL_IEEE_1col_REVISED_2026_10_23.docx'
$taskOut = Join-Path $taskRoot ('outputs\repair_2026_10_23\render-' + $Iteration)
New-Item -ItemType Directory -Path $taskOut -Force | Out-Null
$taskWord = New-Object -ComObject Word.Application
$taskOwned = $false
$taskDoc = $null
try {
    if ($taskWord.Documents.Count -ne 0) { throw 'Word instance contains other documents; not touching them' }
    $taskOwned = $true
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    $taskDoc = $taskWord.Documents.Open($taskSource, $false, $true, $false)
    if ($taskWord.Documents.Count -ne 1 -or $taskDoc.Name -ne 'X_SENTINEL_IEEE_1col_REVISED_2026_10_23.docx') { throw 'Unexpected document ownership' }
    $taskDoc.Repaginate()
    $taskDoc.ExportAsFixedFormat((Join-Path $taskOut 'report.pdf'), 17)
    Write-Output ('Word pages: ' + $taskDoc.ComputeStatistics(2))
} finally {
    if ($taskOwned) {
        if ($null -ne $taskDoc) { $taskDoc.Close(0) }
        $taskWord.Quit()
    }
    if ($null -ne $taskDoc) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc) }
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord)
}
