# Financial NIZAM Architecture Master Handover

Owner: `contracts/programs/SEVEN_CONTRACT_RECOVERY.md`. Phase: Recovery 1.
Inspected 2026-09-11. Status: PARTIAL; not a production-readiness declaration.
Companions: `SOURCE_REGISTRY.md`, `VALIDATION.md`, and the recovery spec under `.kiro/specs/`.

## 1. Executive finding

NIZAM is an implemented offline-first React finance app with deterministic PFOS engines,
a substantial Node/SQLite server tier, Python boundary/rehearsal adapters and Hermes integration.
It is not an empty architecture to rebuild. The repository's original UI contract is present.
The four local PFOS blueprints match their recorded ingestion hashes. The reported unified
v1.3 FINAL cannot yet be independently recovered from Drive.

A bounded code repair now rejects unsafe integer milliunits at the shared JSON schema boundary.
Eleven new synthetic tests distinguish valid endpoints from overflow and protect migration/load.
No financial ledger, credential, production service, deployment setting or other repository changed.

## 2. Seven-contract execution ledger

| Workstream | Status | Evidence produced | Unmet exit evidence |
|---|---|---|---|
| C1_SOURCE_TRUTH_AND_LINEAGE | PARTIAL | Source registry, four blueprint hashes, exact UI contract, narrow supersession map | Remote master/index and older MAL/PFA corpus unavailable |
| C2_LOCAL_RUNTIME_AND_INFRASTRUCTURE | PARTIAL | Local tree/storage map; authenticated SSH; active ingress and seven running containers observed | Container roles/health, deployed revision parity, DB schema and complete scheduler inventory not established |
| C3_DATA_SECURITY_AND_AUTH | BLOCKED | Trust map, value-blind readiness, deterministic boundary repair | Browser plaintext Drive path violates encryption invariant; no live enablement until resolved |
| C4_FINANCIAL_INTELLIGENCE_AND_AGENTIC_CORE | PARTIAL | Existing engine and tool ownership mapped | Full MAL-to-PFOS policy parity requires unavailable canonical evidence; no invented policy |
| C5_PRODUCT_UX_AND_YNAB_EVOLUTION | PARTIAL | UI contract recovered; all 12 routes mapped to real views | No interactive responsive/accessibility audit; no verified target-policy delta |
| C6_IMPLEMENTATION_INTEGRATION_AND_TESTING | PARTIAL | Safe-integer repair, 70 focused tests, 3009 full-suite tests passed | Full repository acceptance 19/21; release checks blocked by dirty tree; live integrations not certified |
| C7_PRODUCTIONIZATION_CONTINUITY_AND_LEARNING | PARTIAL | Handover, validation, recovery map and ranked next loop | No live restore exercise, deployment or end-to-end production certification |

## 3. Verified local architecture and dependency graph

```text
Profile A: browser / owner device
  legacy CSV import -> parse/dedup preview -> explicit import commit -> transactions
  daily-capture/staging path -> separate transactionCandidates -> owner promotion
      -> canonical transactions / obligations / policy
      -> shared integer money core -> budget / liquidity / forecast / decisions / net worth
      -> React views (derived numbers, not model-sourced figures)
  Zustand working state <-> Dexie offline cache + stored sync point
      -> base-aware merge -> browser Drive adapter [PLAINTEXT EGRESS GAP]

Server tier (implemented locally; deployed revision parity unknown)
  evidence -> src/server/ingest -> normalized facts / provenance
      -> finance.db repositories + ordered checksum migrations
      -> existing deterministic PFOS domain -> typed Hermes finance tools
  model/routing/spend telemetry -> explanation/governance, never financial source
  separate life.db / finance.db / signals.db
      <-> consent-controlled bounded signal bus, not shared raw financial data
  backup design -> consistent SQLite snapshot -> encryption -> archive receipt
      -> off-host restore into fresh target -> integrity + FK checks -> throwaway probe

Current ingress authority
  owner Slack window -> Hermes gateway -> deterministic ingress router
      -> isolated life tools OR PFOS tools -> governed result/explanation
```

Evidence anchors:
- `src/App.tsx:6-22,74-86,94-103`: views and local-first boot.
- `src/state/store.ts:8-9,53-80`: cache/push orchestration and true nullable merge base.
- `src/lib/db/schema.ts:57-60,435-479`: schema v9, shared money validator, separate candidates.
- `src/lib/drive/sync.ts:141-195`: entity merges and local candidate preservation.
- `src/server/db/migrations.ts:9-24,57-75`: atomic checksum-protected eight-step migration series.
- `src/server/process/start.ts:16-20`, `main.ts:12-35`: Node process and readiness shell, legacy transport modes.
- `src/server/pfos_port.py:1-8,33-66`: validation/serialization boundary, not a second finance engine.
- `src/server/hermes/toolBoundary.ts:12-45,65-85`: tool allowlists and deterministic fact ports.
- `src/server/signals/`: consent, envelope schema/validation, isolated store and negative tests.

