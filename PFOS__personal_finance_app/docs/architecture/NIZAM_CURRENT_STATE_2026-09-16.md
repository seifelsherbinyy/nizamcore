# NIZAM: current specifications, architecture and gaps

Prepared: 2026-09-16. Evidence snapshot: local working tree at HEAD `5652edf`, plus explicitly dated repository receipts.
Scope: owner-requested research and information preparation. This report is evidence, not a contract amendment, deployment authorization or production-readiness certificate.

## 1. Executive assessment

**NIZAM is a substantial implemented finance application and a partially integrated personal operating assistant, not an empty prototype and not a fully verified live system.**

Three layers must be kept distinct:

1. **Profile-A finance PWA:** private, single-user, offline-first budgeting and financial decision support. Real React screens and deterministic engines exist.
2. **PFOS server tier:** Node/TypeScript, SQLite, ingestion, queues, signals, model governance and operational components exist locally. Local implementation does not establish deployed revision parity.
3. **NIZAMCORE + Hermes assistant:** life management, journaling, planning, health/recovery, continuity and financial read tools. Native Python life code lives in a separate repository. Current restoration, daily companion and dual-channel memory work is largely offline preparation, not completed live integration.

The most important gaps are plaintext browser-to-Drive persistence, unresolved native ingress/tool boundaries, incomplete durable capture, incomplete end-to-end financial intake, FX history handling, and stale or fragmented readiness evidence. The working tree is not release-clean.

## 2. What it does

### Implemented finance product

| User need | Existing implementation |
|---|---|
| Give every unit of income a job | Zero-based monthly budgeting, category groups, assigned/activity/available, rollover, credit handling and targets |
| See and reconcile accounts | Bank/credit/cash/tracking accounts, register, clearance, transfers, splits, reconciliation and corrections |
| Bring in statements | Master-ledger CSV parsing, preview, exact/fuzzy deduplication and explicit import commit |
| Know what can safely be spent | Deterministic eight-term reserve waterfall, protected obligations, living reserve, liquidity buffer and uncertainty |
| Understand upcoming pressure | Obligations and scheduled cash-flow forecasts; baseline/downside/upside scenarios; next-day through multi-year horizons |
| Evaluate a purchase | Hypothetical outflow passed through existing finance engines |
| Learn from decisions | Append-only decision registry and expected-versus-observed outcomes |
| Understand wealth | Nominal/liquid/liquidation/real views, assets and rational FX conversion |
| Review overall finances | Spending, net worth, Age of Money and Egypt-context rescue analytics |
| Work offline | IndexedDB cache, local-first boot and installable PWA with local-asset precaching |

Twelve routes are mounted in `src/App.tsx:74-86`: Home, Budget, Accounts, Reports, Import, Reconcile, Decide, Forecast, Decisions, Net worth, Obligations and Settings. This is source-level wiring, not a fresh interactive audit of every screen.

### Assistant scope and intended experience

The daily-companion spec names ten pillars:

- **HIMAYAH:** privacy and safety gates.
- **SUKOON:** recovery/capacity-aware downshifting.
- **BADAN:** approved health/routine context.
- **THABAT:** commitments and continuity.
- **SHURA:** planning and deliberation.
- **NAQD:** critique, constrained by capacity.
- **YAWMIYAT:** journal/reflection.
- **TAFRIGH:** unloading and capture.
- **QARAR:** decisions.
- **MAL/PFOS:** deterministic financial facts and alerts.

Morning/midday/evening/weekly check-ins, quiet hours, pause, snooze and bounded question selection have an offline reference implementation. This does **not** mean ten working native adapters or live scheduled delivery exist. Sources are injected and unavailable until approved native wiring is supplied.

Telegram restoration specifies one private text conversation, English/Arabic routing, durable intake, honest received/answered/saved states, cancellation and supported PFOS reads. Voice, attachments, Mini App and financial writes are outside that initial increment.

Sources: `src/App.tsx`; `src/features/safeToSpend/safeToSpend.ts:35-44`; `src/features/forecast/forecast.ts:19-26`; `.kiro/specs/telegram-daily-companion/design.md:56-85`; `.kiro/specs/telegram-window/{requirements,design}.md`.

