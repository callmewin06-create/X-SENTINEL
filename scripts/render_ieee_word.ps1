param([string]$Iteration = '1')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskSource = Join-Path $taskRoot 'output\ieee_2026_10_16\X_SENTINEL_IEEE_1col.docx'
$taskPages = Join-Path $taskRoot ('tmp\ieee_2026_10_16\word-render-' + $Iteration)
New-Item -ItemType Directory -Path $taskPages -Force | Out-Null
$taskWord = New-Object -ComObject Word.Application
$taskOwned = $false
$taskDoc = $null
try {
    if ($taskWord.Documents.Count -ne 0) { throw 'Word instance is not exclusively empty' }
    $taskOwned = $true
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    $taskDoc = $taskWord.Documents.Open($taskSource, $false, $false, $false)
    if ($taskWord.Documents.Count -ne 1 -or $taskDoc.Name -ne 'X_SENTINEL_IEEE_1col.docx') { throw 'Unexpected document ownership' }
    $taskWord.ActiveWindow.View.Type = 3
    [void]$taskDoc.Fields.Update()
    [void]$taskDoc.Fields.Update()
    $taskDoc.Repaginate()
    $taskDoc.Save()
    $taskCount = $taskDoc.ComputeStatistics(2)
    for ($taskPage=1; $taskPage -le $taskCount; $taskPage++) {
        [byte[]]$taskBytes = $taskWord.ActiveWindow.Panes.Item(1).Pages.Item($taskPage).EnhMetaFileBits
        $taskStream = New-Object System.IO.MemoryStream(,$taskBytes)
        $taskMeta = [System.Drawing.Image]::FromStream($taskStream)
        $taskBitmap = New-Object System.Drawing.Bitmap(2550,3300)
        $taskGraphics = [System.Drawing.Graphics]::FromImage($taskBitmap)
        $taskGraphics.Clear([System.Drawing.Color]::White)
        $taskGraphics.DrawImage($taskMeta,0,0,2550,3300)
        $taskBitmap.Save((Join-Path $taskPages ('page-' + $taskPage + '.png')),[System.Drawing.Imaging.ImageFormat]::Png)
        $taskGraphics.Dispose(); $taskBitmap.Dispose(); $taskMeta.Dispose(); $taskStream.Dispose()
        Write-Output ('Rendered page ' + $taskPage)
    }
    Write-Output ('Actual Word pages rendered: ' + $taskCount)
} finally {
    if ($taskOwned) {
        if ($null -ne $taskDoc) { $taskDoc.Close(0) }
        $taskWord.Quit()
    }
    if ($null -ne $taskDoc) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc) }
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord)
}
