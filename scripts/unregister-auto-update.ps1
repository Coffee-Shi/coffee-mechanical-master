$ErrorActionPreference = 'Stop'
$TaskName = 'CoffeeMechanicalMasterSkillAutoUpdate'

& schtasks.exe /Delete /F /TN $TaskName | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove scheduled task $TaskName."
}

Write-Output "Removed $TaskName."
