param(
    [ValidateSet('all', 'plan', 'guide')][string]$Document = 'all',
    [string]$Iteration = '1'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskItems = @(
    @{ Key = 'plan'; Name = 'KE_HOACH_TRIEN_KHAI_VA_DEMO_2026_10_19.docx' },
    @{ Key = 'guide'; Name = 'HUONG_DAN_BODMAS_KALI_2026_10_19.docx' }
)
if ($Document -ne 'all') { $taskItems = @($taskItems | Where-Object { $_.Key -eq $Document }) }
foreach ($taskItem in $taskItems) {
    $taskSource = Join-Path $taskRoot ('output\bodmas_demo_2026_10_19\' + $taskItem.Name)
    $taskPages = Join-Path $taskRoot ('output\bodmas_demo_2026_10_19\documents\' + $taskItem.Key + '-word-' + $Iteration)
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
        if ($taskWord.Documents.Count -ne 1 -or $taskDoc.Name -ne $taskItem.Name) { throw 'Unexpected document ownership' }
        $taskWord.ActiveWindow.View.Type = 3
        [void]$taskDoc.Fields.Update()
        foreach ($taskSection in $taskDoc.Sections) {
            foreach ($taskFooter in $taskSection.Footers) { [void]$taskFooter.Range.Fields.Update() }
        }
        $taskDoc.Repaginate()
        $taskDoc.Save()
        $taskCount = $taskDoc.ComputeStatistics(2)
        $taskPageInfo = @()
        for ($taskPage = 1; $taskPage -le $taskCount; $taskPage++) {
            [byte[]]$taskBytes = $taskWord.ActiveWindow.Panes.Item(1).Pages.Item($taskPage).EnhMetaFileBits
            $taskStream = New-Object System.IO.MemoryStream(,$taskBytes)
            $taskMeta = [System.Drawing.Image]::FromStream($taskStream)
            $taskBitmap = New-Object System.Drawing.Bitmap(1700,2200)
            $taskGraphics = [System.Drawing.Graphics]::FromImage($taskBitmap)
            $taskGraphics.Clear([System.Drawing.Color]::White)
            $taskGraphics.DrawImage($taskMeta,0,0,1700,2200)
            $taskPng = Join-Path $taskPages ('page-' + $taskPage + '.png')
            $taskBitmap.Save($taskPng, [System.Drawing.Imaging.ImageFormat]::Png)
            $taskGraphics.Dispose(); $taskBitmap.Dispose(); $taskMeta.Dispose(); $taskStream.Dispose()
            $taskPageInfo += @{ page = $taskPage; path = $taskPng }
            Write-Output ($taskItem.Key + ': rendered page ' + $taskPage)
        }
        @{ document = $taskSource; renderer = 'Microsoft Word hidden COM instance'; page_count = $taskCount; pages = $taskPageInfo } |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskPages 'render.json') -Encoding utf8
        Write-Output ($taskItem.Key + ': actual Word pages rendered ' + $taskCount)
    } finally {
        if ($taskOwned) {
            if ($null -ne $taskDoc) { $taskDoc.Close(0) }
            $taskWord.Quit()
        }
        if ($null -ne $taskDoc) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc) }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord)
    }
}