Repository map: `src/features/` contains 15 feature directories; `src/server/` contains
storage, ingestion, ports, process, model, routing, signals, operations and Hermes modules.
`ops/` contains templates/runbooks, not proof that those exact artifacts are live.
Native local toolchain observed: Node v24.14.1, npm 11.11.0. Branch master; initial HEAD
`5652edf`. No branch switch, commit, push, reset, cleanup or user-file overwrite occurred.

## 4. Finance capabilities and user decisions

| Surface / user decision | Existing implementation | Evidence level |
|---|---|---|
| Home: what can I safely spend? | `safeToSpend/CommandCenter.tsx`, `safeToSpend.ts:1-31` | Pure eight-term waterfall over NizamDb, injected as-of date |
| Budget: what is assigned/available? | `budget/BudgetView.tsx`, `budget.logic.ts` | Implemented; included in full test suite |
| Accounts: what posted/pending? | `transactions/Register.tsx`, account sidebar | Real route and ledger state, not a mock dashboard |
| Reconcile: does cleared state match? | `reconciliation/Reconcile.tsx`, state actions | Implemented; no owner financial data inspected |
| Import: which evidence should become ledger truth? | `import/ImportWizard.tsx`, schema candidates | Legacy CSV preview/commit exists; separate staging model exists, but a dedicated candidate-review UI was not found |
| Obligations: what must be protected? | `obligations/ObligationsView.tsx`, `obligations.logic.ts` | Existing priority/reserve engine |
| Decide: can this purchase proceed? | `decisions/DecideView.tsx`, `decision.logic.ts:1-11` | Simulates an outflow through existing deterministic engines |
| Forecast: what changes over time/scenarios? | `forecast/ForecastView.tsx`, `forecast.ts:1-26` | Baseline/downside/upside; uncertainty toggles, no invented magnitudes |
| Decisions: what happened versus expected? | `decisions/DecisionsView.tsx`, `decisionRegistry.ts` | Append-only outcome-learning records, not autonomous policy rewriting |
| Net worth: assets/FX/liquidation/real view? | `netWorth/NetWorthView.tsx`, `netWorth.ts` | Existing rational-money computation |
| Reports / Settings | `reports/Reports.tsx`, `settings/SettingsView.tsx` | Wired routes; not interactively audited this session |

Target architecture: preserve these working capabilities; reconcile master lineage before new
policy; repair encrypted archive boundaries; expose deterministic results through typed ports;
retain isolated state/caps and explicit owner approval. Do not create competing MAL/PFOS ledgers,
a second arithmetic implementation, a new cloud database or a new transport from old research.

## 5. Live runtime observations, narrowly stated

Read-only SSH succeeded using the account/key references in protected operator metadata.
A separate protected environment file named a different account; that pairing was rejected.
No password fallback, host-key bypass or credential edit was used.

Initial `systemctl is-active` probes of anticipated unit names returned inactive. Discovery via
`systemctl list-units --all --type=service --output=json --no-pager` then found one project ingress
service loaded/active/running in system scope; no project user services were returned.
`docker ps --format '{{.State}}'` reported seven running containers. Node is in the operator PATH;
its version was not established as 24. System/user project-name-filtered timer counts were zero.
These observations do NOT establish container health, every scheduler, finance readiness,
allowlist correctness, model eligibility, backup freshness or deployed code parity.

All raw unit names, hosts, accounts, keys, container identifiers, environment values and private
payloads were withheld. No process was restarted and no host file was written.

## 6. Credential and integration readiness

| Integration / credential class | Status | Observation / minimum next action |
|---|---|---|
| VPS SSH configured identity | PRESENT | Authentication observed using documented account/key paths; separate env account drifts |
| Drive cached access token | EXPIRED | Configured exact `drive.file`; HTTP 401; no broader scope requested |
| Existing Drive refresh grant | INVALID | Renewal attempt HTTP 400, no raw provider body emitted; owner must restore existing grant securely |
| Google desktop client | PRESENT | Configuration consumable; this does not prove client/grant pairing is valid |
| OpenRouter runtime keys/caps | UNVERIFIED | Alias registry and isolated runtime design present; no model call or spend performed |
| Slack bot/app tokens + allowlist | UNVERIFIED | Ingress process active is not proof of token validity, allowlist or round-trip delivery |
| Backup encryption identity/Drive archive grant | UNVERIFIED | Templates inspected; no secret transfer, restore drill or archive upload attempted |
| Revoked Telegram aliases | UNVERIFIED at provider | Contract 14 says retired; not probed or re-enabled |
| MCP Drive connection | INACCESSIBLE | No MCP servers configured for this profile |

