$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$previewDir = Join-Path $taskRoot 'tmp\report_1_ieee\render'
New-Item -ItemType Directory -Path $previewDir -Force | Out-Null
$wordApp = $null
$openedDoc = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    $pairs = @(
        @{Input = 'C:\Users\win9tui\Downloads\Report (1).docx'; Output = 'source.pdf'},
        @{Input = (Join-Path $taskRoot 'output\docx\Report_1_IEEE_References.docx'); Output = 'revised.pdf'}
    )
    foreach ($pair in $pairs) {
        $openedDoc = $wordApp.Documents.Open($pair.Input, $false, $true, $false)
        $openedDoc.Repaginate()
        $openedDoc.ExportAsFixedFormat((Join-Path $previewDir $pair.Output), 17)
        Write-Output ($pair.Output + ': ' + $openedDoc.ComputeStatistics(2) + ' pages')
        $openedDoc.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($openedDoc)
        $openedDoc = $null
    }
}
finally {
    if ($null -ne $openedDoc) {
        $openedDoc.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($openedDoc)
    }
    if ($null -ne $wordApp) {
        $wordApp.Quit(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordApp)
    }
}
