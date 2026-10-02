# Agentic Profile baseline verification receipt

Contract 05 addendum, Phase 0. Session date: 2026-09-11.
Scope: local evidence-reporting foundation only, not full first-increment delivery.

## Commands and observed results

Node/npm commands ran through `powershell.exe -NoProfile -Command` to use the
installed Node runtime, not the tool shell's Bun alias.

| Command | Observed result |
|---|---|
| `node --version` | v24.14.1 |
| `npm run typecheck` | Initial test edit failed with five syntax diagnostics caused by one extra closing parenthesis. Corrected; rerun passed. |
| `npm test -- --run src/server/hermes/baselineEvidence.test.ts` | 69 passed, one file, zero failures. |
| `npm run lint` | Passed with zero warnings allowed. |
| `npm run build` | Passed TypeScript and Vite production build; 100 modules transformed; PWA artifacts generated. |
| `npm run inspect:agentic-baseline` | Valid metadata report, allCurrent false, authorizesExecution false, eight capabilities. Exact npm exit 2 confirmed using `$LASTEXITCODE`. The initial PowerShell wrapper surfaced nonzero as 1; the explicit native exit check confirmed 2. |
| `npm run verify:all -- --all` | 19/21 checks passed. AC14 and AC15 failed because the working tree is not clean. |
| `git diff --check` | No findings. |
| `git status --short` | Intended increment changes plus the pre-existing untracked research directory; no cleanup performed. |

The full-suite machine report at `.loop/tmp/test-results.json` records success:
2,998 total, 2,998 passed, zero failed, zero pending. It includes all 69 baseline
assertions. The report is a local test artifact, not a VPS attestation.

AC14 reports uncommitted changes; AC15 reports the same dirty-tree condition.
The release acknowledgement itself was accepted. No acceptance check, floor,
release record or protected user file was modified to get a pass. This receipt
does not claim a green repository handoff, commit readiness or push readiness.

## Coverage and review

- AB01: closed objects, versions, capability/check enums, unique receipt IDs,
  date/calendar validity, null observation metadata, bounded refs/counts and
  generic input errors.
- AB02: independent literal requirements for all eight capabilities; removing
  either required check blocks current status.
- AB03/AB04: source basis, exact environment/snapshot, inclusive 24-hour expiry,
  injected clocks, null baselines, missing evidence, unknown/failed outcomes,
  contradictory fresh pass/fail receipts, deterministic immutable output.
- AB05/AB06: real Node subprocesses test default repository data from another
  working directory, synthetic all-current data, malformed JSON, schema errors,
  nonexistent files, extra arguments and exit 0/1/2. Package wiring is asserted.
- Coverage is requirement-based, not an instrumented line/branch percentage.
  No coverage provider is installed in the project lockfile; no dependency was added.
- Manual review: one validation/assessment module plus a thin filesystem CLI;
  fixed requirements are duplicated only in independent tests; no new runtime
  hook, money calculation, provider call, production authorization or dependency.
- Bundle-isolation acceptance passed. An additional search for baseline module/
  error symbols under `dist` returned no matches.
- An explicit supplemental scan covered all nine increment files, including
  untracked additions, for the repository's five secret patterns and trailing
  whitespace: zero findings. Tracked-only scans alone do not cover new files.
- Independent teammate review was unavailable: the tool denied the agent-spawn
  capability. No independent-review claim is made.

## Remaining boundary

Current evidence is REPORTED for ingress, journal and recovery; HISTORICAL for
retrieval, capacity, scheduler, calendar and finance. All target hashes stay null.
This says reconciliation is incomplete, not that the live capabilities are absent.

At the initial local verification checkpoint, no VPS connection, host mutation,
credential changes, human-gate operation, cross-repository write, commit or push
was performed. The later read-only inspection is recorded below. The stale local core checkout and existing
research directory remain untouched. Native capture wiring still requires completed contract reconciliation and a
separately bounded implementation step. The full first increment remains blocked.


## Read-only access follow-up, same session

The owner identified access details in this workspace and directed continuation.
The ignored operator metadata and key reference exist; neither access record is
tracked. No credential value was printed or copied into this receipt.

- The first background probe stalled in the local tool shell and was cancelled.
- A reviewed temporary Python probe invoked SSH with BatchMode, IdentitiesOnly,
  StrictHostKeyChecking, no agent forwarding, and bounded connection/process
  timeouts. It consumed existing metadata/key references, not inline secrets.
- The account in the access environment file was rejected (SSH exit 255,
  authentication). The account documented in VPS JSON metadata succeeded with
  the same key and existing known-host trust. No credential was changed.
- Native Git HEAD observed: `711b7cd111753d53ddf9c610ab021def646650d1`.
  There are 421 tracked paths and seven dirty status entries: two modified and
  five untracked. No dirty file was overwritten, reverted or removed.
- Conventional root `contracts/` and `.kiro/` authority directories were absent.
  Native authority documents instead exist under `NIZAM__system/docs/`.
- Read selected continuity, YAWMIYAT persistence and TAFRIGH capture/triage docs;
  inspected AST-level interfaces in journal persistence, kill-switch, recovery
  packaging and retrieval MCP modules. No application module was imported or run.
- Existing code includes adaptive governor, scheduler, retrieval, journal writer
  and capture skill paths. File presence is not proof of runtime wiring or health.

Reconciliation findings, not production diagnoses:

1. Native YAWMIYAT documentation names `tools/yawmiyat.py` as the core writer;
   `governor/journal_persistence.py` also exposes a persistence writer. Determine
   the ingress-selected path and idempotency/session protocol before integration.
2. TAFRIGH capture separates verbatim capture from opt-in triage. Preserve that
   distinction and reconcile it with the canonical YAWMIYAT session protocol.
3. Recovery code exposes secret-bundle packaging. That existence does not prove
   a Drive upload occurred. This repository's prohibition on keys/secrets on
   Drive remains governing; no packaging or mirror procedure was executed.
4. Native journal documentation permits selected Drive mirrors and describes
   read-back verification, but the inspected document alone does not establish
   encryption or the actual OAuth scope. Do not treat it as current compliance.

The access blocker is resolved; native integration/reconciliation is not. No
remote tests, writers, providers, service changes, installs, credential changes,
human gates, commits or pushes were executed. No private journal/ledger content
was read. A Git commit alone is not a complete snapshot of code/configuration/
policy including dirty files, so the evidence manifest remains unpromoted with
null target hashes. Earlier local test results remain local results only.

## Dual journal-writer call-site check, same session (2026-09-11)

Follow-up to the reconciliation item above (finding 1). Four additional bounded
read-only SSH probes, same reviewed-script pattern (BatchMode, IdentitiesOnly,
StrictHostKeyChecking, no agent forwarding, bounded timeouts, redacted output).
Only source files, grep hits and commit metadata were read; no private journal
or ledger content, no application module was imported or run.

Findings:

1. `NIZAM__system/governor/journal_persistence.py` (native commit `d71a0b6`,
   2026-09-02) exposes `persist_journal_entry`, `atomic_write_text`,
   `read_back_verify`, `recover_staged_records`. Its only importer anywhere in
   the tree is its own dedicated test file. No production caller was found.
   This module is orphaned as of native HEAD.
2. `tools/yawmiyat.py` (native commit `711b7cd`, 2026-09-04 -- matches native
   HEAD) is imported by `tools/backfill_migrate.py`, `tools/journal_enrich.py`,
   `tools/yawmiyat_derived.py`, `tools/yawmiyat_index.py`, `tools/g3_proof.py`,
   `tools/g5_proof.py`, and a top-level test file (distinct from the governor
   test above, similarly named). It is wired to a scheduled path:
   `tools/journal_daily.sh` (cron) -> `tools/journal_enrich.py` ->
   `import yawmiyat as Y`. This is a retrospective enrichment/backfill
   pipeline, not a live-ingress write path.
3. `NIZAM__system/relay/hermes_adapter.py` imports neither writer. Its only
   journal-related logic is a read-side privacy exclusion (journal/health
   domains are dropped from cloud-eligible grounding context before an
   external Hermes process is invoked via subprocess, gated on
   `NIZAM_HERMES_LIVE`). `NIZAM__system/relay/webhook.py` and
   `NIZAM__system/relay/poller.py` reference neither writer; both simply call
   `coordinator.handle_update(...)` and forward its return value.
4. The actual live-ingress write path is a third module, not previously
   named in the finding-1 reconciliation item:
   `NIZAM__system/governor/ledger_writer.py`, called from
   `NIZAM__system/relay/coordinator.py` ("Phase-1 boot loop", step B4.7,
   "ledger append (Ammar)") on every Telegram/Hermes turn. It appends one
   `EVENT_LEDGER` row keyed by `tg-update:<update_id>` (or `turn:<trace_id>`
   as an unreachable-in-production fallback), with retry-safe idempotency
   noted in-code ("crash retries the turn, the writer returns the row that
   already exists"). The persisted payload is turn *metadata* only --
   trace_id, user_id, kind, target, confidence, sukoon_mode, classification,
   input_chars, artifact_a_present/artifact_b_present booleans, hermes_status,
   a fixed note. It does **not** include the raw captured text.
5. The raw text (`artifact_a["capture"]`, `artifact_b[...]`) is constructed
   in-memory by `coordinator._agent_stub` / `_agent_response` and returned
   from `handle_update`, but neither `webhook.py` nor `poller.py` writes it
   anywhere afterward -- confirmed by direct inspection, no `artifact_a`,
   `artifact_b`, `TAFRIGH` or `brain_dumper` reference exists in either file.
   `coordinator._pretend_capture_path` maps target codenames to file paths
   under `TAFRIGH__brain_dumper/raw/*.md`, but the function name and its sole
   use (feeding `classify()` / `is_egress_blocked()` for a privacy check, not
   an actual write) confirm this is a stub, not a wired write.

Conclusion: as observed at native HEAD `711b7cd`, a live Telegram/Hermes turn
persists only ledger metadata (via `ledger_writer.append`, actor "Ammar").
The raw captured text is not currently written to any durable store by this
path. `journal_persistence.py` is orphaned. `yawmiyat.py` is real but serves a
separate, scheduled, retrospective pipeline unconnected to live ingress. This
narrows finding 1 from "two candidate writers, ingress-selected path unknown"
to "three writers exist; the live-ingress path writes metadata only and does
not durably persist raw capture text at this phase." This is evidence from
code inspection, not a production diagnosis, and does not authorize any change
to native files or services. No remote tests, writers, providers, service
changes, installs, credential changes, human gates, commits or pushes were
executed during this check.