## 3. Where and how it lives

```text
Owner browser / installed PWA
  React views -> Zustand -> deterministic finance engines
                      <-> Dexie / IndexedDB working data
                      <-> Profile-A Drive JSON adapter [plaintext gap]

Owner conversational channel
  Contract-14 v2: Slack Socket Mode
  New Telegram / dual-channel versions: preparation, not accepted live cutover
      -> host-native Hermes gateway
      -> native NIZAM governance and bounded tools
          -> life / journal / continuity: separate Python nizamcore repository
          -> finance: PFOS Node 24 / TypeScript + finance.db
          -> consent-controlled signal bus: bounded state, not raw ledgers

Server storage design
  life.db | finance.db | signals.db, separate ownership
  SQLite snapshot -> encrypted archive -> Drive (drive.file)
  Keys/secrets remain outside Drive and Git
```

| Layer | Location / technology | Evidence limit |
|---|---|---|
| Development checkout | Current Windows NIZAM workspace; finance repository identified in steering as nizamfinancialapp | HEAD alone omits protected uncommitted work |
| Browser application | React 18.3.1, TypeScript, Vite 5.4.11, Zustand 5.0.2, Dexie 4.0.10, Zod 3.24.1 | Package versions inspected locally |
| Local app data | In-memory Zustand plus browser IndexedDB; JSON schema version 9 | Clearing browser storage can affect unsynced data; no real data inspected |
| Profile-A canonical sync design | One `nizam_db.json`, snapshots and three-way merge under drive.file | Current browser implementation is not application-encrypted |
| Finance server | Node 24, native node:sqlite, WAL/foreign keys, strict integer schema, eight ordered checksum-protected migrations | Implemented locally; live schema/version not rechecked |
| Life subsystem | Separate nizamcore repository, Python native governance/relay/writers | Inspected through existing dated receipts only in this session |
| Persistent compute | OVHcloud VPS in project design; recent receipts establish actual host services | No fresh SSH/provider probe performed for this report |
| Hermes | Host-native gateway supervised by systemd in the Sept 15 receipt; another candidate gateway process also observed | Sole intended bot consumer and effective loaded tool restrictions unresolved |
| Container topology | Templates for proxy, life, finance, signalbus, scheduler and backup | Sept 11 observed seven running containers; do not map them to template roles by count |
| App access on server | Existing appServer is loopback-only static serving through an authenticated administrative tunnel | It is explicitly not a finance API and opens no database |
| Cloudflare | DNS role; ADR-0003 permits stateless Workers/static hosting as a hybrid | Ledger storage in Cloudflare D1/R2/KV/Durable Objects not adopted; Access deferred; Worker deployment not proven |
| Source repositories | Public-source posture is recorded in steering | Private single-user application does not mean private Git repositories; deployment particulars must remain untracked |

**Important:** serving the PWA from the VPS does not make its browser ledger the server SQLite ledger. `src/state/store.ts` uses Dexie/Drive; `src/server/process/appServer.ts:14-25` serves static files and explicitly has no data API. A shared, current end-to-end source-of-truth bridge is not established by these components existing.

Local package commands are `npm run dev`, `npm run build`, `npm run preview`; dev/preview are configured on port 5173. This report did not start either server or connect Google Drive.

Sources: `package.json`; `vite.config.ts`; `src/state/store.ts:8-24`; `src/lib/db/schema.ts:57,435-478`; `src/server/db/{schema,migrations}.ts`; `ops/docker-compose.yml` (template only); `docs/adr/ADR-0003-post-ynab-architecture.md:26-68`.

## 4. Governing specifications and actual status

Do not confuse the original numbered build contracts, PFOS contracts, and the seven recovery-program workstreams.

