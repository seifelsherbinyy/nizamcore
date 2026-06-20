# Non-destructive local go-live activation for NIZAM.
# Sets approval gates, runs smoke checks, and optionally starts the Telegram poller.

param(
    [switch]$PollOnce,
    [switch]$StartPoller,
    [switch]$RequireTelegram,
    [switch]$RequireModel
)

$ErrorActionPreference = "Stop"
$Repo = "D:\NIZAM"
$Py = Join-Path $Repo ".venv\Scripts\python.exe"

if (-not (Test-Path $Py)) {
    throw "Python venv not found: $Py"
}

Set-Location $Repo

$argsList = @("tools\nizam_go_live.py")
if ($PollOnce) { $argsList += "--poll-once" }
if ($StartPoller) { $argsList += "--start-poller" }
if ($RequireTelegram) { $argsList += "--require-telegram" }
if ($RequireModel) { $argsList += "--require-model" }

& $Py @argsList
exit $LASTEXITCODE
