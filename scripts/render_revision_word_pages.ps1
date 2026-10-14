$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$taskRoot = Split-Path -Parent $PSScriptRoot
$pageRoot = Join-Path $taskRoot 'tmp\revision_word_preview\pages'
New-Item -ItemType Directory -Path $pageRoot -Force | Out-Null
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$app.DisplayAlerts = 0
$app.AutomationSecurity = 3
$taskDoc = $null
try {
    $taskDoc = $app.Documents.Open((Join-Path $taskRoot 'output\revision_2026_10_13\X_SENTINEL_Report_Revised.docx'), $false, $false, $false)
    if ($taskDoc.Name -ne 'X_SENTINEL_Report_Revised.docx' -or $app.Documents.Count -ne 1) { throw 'Not the exclusive owned revision instance' }
    $app.ActiveWindow.View.Type = 3
    [void]$taskDoc.Fields.Update()
    $taskDoc.Repaginate()
    [void]$taskDoc.Sections.Item(1).Footers.Item(1).Range.Fields.Update()
    $taskDoc.Save()
    $count = $taskDoc.ComputeStatistics(2)
    for ($taskPage = 1; $taskPage -le $count; $taskPage++) {
        [byte[]]$pageBytes = $app.ActiveWindow.Panes.Item(1).Pages.Item($taskPage).EnhMetaFileBits
        $stream = New-Object System.IO.MemoryStream(,$pageBytes)
        $metafile = [System.Drawing.Image]::FromStream($stream)
        $bitmap = New-Object System.Drawing.Bitmap(1600,2263)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($metafile,0,0,1600,2263)
        $bitmap.Save((Join-Path $pageRoot ('page-' + $taskPage + '.png')),[System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose();$bitmap.Dispose();$metafile.Dispose();$stream.Dispose()
        Write-Output ('Rendered actual Word page ' + $taskPage)
    }
    $taskDoc.Close(0)
    $app.Quit()
    Write-Output ('Actual Word pages rendered: ' + $count)
} finally {
    if ($null -ne $taskDoc) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc) }
    [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
}
