#requires -Version 5.1
# Static inventory only. This script never starts samples.
param([Parameter(Mandatory=$true)][string]$SampleDirectory,
      [string]$OutputDirectory = "$env:USERPROFILE\Desktop\XSENTINEL_M8_REPORT")
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$rows = foreach ($file in Get-ChildItem -LiteralPath $SampleDirectory -File -Recurse -Filter '*.exe') {
    $status = 'OK'; $machine = ''; $message = ''
    try {
        $stream = [IO.File]::OpenRead($file.FullName)
        try {
            $reader = New-Object IO.BinaryReader($stream)
            if ($reader.ReadUInt16() -ne 0x5A4D) { throw 'Missing MZ signature' }
            $stream.Position = 0x3c; $pe = $reader.ReadUInt32()
            $stream.Position = $pe
            if ($reader.ReadUInt32() -ne 0x00004550) { throw 'Missing PE signature' }
            $machine = ('0x{0:X4}' -f $reader.ReadUInt16())
        } finally { $stream.Dispose() }
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    } catch { $status = 'ERROR'; $message = $_.Exception.Message; $hash = '' }
    [pscustomobject]@{ Path=$file.FullName; Bytes=$file.Length; SHA256=$hash; Machine=$machine;
        StaticStatus=$status; Error=$message; FunctionalStatus='NOT_RUN'; Label='UNVERIFIED' }
}
@($rows) | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'binary_inventory.csv')
Write-Output "Inventory saved in $OutputDirectory. No functionality or malware labels inferred."
