param([string]$Iteration = '1')
$ErrorActionPreference = 'Stop'
if ($Iteration -notmatch '^\d+$') { throw 'Iteration must be numeric' }
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskSource = Join-Path $taskRoot 'output\bodmas_2026_10_23\X_SENTINEL_IEEE_1col_BODMAS_2026_10_23.docx'
$taskOut = Join-Path $taskRoot ('outputs\bodmas_2026_10_23\word-render-' + $Iteration)
New-Item -ItemType Directory -Path $taskOut -Force | Out-Null
$taskPdf = Join-Path $taskOut 'report.pdf'
$taskWord = New-Object -ComObject Word.Application
$taskOwned = $false
$taskDoc = $null
try {
    if ($taskWord.Documents.Count -ne 0) { throw 'Word instance contains other documents; not touching them' }
    $taskOwned = $true
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    # Read-only: rendering must not reserialize the verified OOXML package.
    $taskDoc = $taskWord.Documents.Open($taskSource, $false, $true, $false)
    if ($taskWord.Documents.Count -ne 1 -or $taskDoc.Name -ne 'X_SENTINEL_IEEE_1col_BODMAS_2026_10_23.docx') {
        throw 'Unexpected document ownership'
    }
    $taskDoc.Repaginate()
    $taskCount = $taskDoc.ComputeStatistics(2)
    $taskDoc.ExportAsFixedFormat($taskPdf, 17)
    Write-Output ('Word pages: ' + $taskCount)
    Write-Output ('QA PDF: ' + $taskPdf)
} finally {
    if ($taskOwned) {
        if ($null -ne $taskDoc) { $taskDoc.Close(0) }
        $taskWord.Quit()
    }
    if ($null -ne $taskDoc) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc) }
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord)
}
