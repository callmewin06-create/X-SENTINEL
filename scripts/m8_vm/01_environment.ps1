# Read-only inventory. No binary execution, downloads or security changes.
param([string]$OutputDirectory = "$env:USERPROFILE\Desktop\XSENTINEL_M8_REPORT")
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$os = Get-WmiObject Win32_OperatingSystem
$report = [ordered]@{
    Stage = 'environment_only'; UTC = [DateTime]::UtcNow.ToString('o')
    OS = $os.Caption; Version = $os.Version; Build = $os.BuildNumber
    Architecture = $os.OSArchitecture; Is64Bit = [Environment]::Is64BitOperatingSystem
    PowerShell = $PSVersionTable.PSVersion.ToString()
    MalwareExecuted = $false; FunctionalValidation = 'NOT_RUN'
    FrameworkDirectories = @(Get-ChildItem "$env:WINDIR\Microsoft.NET\Framework*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
}
$report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory 'environment.json')
Write-Output "Environment report: $OutputDirectory"
if (-not [Environment]::Is64BitOperatingSystem) { Write-Warning 'x86 guest cannot run the current x64 native fixture.' }
