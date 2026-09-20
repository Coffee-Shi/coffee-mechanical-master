param(
    [string]$SkillRoot = (Split-Path -Parent $PSScriptRoot),
    [int]$Minutes = 15
)

$ErrorActionPreference = 'Stop'
$TaskName = 'CoffeeMechanicalMasterSkillAutoUpdate'
$SkillRoot = (Resolve-Path -LiteralPath $SkillRoot).Path
$Updater = Join-Path $SkillRoot 'scripts\update-installed-skill.ps1'

if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot '.git'))) {
    throw 'Automatic updates require the installed skill directory to be a Git clone.'
}
if (-not (Test-Path -LiteralPath $Updater)) {
    throw "Updater not found: $Updater"
}
if ($Minutes -lt 5) {
    throw 'Update interval must be at least 5 minutes.'
}

$PowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$TaskCommand = "`"$PowerShell`" -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Updater`""
& schtasks.exe /Create /F /SC MINUTE /MO $Minutes /TN $TaskName /TR $TaskCommand | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to register scheduled task $TaskName."
}

& $Updater -SkillRoot $SkillRoot
if ($LASTEXITCODE -ne 0) {
    throw 'The scheduled task was registered, but the initial update check failed. See ~/.codex/logs/coffee-mechanical-master-update.log.'
}

Write-Output "Registered $TaskName to check origin/main every $Minutes minutes."