| Contract/spec family | Governs | Current interpretation |
|---|---|---|
| Original build C1-C5 | Foundation, Drive, budget engine, UI, reports/release | Historical implementation marked done; not a whole-system live-readiness declaration |
| PFOS 01-04 | Product constitution, data/security, financial intelligence, UX | Retained product blueprints; finance runtime language is overridden by server steering |
| PFOS 05 + baseline addendum | Agent orchestration, knowledge/tools and capability evidence | Contracts exist; older missing-05 prose is stale. Baseline report implemented, native capture reconciliation blocked |
| PFOS 06 | SQLite, isolation, knowledge, spend persistence | Contract and server modules exist; older missing-06 next-step text is stale |
| PFOS 09-11 | Model benchmark, routing and cost/quality governance | Local modules exist. No live eligibility, prices or provider caps freshly certified here |
| PFOS 12 | Two-agent operations, transport, signals, backup/recovery | Governing server contract; templates/tests are not proof of deployment |
| PFOS 13 | v1.4 controller delta | Explicitly proposed and non-superseding of the reported v1.3 master |
| PFOS 14 v2 | Single Slack conversational window | Still the live-policy baseline despite Telegram in the filename |
| PFOS 14 sections 10-12 | Telegram restoration, daily companion, dual-channel memory | Bounded local preparation/reference authority; no automatic transport cutover |
| PFOS 15 | Daily transaction asking, parsing and candidate staging | Pure parser and candidate model exist; operational capture/review/promotion not delivered end-to-end |
| Build C6 + ADR-0003 | Multi-currency and ledger-integrity evolution | C6 still DRAFT; ADR independently ratifies specific landed changes. Per-currency display decision remains open |
| UPOI | Unified governance, grants, context, objectives, rehearsal | Requirements remain DRAFT; substantial offline modules exist, three substeps still marked in progress |
| Seven-contract recovery | Lineage, runtime, security, finance, UX, testing, continuity audit | Actions checked off; overall program PARTIAL/BLOCKED, not production complete |
| Kiro development programs | Skills, validators, research, browser/property/mutation tooling | Local tooling exercised; fresh-session Kiro activation remains unverified |

### Current `.kiro/specs/` checklist inventory

Counts below are checkbox entries, including parents; **not completion percentages**. A checked verification task can mean the check ran and failed.

| Spec directory | Checked | Unchecked | In progress | Main remaining limit |
|---|---:|---:|---:|---|
| agentic-profile-baseline | 7 | 1 | 0 | Native writer/privacy/recovery reconciliation |
| telegram-window | 4 | 12 | 0 | Unique consumer, actual hooks/grants, safe runtime integration and live acceptance |
| telegram-daily-companion | 5 | 2 | 0 | Full clean-tree gate and native live adapter |
| dual-channel-memory | 3 | 2 | 0 | Full clean-tree gate and real VPS/Drive persistence integration |
| unified-personal-operating-intelligence | 39 | 3 | 3 | Substeps 5.2 signal adapter, 6.1 archive port, 7.4 evidence-integrity property test remain marked in progress |
| seven-contract-recovery | 9 | 0 | 0 | Program exit evidence remains blocked despite completed research actions |
| kiro-capability-expansion | 6 | 2 | 0 | Fresh Kiro activation and separately authorized wider integrations |
| kiro-research-evidence | 4 | 0 | 0 | Research validation is not runtime activation |
| kiro-tool-adoption | 4 | 0 | 0 | Tooling trials delivered; app accessibility findings remain |

Older `.kiro/specs/06-two-agent-vps` and original build-spec directories are absent. Existing source headers still refer to them. The source registry traces intentional deletion and later steering restoration; do not recreate policy from those references alone.

The reported unified v1.3 master/index was not independently recovered in the Sept 11 audit. That receipt records expired Drive access and failed refresh. This report did not retry authentication, so credential failure remains **last observed**, not newly diagnosed.

## 5. Ranked gaps

Priorities are this report's triage assessment, not amendments to existing authority.

