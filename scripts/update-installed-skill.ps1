param(
    [string]$SkillRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$TaskLabel = 'Coffee机械大师自动更新'
$LogDirectory = Join-Path $env:USERPROFILE '.codex\logs'
$LogPath = Join-Path $LogDirectory 'coffee-mechanical-master-update.log'

function Write-UpdateLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$TaskLabel] $Message"
}

function Invoke-RepositoryGit {
    param([string[]]$GitArguments)
    $output = & git -C $SkillRoot @GitArguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return @($output)
}

try {
    $SkillRoot = (Resolve-Path -LiteralPath $SkillRoot).Path
    if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot '.git'))) {
        throw 'The installed skill is not a Git clone; automatic updates require a cloned repository.'
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'git is not available.'
    }
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw 'Python launcher py.exe is not available for update validation.'
    }

    $dirty = Invoke-RepositoryGit @('status', '--porcelain', '--untracked-files=no')
    if ($dirty.Count -gt 0) {
        throw 'Local tracked changes exist; update skipped to preserve them.'
    }

    Invoke-RepositoryGit @('fetch', '--quiet', 'origin', 'main') | Out-Null
    $localSha = (Invoke-RepositoryGit @('rev-parse', 'HEAD'))[0].Trim()
    $remoteSha = (Invoke-RepositoryGit @('rev-parse', 'origin/main'))[0].Trim()
    if ($localSha -eq $remoteSha) {
        exit 0
    }

    $mergeBase = (Invoke-RepositoryGit @('merge-base', 'HEAD', 'origin/main'))[0].Trim()
    if ($mergeBase -ne $localSha) {
        throw 'Local and remote histories diverged; only fast-forward updates are allowed.'
    }

    $validationRoot = Join-Path $env:TEMP ("coffee-master-update-" + [guid]::NewGuid().ToString('N'))
    Invoke-RepositoryGit @('worktree', 'add', '--quiet', '--detach', $validationRoot, 'origin/main') | Out-Null
    try {
        $validator = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-creator\scripts\quick_validate.py'
        if (Test-Path -LiteralPath $validator) {
            & py -3 -X utf8 $validator $validationRoot
            if ($LASTEXITCODE -ne 0) { throw 'Skill structure validation failed.' }
        }
        & py -3 -X utf8 (Join-Path $validationRoot 'scripts\roughness\recommend_ra.py') --self-test
        if ($LASTEXITCODE -ne 0) { throw 'Surface-roughness self-test failed.' }
        & py -3 -X utf8 -m unittest discover -s (Join-Path $validationRoot 'scripts\fits') -p 'test_*.py'
        if ($LASTEXITCODE -ne 0) { throw 'Limits-and-fits tests failed.' }
    }
    finally {
        & git -C $SkillRoot worktree remove --force $validationRoot 2>$null
    }

    Invoke-RepositoryGit @('merge', '--ff-only', 'origin/main') | Out-Null
    Write-UpdateLog "Updated $localSha -> $remoteSha. Codex will detect the local skill change automatically."
    exit 0
}
catch {
    Write-UpdateLog "ERROR: $($_.Exception.Message)"
    exit 1
}
