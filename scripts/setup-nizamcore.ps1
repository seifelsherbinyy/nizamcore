# NIZAM Core local setup — idempotent installer
# Target: D:\NIZAM (not doctorhealth)
# Requires: git, py -3.12

param(
    [switch]$SkipPlaywright
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "D:\NIZAM"
$RepoPath      = $WorkspaceRoot
$Remote        = "https://github.com/seifelsherbinyy/nizamcore.git"
$Branch        = "main"
$AuditDir      = Join-Path $RepoPath "install-audit"
$VenvPython    = Join-Path $RepoPath ".venv\Scripts\python.exe"
$VenvPip       = Join-Path $RepoPath ".venv\Scripts\pip.exe"
$VenvPytest    = Join-Path $RepoPath ".venv\Scripts\pytest.exe"
$VenvPlaywright = Join-Path $RepoPath ".venv\Scripts\playwright.exe"

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    throw "Canonical checkout not found at $RepoPath. Clone it manually before running setup."
}

New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null
$LogFile = Join-Path $AuditDir ("setup-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Start-Transcript -Path $LogFile | Out-Null

Set-Location $RepoPath
$LocalHead  = (git rev-parse HEAD).Trim()
$RemoteHead = (git ls-remote origin refs/heads/main).Split()[0].Trim()
if ($LocalHead -ne $RemoteHead) {
    throw "HEAD mismatch: local=$LocalHead remote=$RemoteHead"
}
Write-Host "HEAD parity OK: $LocalHead"

py -3.12 -m venv .venv
& $VenvPython -m pip install --upgrade pip wheel
& $VenvPip install -r HIFZ__github_version_control\requirements-governor.txt `
    -r MARSAD__flight_radar\requirements.txt

if (-not $SkipPlaywright) {
    & $VenvPlaywright install chromium
}

& $VenvPip freeze | Out-File -Encoding utf8 (Join-Path $AuditDir "pip-freeze.txt")
& $VenvPython tools\nizam_startup.py --json | Out-File -Encoding utf8 (Join-Path $AuditDir "startup-receipt.json")
if ($LASTEXITCODE -ne 0) { throw "nizam_startup.py failed with exit $LASTEXITCODE" }

Push-Location MARSAD__flight_radar
& $VenvPython -c "import radar; print('radar OK')"
& $VenvPytest -q
if ($LASTEXITCODE -ne 0) { throw "MARSAD pytest failed" }
Pop-Location

$excludeFile = Join-Path $RepoPath ".git\info\exclude"
if (-not (Select-String -Path $excludeFile -Pattern "install-audit" -Quiet -ErrorAction SilentlyContinue)) {
    Add-Content -Path $excludeFile -Value "install-audit/"
}

$temple = Get-Content NIZAM_TEMPLE.json | ConvertFrom-Json
$receipt = Get-Content (Join-Path $AuditDir "startup-receipt.json") | ConvertFrom-Json
$state = [ordered]@{
    timestamp_utc        = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    workspace_root       = $WorkspaceRoot
    repo_path            = $RepoPath
    remote               = $Remote
    branch               = $Branch
    commit_local         = $LocalHead
    commit_remote_main   = $RemoteHead
    head_parity_ok       = $true
    platform_version     = $temple.platform_version
    startup_ready        = $receipt.ready
    startup_exit_code    = 0
    python               = $receipt.sandbox.python
    venv                 = ".venv"
    requirements_files   = @(
        "HIFZ__github_version_control/requirements-governor.txt",
        "MARSAD__flight_radar/requirements.txt"
    )
    pip_freeze_path      = "install-audit/pip-freeze.txt"
    marsad_pytest        = "pass"
    notes                = @(
        "doctorhealth not used",
        "no pip package named nizam",
        "no GitHub release tags on remote"
    )
}
$state | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $AuditDir "NIZAM_SETUP_STATE.json")

Stop-Transcript | Out-Null
Write-Host "Setup complete. Audit: $AuditDir"