| Priority | Gap and impact | Evidence / confidence |
|---|---|---|
| P0 | **Browser Drive path uploads plaintext JSON.** Violates encrypted-data-only policy. Do not enable real-data sync until encryption, key custody, migration/refusal and recovery are designed and tested. | Current source: driveDb.ts:75-78,108-117; driveClient.ts:150-183. Application-level encryption absent in this call chain; HTTPS is not that encryption. |
| P1 | **Device-local candidates can leave the device.** Merge labels candidates local-only but full-db serialization includes them in canonical saves/snapshots. | Current source: sync.ts:192-194 plus driveDb.ts:108. |
| P1 | **Native ingress safety and sole-consumer ownership unresolved.** Hook ordering/failure behavior, startup mutations/update drops and direct tool paths need bounded integration before Telegram restoration. | Sept 15 source-trace receipts and telegram-window tasks; not a new live exploit reproduction. |
| P1 | **Effective tool exposure and service hardening need reconciliation.** Inspected MCP definitions lack nested include/exclude restrictions; gateway selector can default-include MCP tools. Four systemd protections were off. | Sept 15 supervisor/remaining-bridges receipts. Static configuration is not proof of tools actually loaded or invoked. |
| P1 | **Durable raw journal capture is not established.** Sept 11 inspected native live-ingress path wrote turn metadata, not raw captured text. Separate writer modules did not establish live capture integration. | agentic-profile-baseline/verification.md:124-175. Dated native-source evidence, not current provider observation. |
| P1 | **Daily financial intake is incomplete end-to-end.** Parser writes nothing and has no production importer found; schema staging exists, but no dedicated candidate-review/promotion UI was found. | src/server/ingest/dailyCapture.ts:11-19; current non-test source searches; src/features/import and App.tsx. |
| P1 | **PWA/server ledger coherence unproven.** Browser is Dexie/Drive, static host is not an API, server has its own finance store. Do not assume bot and app answer from the same current ledger. | Current store.ts and appServer.ts; inference from their distinct data paths, not a proven deployed divergence. |
| P1 | **FX history can be lost.** UI replaces rate by currency; merge keys by currency; engine expects timestamped historical observations. | Current NetWorthView.tsx:227-229; sync.ts:153; lib/money/fx.ts:123-150. |
| P1 | **Legacy migration can silently replace malformed money with defaults.** Current-schema safe-integer validation does not cover coercion before validation. | Current migrations.ts:31-32,60-62,75-78. Source finding, no new regression written in this research task. |
| P1 | **Live readiness and recovery evidence are incomplete.** No current deployed snapshot parity, full finance round trip or independently observed restore provided by this report. | Fresh local baseline says allCurrent=false for eight capabilities; Sept 11/15 receipts are narrower observations. |
| P2 | **Accessibility defects are recorded.** Budget, Settings, Reports lack H1; Reports has four serious contrast nodes; Settings has an incomplete ARIA finding requiring review. | Same-day docs/kiro/operational-excellence/final-verification.md:49-62. Prior browser trial, not rerun here. |
| P2 | **Reconciled no-op corrections can add unnecessary audit rows when splits are supplied.** | Current state/actions.ts:531-538. Logic trace; no new runtime reproduction. |
| P2 | **Documentation and release evidence lag implementation.** README says no servers; steering cites 333 tests and missing contracts; transport filenames and history conflict without reading amendments. | Current README, steering and contract files. |
| P2 | **Acceptance coverage does not certify the full system.** AC12 checks only the original five-contract ledger; test floor is 3009, below latest recorded 3141; Python and isolated Kiro quality suites are not automatically the Vitest gate. | scripts/verify/{all,contract-ledger,testcount}.mjs; vite.config.ts:48-52; tooling receipt. |
| P2 | **Test runner health check has a blind spot.** testcount.mjs does not reject the child exit status, validate report freshness or explicitly reject pending tests; it checks reported failures and passing-count floor. | Current testcount.mjs:17-38. This is a source-level verifier gap, not evidence this run's report is stale. |
| P2 | **Working tree is not release-clean.** Protected source/spec/tooling changes require owner-reviewed disposition. | Initial 48 collapsed status entries: 10 tracked modifications and 38 untracked entries, before this report. Do not clean or commit to conceal this. |

### Corrections to stale findings

- Multi-currency is **not absent**: Account and Transaction require currency; FX observations carry observedAt/conversionVersion.
- Candidate staging is **not absent**: schema v9, cache and migrations contain transactionCandidates. Full workflow is still missing.
- Base-aware sync repair and versioned split/correction types already exist. Do not blindly replay the Sept 2 gap list.
- PFOS Contracts 05 and 06 **exist**.
- The VPS is not merely hypothetical: Sept 11 and Sept 15 receipts observed services. That is still not whole-system readiness.
- The suspected missing container MCP script **exists**. The final Sept 15 receipt corrected an EACCES false absence and identified a WHOOP interface. Other traced bridges are Camofox browser automation and native knowledge retrieval, not proven PFOS/capture ports.
- UI accessibility is no longer entirely unexamined: the Sept 16 tooling trial found concrete defects.
- The current model policy is not evidence of a GPT-6 migration: inspected source defaults remain MiMo/GLM, with premium Grok/Kimi opt-in. Actual live model configuration was not inspected here.

