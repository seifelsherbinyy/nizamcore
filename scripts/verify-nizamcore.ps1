# Non-destructive NIZAM Core health check.
# Verifies the existing D:\NIZAM install and refreshes install-audit.

param(
    [switch]$SkipNetwork
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "D:\NIZAM"
$Repo = $WorkspaceRoot
$Py = Join-Path $Repo ".venv\Scripts\python.exe"
$Audit = Join-Path $Repo "install-audit"
$StartupReceipt = Join-Path $Audit "startup-receipt.json"
$StatePath = Join-Path $Audit "NIZAM_SETUP_STATE.json"
$Log = Join-Path $Audit ("verify-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

function Log-Line {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $Log -Value $line -Encoding utf8
}

try {
    if (-not (Test-Path $Repo)) { throw "Repo not found: $Repo" }
    if (-not (Test-Path $Py)) { throw "Python venv not found: $Py" }

    New-Item -ItemType Directory -Path $Audit -Force | Out-Null
    Log-Line "NIZAM verification started"

    Set-Location $Repo

    $localHead = (git rev-parse HEAD).Trim()
    $branch = (git branch --show-current).Trim()
    $remoteHead = $null
    $headParityOk = $null
    if (-not $SkipNetwork) {
        $remoteHead = (git ls-remote origin refs/heads/main).Split()[0].Trim()
        $headParityOk = ($localHead -eq $remoteHead)
        if ($branch -eq "main" -and -not $headParityOk) {
            throw "main HEAD mismatch: local=$localHead remote=$remoteHead"
        }
        Log-Line "Git state: branch=$branch local=$localHead remote_main=$remoteHead parity=$headParityOk"
    }
    else {
        Log-Line "Git state: branch=$branch local=$localHead remote check skipped"
    }

    $startupArgs = @("tools\nizam_startup.py", "--json")
    if ($SkipNetwork) { $startupArgs += "--no-net" }

    & $Py @startupArgs | Tee-Object -FilePath $StartupReceipt | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "nizam_startup.py failed with exit code $LASTEXITCODE" }
    $receipt = Get-Content $StartupReceipt | ConvertFrom-Json
    if (-not $receipt.ready) { throw "startup receipt reports ready=false" }
    Log-Line "Startup ready: version=$($receipt.repo.version), gates_ok=$($receipt.repo.gates_ok)"

    Push-Location (Join-Path $Repo "MARSAD__flight_radar")
    & $Py -c "import radar; print('radar OK')" | Add-Content -Path $Log -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "radar import failed" }

    $pytestOutput = & $Py -m pytest -q 2>&1
    $pytestExit = $LASTEXITCODE
    $pytestOutput | Add-Content -Path $Log -Encoding utf8
    Pop-Location
    if ($pytestExit -ne 0) { throw "MARSAD pytest failed" }

    $testCount = 0
    foreach ($line in $pytestOutput) {
        if ($line -match "(\d+) passed") { $testCount = [int]$Matches[1] }
    }
    Log-Line "MARSAD pytest OK: $testCount passed"

    $governorPath = Join-Path $Repo "HIFZ__github_version_control\scripts\nizam_governor_lib.py"
    & $Py -c "import importlib.util; p=r'$governorPath'; spec=importlib.util.spec_from_file_location('nizam_governor_lib', p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('governor_lib OK')" | Add-Content -Path $Log -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "governor lib import failed" }
    Log-Line "Governor lib import OK"

    & (Join-Path $Repo ".venv\Scripts\pip.exe") freeze | Out-File -Encoding utf8 (Join-Path $Audit "pip-freeze.txt")

    $state = [ordered]@{
        timestamp_utc      = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        workspace_root     = $WorkspaceRoot
        repo_path          = $Repo
        remote             = "https://github.com/seifelsherbinyy/nizamcore.git"
        branch             = $branch
        commit_local       = $localHead
        commit_remote_main = $remoteHead
        head_parity_ok     = $headParityOk
        platform_version   = $receipt.repo.version
        startup_ready      = [bool]$receipt.ready
        startup_exit_code  = 0
        python             = $receipt.sandbox.python
        venv               = ".venv"
        requirements_files = @(
            "HIFZ__github_version_control/requirements-governor.txt",
            "MARSAD__flight_radar/requirements.txt"
        )
        pip_freeze_path    = "install-audit/pip-freeze.txt"
        marsad_pytest      = "pass"
        marsad_tests_passed = $testCount
        governor_lib_import = "pass"
        verify_log         = (Split-Path $Log -Leaf)
        notes              = @(
            "doctorhealth not used",
            "no pip package named nizam; use tools/nizam_startup.py and NIZAM_TEMPLE platform_version",
            "no GitHub release tags on remote"
        )
    }
    $state | ConvertTo-Json -Depth 6 | Set-Content -Path $StatePath -Encoding utf8

    Log-Line "Verification complete"
    exit 0
}
catch {
    $message = "Verification failed: $($_.Exception.Message)"
    Write-Error $message
    if (Test-Path $Audit) {
        Add-Content -Path $Log -Value $message -Encoding utf8
    }
    exit 1
}
