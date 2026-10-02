# External capability evaluation

Owner: KDE contract Phase 1. Sources inspected 2026-09-16. No popularity benchmark claims.
Ranks below are engineering selection judgments, not measured performance scores.

## Installed

**playwright-core 1.63.0** from https://github.com/microsoft/playwright.
Stable release: https://github.com/microsoft/playwright/releases/tag/v1.63.0, published
2026-09-04; API reports prerelease=false and draft=false.
Package metadata: https://registry.npmjs.org/playwright-core/1.63.0.
Apache-2.0; Node >=20; no declared runtime dependencies or lifecycle scripts. Exact package
and integrity are recorded in scripts/kiro/package-lock.json. Installed with lifecycle
scripts disabled into developer tooling only. Browser access has user-process privileges;
our runner uses a fresh profile/context, Chromium sandbox, local build and blocked external
requests/WebSockets. It is not a hostile-code containment boundary or browser-wide firewall.
No provider auth, personal profile or additional browser download is used.
Observed local trial: actual app navigation across three routes plus reload; no page/console
errors or attempted external requests. Kiro activation remains unverified.

## Ranked alternatives and rejected/deferred scope

| Candidate | Current source evidence | Decision / concrete trade-off |
|---|---|---|
| https://github.com/microsoft/playwright-cli | v0.1.20 package; commit 12228454ed024c9ac89abd59df3b706ed9135fd9, 2026-09-14 | Not installed. Direct dependencies are 1.64.0-alpha-2026-09-14. Tarball integrity matched; inspected wrapper and skill. Stable core is sufficient for our smoke trial. |
| https://github.com/github/github-mcp-server | v1.12.2 release 2026-09-16; MIT; active commit/release history | Conditional. Compare native Git/gh first. Credentialed toolsets and actual Kiro transport need a separate trial; no token creation or broad repository write grant. |
| https://github.com/upstash/context7 | MCP 4.1.1 release 2026-09-14; MIT | Deferred. Public official-doc retrieval works for this research. Setup shortcut creates OAuth/key state; do not run it. Backend is not fully open source; external queries require data minimization. |
| https://github.com/obra/superpowers | v6.3.0 release 2026-08-12; MIT | Reference only. Local debugging workflow uses general hypothesis/test practice; no upstream code/text copied or plugin activated. Whole orchestration duplicates native tools and introduces incompatible task/commit assumptions. |
| https://github.com/microsoft/playwright-mcp | v0.0.81 release 2026-09-14; Apache-2.0 | Deferred. Upstream explicitly distinguishes CLI versus MCP trade-offs. Additional service/tool schemas are unnecessary for our current smoke checks. |
| https://github.com/kirodotdev/powers | commit 72497ed35129ddb451cef28556143f7ec6ff69c3, 2026-09-14 | Packaging/reference source only. No matching bundle justifies installation. Check per-Power licensing, not a blanket assumed license. |
| https://github.com/anthropics/skills | commit 34040c9c568585f6929bedeaad110ad08f079624, 2026-09-10 | Reference pool only; per-skill licensing and tool-specific commands need review. No wholesale import. |
| https://github.com/modelcontextprotocol/servers | release 2026.8.31; maintenance commit 2026-09-03 | No filesystem/Git/fetch/memory server installation; duplicates native capabilities. |
| https://github.com/docker/mcp-gateway | commit a21c0ac1c1e7a9f01a4b713a40d9a3b4c32d722b, 2026-08-26; MIT | Deferred. Adds Docker/gateway lifecycle for a tiny tool set; does not itself provide VPS diagnosis. |
| https://github.com/tufantunc/ssh-mcp | commit 41729d3d820f12dba849d2ea2ce1d3cfb56824b9, 2026-09-15; MIT | Deferred. Existing native SSH avoids another credential/session broker. Not security-audited or installed. |
| https://github.com/Harsh-2002/SSH-MCP | commit 378d2eaf1d11ccb66ff1a0c78d87be1210fc9573, 2026-02-17 | Rejected for baseline. README describes automatic key generation, broad operations and another service. License API and README need reconciliation before reuse. |
| https://github.com/purelyKai/kiro-power-playwright | commit 2ba9ecc52846c7c6a0587af000d05b09d0933af0, 2026-04-17 | Not selected. Extra wrapper and no established license/maintenance advantage over original tooling. |

Discovery catalogs (not trusted installers): https://github.com/VoltAgent/awesome-agent-skills
and https://github.com/punkpeye/awesome-mcp-servers. Both showed updates on 2026-09-15.

## Practical reports and limits

- https://github.com/kirodotdev/Kiro/issues/6193: closed report of CLI registry initialization
  failure despite a working standalone Playwright server. This is not our IDE/version.
- https://github.com/kirodotdev/Kiro/issues/5452: older CLI transport/content-type regression.
- https://github.com/microsoft/playwright-mcp/issues/1754: Windows persistent-profile download
  failure report. Our runner neither downloads nor uses a persistent personal profile.
- https://github.com/github/github-mcp-server/issues/3281: approval annotation complaint.
- https://github.com/upstash/context7/issues/3196: report of incorrect/missing indexed docs.

These are user reports, not reproduced defects here. Reddit/developer-community searches
were performed; no repeated, independently substantiated recommendation establishes a
performance or security claim in this report. Primary source and local trials decide.
Stars/forks were inspected as adoption signals; they are not maintenance or security proof.
Open issue counts include PRs in API metadata, and some repositories redirect issue filing.

## Admission/update checklist

For any later install: exact identity/revision; original docs; license; meaningful release
and contributor activity; issue handling; scripts/transitives; runtime; filesystem/shell/
network/credential scope; native duplication; smallest alternative; Kiro version and real
activation trial. Unvalidated candidates remain deferred. Never use @latest in a persisted
executable config. Review lockfile diffs and repeat tests before promotion.