## 6. Verification for this report

Native Node/npm commands use PowerShell to avoid the tool shell's Node alias.

- `node --version`: v24.14.1.
- `npm --version`: 11.11.0.
- `npm run typecheck`: exit 0.
- `npm run inspect:agentic-baseline`: valid report, allCurrent=false, authorizesExecution=false; eight capabilities classified REPORTED/HISTORICAL with missing current baseline/check evidence. Observed process exit 2, the diagnostic's noncurrent-evidence result; not a code crash.
- `git diff --check`: no diff errors; existing LF/CRLF notices on three steering files.
- `npm run verify:all -- --all`: exit 1; **19 of 21 executed checks passed**. Typecheck, lint, tests, build, bundle isolation and other acceptance checks passed. AC14 (clean working tree) and AC15 (release readiness) failed on 48 existing collapsed status entries. The new report was written after that status snapshot. No failure was suppressed.
- Fresh `.loop/tmp/test-results.json`: success=true; **3141 total, 3141 passed, 0 failed, 0 pending**. Report modification time was checked against this run. This counts the application Vitest suite, not every isolated developer or Python test.
- The report itself was reread and checked for local references, stale draft markers, whitespace and common secret patterns. No new tests were necessary because application behavior was unchanged.

No app source, test, contract, existing spec or deployment record was changed. Local verification may regenerate build/test artifacts. No SSH, provider/auth probe, browser session, credential operation, external write, commit or push was performed by this report task. Independent subagent research was attempted but denied by the tool; no independent-review claim is made.

## 7. Recommended next work, in order

1. **Protect persistence:** design and implement application-encrypted Profile-A storage with off-Drive key custody and explicit candidate exclusion. Preserve offline functionality and prior data.
2. **Establish one actual runtime path:** reconcile the managed gateway, candidate second process, admission/auth, durable acceptance, grant fences and tool allowlists. Do not start another gateway to solve uncertainty.
3. **Deliver one complete user loop:** choose either governed conversation -> supported versioned PFOS read -> honest reply, or capture -> native sole writer -> read-back -> continue. No success acknowledgement before actual persistence.
4. **Finish financial intake/integrity:** review/promotion surface, source-to-ledger reconciliation, historical FX identity, legacy malformed-money refusal and correction no-op tests.
5. **Close evidence and release gaps:** scoped current runtime/readiness and recovery observations, accessibility fixes, acceptance coverage review, canonical source reconciliation and owner-reviewed disposition of existing changes.

These are recommendations, not authorization to operate gates, credentials, deployment or production models.

## 8. Primary reading list

1. `.kiro/steering/{money-rules,drive-db,pfos-current,two-agent-vps,loop-protocol}.md`.
2. `contracts/pfos/_PFOS_CONTRACT_INDEX.md` and the domain contracts listed above.
3. `docs/adr/ADR-0003-post-ynab-architecture.md`.
4. `docs/architecture/seven-contract-recovery/{MASTER_HANDOVER,SOURCE_REGISTRY,VALIDATION,COMPLETION_AUDIT}.md` (Sept 11).
5. `.kiro/specs/agentic-profile-baseline/verification.md` (Sept 11 native capture findings).
6. `.kiro/specs/telegram-window/{requirements,design,tasks}.md`, plus Sept 15 inspection/wiring/supervisor/bridge receipts and the final container-script correction.
7. `.kiro/specs/telegram-daily-companion/{requirements,design,tasks}.md`.
8. `.kiro/specs/dual-channel-memory/{requirements,design,tasks}.md`.
9. `.kiro/specs/unified-personal-operating-intelligence/{requirements,design,tasks}.md`.
10. `docs/kiro/operational-excellence/final-verification.md` (Sept 16 browser accessibility findings).

No secret, real ledger content or deployment particular is needed to use this report.
