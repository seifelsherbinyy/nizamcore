# Local browser trial

Owner: KDE contract Phase 1. Browser engine: https://github.com/microsoft/playwright.
Pinned package: playwright-core 1.63.0; Node >=20 upstream, Node 24 here.

From the repository root, with an actual Node 24 runtime:

```text
npm ci --prefix scripts/kiro --ignore-scripts --no-audit --no-fund
npm run build
node scripts/kiro/browser-smoke.mjs
```

Set NIZAM_BROWSER_EXECUTABLE in the invoking process to an existing Chromium-compatible
browser executable. Do not put a workstation path in tracked configuration. The runner
fails if absent. It does not install a browser or attach to an existing profile.

The runner owns a temporary browser context and a loopback static server over dist only.
It blocks browser requests outside that origin, bypasses no certificate checks and closes
owned resources. It verifies navigation and reload on empty local state, not financial
math, production health, persistent login, offline PWA behavior or complete UI coverage.
A failure exits nonzero; diagnose the sanitized phase error before modifying code.

For a new browser regression, add a deterministic assertion under the owning app contract
rather than teaching the skill to declare success. No personal storage-state import, real
ledger, provider login, downloads, browser-wide shutdown or cloud upload in smoke trials.

Selection: @playwright/cli 0.1.20 was inspected but not selected because its direct engine
dependencies are alpha releases. The stable core plus this small runner avoids that and
requires no MCP service. Package install uses a separate lockfile outside the app manifest.
