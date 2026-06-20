# Non-destructive production env sync + status check

param(
    [switch]$Deploy,
    [switch]$StartPoller
)

$ErrorActionPreference = "Stop"
$Repo = "D:\NIZAM"
$Py = Join-Path $Repo ".venv\Scripts\python.exe"

Set-Location $Repo

& $Py tools\sync_production_env_from_vps.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Deploy) {
    & $Py tools\deploy_nizam_vps.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $Py tools\nizam_production_status.py
$statusCode = $LASTEXITCODE

if ($StartPoller -and $statusCode -eq 0) {
    & $Py tools\nizam_go_live.py --start-poller --require-telegram
    exit $LASTEXITCODE
}

exit $statusCode
