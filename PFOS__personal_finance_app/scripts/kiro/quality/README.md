# Local quality tools

Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 3-6.

Run from repository root with Node 24.14.1 (not the Aki node/Bun alias):

```text
npm test --prefix scripts/kiro/quality
node scripts/kiro/quality/mutation.mjs
node scripts/kiro/quality/accessibility.mjs
```

Accessibility requires NIZAM_BROWSER_EXECUTABLE pointing to an existing browser and a
fresh `npm run build`. It opens only a fresh headless context against loopback, blocks
external requests and scans empty app state. It does not use your browser profile.
A nonzero result with route/rule IDs means unresolved app findings, not a broken install.
No axe rules are suppressed. Incomplete results require manual review.

Mutation only tests a synthetic attempt boundary in an owned ~/.aki/tmp/kde-mutation-*
folder. Inspect run.log and mutation.json there. No production file is mutated. This is
an installation/control trial, not an application-wide mutation score. The outer timeout
is a stop bound, not a hostile-process sandbox; inspect any owned children after a timeout.

The separate lock pins fast-check 4.10.1, axe-core 4.13.0, Stryker 10.0.0 and patched
transitive qs 6.16.0. It reuses Playwright from the parent developer package. Installation
is authorized for this increment; future changes still require inspected pins. Reproduce
only when needed with `npm ci --prefix scripts/kiro/quality --ignore-scripts --no-audit --no-fund`.
No installation is triggered by tests or application startup. No global configuration.

Full research and observed limitations: docs/kiro/operational-excellence/blueprint.md.
