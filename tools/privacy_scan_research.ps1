#!/usr/bin/env pwsh
# Non-destructive privacy scan for research / graphify boundaries.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"
if (-not $ReportPath) {
    $ReportPath = Join-Path $RepoRoot "Research_docs\vendor_research\2026-06-14_agent_frameworks\privacy_scan_report.md"
}

$blockedPatterns = @(
    ".env",
    "oauth-token.json",
    "oauth-client.json",
    "NIZAM-secrets.json",
    "YAWMIYAT__journaling",
    "BADAN__body_health_system\daily_signals",
    "SUKOON__recovery_first",
    "NIZAM__system\ledgers\EVENT_LEDGER.jsonl",
    "TAFRIGH__brain_dumper\raw",
    "SOUL.md"
)

$checks = @()
$failures = @()

foreach ($pat in $blockedPatterns) {
    $full = Join-Path $RepoRoot $pat
    $exists = Test-Path $full
    $checks += [pscustomobject]@{
        Pattern = $pat
        Exists  = $exists
        Status  = if ($exists) { "PRESENT_STRICT_LOCAL" } else { "ABSENT_OR_OK" }
    }
}

$sandbox = Join-Path $RepoRoot "Research_docs\vendor_research\2026-06-14_agent_frameworks"
if (-not (Test-Path $sandbox)) {
    $failures += "Research sandbox missing: $sandbox"
}

$companion = Join-Path $RepoRoot "NIZAM__system\companion"
if (-not (Test-Path $companion)) {
    $failures += "Companion module missing: $companion"
}

$overall = if ($failures.Count -eq 0) { "PASS" } else { "FAIL" }

$lines = @(
    "# Privacy Scan Report",
    "",
    "Generated: $(Get-Date -Format o)",
    "Repo root: $RepoRoot",
    "",
    "## Overall status: **$overall**",
    "",
    "## Blocked path presence (strict-local inventory)",
    "",
    "| Pattern | Exists | Status |",
    "|---------|--------|--------|"
)

foreach ($c in $checks) {
    $lines += "| $($c.Pattern) | $($c.Exists) | $($c.Status) |"
}

$lines += @(
    "",
    "## Failures",
    ""
)
if ($failures.Count -eq 0) {
    $lines += "- None"
} else {
    foreach ($f in $failures) { $lines += "- $f" }
}

$lines += @(
    "",
    "## HIMAYAH rule",
    "",
    "Research and graphify scans must scope to `NIZAM__system/companion/` and `Research_docs/vendor_research/` only.",
    "Never include blocked paths in clone, graphify, or egress operations."
)

$content = $lines -join "`n"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
Set-Content -Path $ReportPath -Value $content -Encoding utf8
Write-Output "Report: $ReportPath"
Write-Output "Status: $overall"
if ($overall -eq "FAIL") { exit 1 }
exit 0