Credential presence is not authentication, and authentication is not end-to-end readiness.

## 7. Security contradictions and remaining risks

| Priority | Finding | Evidence / disposition |
|---|---|---|
| P0 | Browser adapter sends plaintext database JSON to Drive | `driveDb.ts:75-78,108-117` -> `driveClient.ts:150-182`; conflicts with PFOS steering encrypted-data-only. No live write performed. Requires encryption/key custody/migration design before enablement |
| P1 | Exact unified master/index inaccessible | Attachment and Contract 13 corroborate lineage only. Restore scoped grant or provide architecture-only exports with provenance |
| P1 | Release gate cannot pass dirty tree | Protected pre-existing work plus this repair; no commit authorized; keep AC14/AC15 failures visible |
| P1 | Current runtime parity and recovery unknown | Active ingress/seven containers do not prove finance/schema/backups; bounded follow-up needed |
| P1 | Device-local candidates may be serialized by full-database Drive save | `sync.ts:192-194` says local-only, while `driveDb.ts:108` serializes whole db. Treat as egress design gap alongside encryption |
| P1 | FX history can be overwritten/collapsed | `NetWorthView.tsx:227-229` replaces by currency; `sync.ts:153` keys only by currency; `fx.ts:123-150` expects historical observations. Coupled writer/merge repair requires an explicit observation identity/conflict design |
| P2 | No-op reconciled corrections can append audit rows | `state/actions.ts:531-538` compares splits to null and bypasses refusal whenever splits are supplied. Reviewer logic trace confirmed; no production mutation or new regression executed here |
| P2 | Historical contract/spec status is inconsistent | Original specs intentionally removed (D6-B); steering later restored; DRAFT C6 work separately authorized in ADR-0003; stale absent-05 prose remains |
| P1 | Legacy migration can default malformed money before validation | `migrations.ts:31-32,60-62,75-78` confirms coercion in specific legacy paths. Current-schema refusal is covered; legacy evidence-preserving rejection needs separate regressions and compatibility review |
| P2 | Safe-money repair covers validation/load, not every typed write boundary | `localCache.ts`/`driveDb.ts` typed write APIs require separate untrusted-write audit; do not claim universal input protection |
| P2 | Backup operational constraints remain unproven | `ops/backup/backup.sh:59-77` WAL read-only sidecar issue; restore template integrity checks not live-drilled |
| P2 | Schema/engine capabilities ahead of UI | Approval control, allocation history and dedicated candidate-review surface not found by lineage reviewer; per-currency formatting explicitly open in ADR-0003:216 |
| P3 | Responsive/accessibility and product acceptance unobserved | No UI redesign or interactive audit performed |

## 8. Decisions, rollback and next autonomous loop

- Preserve all existing modules; repair the smallest proven defect under existing authority.
- Preserve upstream blueprint bytes; keep program IDs separate from product contract numbering.
- Use read-only runtime discovery before interpreting inactive anticipated service names.
- Do not deploy while canonical recovery and plaintext egress risks remain unresolved.
- Rollback for this local repair is a reviewed inverse of only its schema/test/floor diff if the owner
  chooses it. No schema migration or data rewrite exists to undo. Do not reset the working tree.
- Existing recovery design uses encrypted snapshots and off-host fresh-target restoration:
  `ops/restore/restore.sh:19-56`. It was inspected as text, never executed.

Next loop, after the concrete blockers are resolved:
1. Owner restores the existing narrow Drive grant or supplies the master/index as architecture-only exports.
2. Compare exact master/source hashes and supersession markers; close lineage contradictions explicitly.
3. Design encrypted Profile-A persistence, key custody and plaintext migration/refusal, including local-only
   candidate exclusion; obtain review before behavior-changing implementation.
4. Inspect deployed revision/container roles/readiness and scheduler coverage using value-blind reads.
5. Implement approved offline encryption/migration tests, then a separately authorized deployment/restore plan.
6. Resolve working-tree ownership with the owner; commit only if explicitly authorized, then rerun the full gate.

Independent finance review also flags the documented lenient import provenance fallback
(`ledgerImport.ts:352-357`): unknown extraction methods become manual, unlike the strict path.
Treat as a policy-compatibility issue, not a reason to silently change existing import behavior.

Independent repair review returned without a blocking defect and reported 3009 tests passing.
The 3009 floor depends on protected untracked tests remaining included; resolve their release
disposition with the owner, not by silently committing them or reducing acceptance. See VALIDATION.md.
