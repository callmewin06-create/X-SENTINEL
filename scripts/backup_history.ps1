param([string]$DockerCommand = 'docker')
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectPath
try {
    $backupFolder = Join-Path $projectPath 'backups'
    New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
    $backupName = 'history_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.dump'
    $backupDestination = Join-Path $backupFolder $backupName
    if (Test-Path -LiteralPath $backupDestination) { throw 'Backup path already exists' }
    & $DockerCommand compose exec -T postgres pg_dump -U xsentinel -d xsentinel -Fc -f /tmp/xsentinel-history.dump
    if ($LASTEXITCODE -ne 0) { throw 'Database backup failed' }
    & $DockerCommand compose cp postgres:/tmp/xsentinel-history.dump $backupDestination
    if ($LASTEXITCODE -ne 0) { throw 'Copying backup failed' }
    if ((Get-Item -LiteralPath $backupDestination).Length -eq 0) { throw 'Empty backup' }
    Write-Output ('Backup saved: ' + $backupDestination)
} finally {
    Pop-Location
}
