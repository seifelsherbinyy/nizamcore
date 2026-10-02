# Canonical source and supersession registry

Owner: `contracts/programs/SEVEN_CONTRACT_RECOVERY.md`. Phase: Recovery 1.
Inspection date: 2026-09-11. This is an evidence registry, not new product authority.

## Evidence classes

FACT means inspected bytes, code or observed command output. INFERENCE means a reasoned
connection. MISSING means required evidence was unavailable in this bounded inspection.
A historical document's assertion is a FACT about that document, not proof of current runtime.

| Source | Evidence and lineage | Authority / disposition |
|---|---|---|
| `.kiro/steering/money-rules.md`, `drive-db.md` | FACT: integer milliunits, exact allocation, `drive.file`, offline cache/merge | Unconditional invariants; encrypted-data-only further required by PFOS steering |
| `.kiro/steering/pfos-current.md:1-45` | FACT: older Profile-A completion, PFOS engines, 21-check gate, encrypted data only | Governs PFOS; old server wall superseded in server scope only |
| `.kiro/steering/two-agent-vps.md:1-6,45-121` | FACT: Node 24 finance, independent stores, injected ports, read-only carve-out | Server/agent precedence over PFOS steering; no override of money or Drive rules |
| `contracts/CONTRACT_1..5`, `_CONTRACT_INDEX.md` | FACT: original build lineage is retained | Original app contracts, not seven program workstreams |
| `contracts/CONTRACT_4_ui_ynab.md:1-42` | FACT: exact allegedly missing filename recovered locally; UI phases 4.1-4.7 | Original UI contract; linked `.kiro/specs/04-ui-ynab/` is unavailable in current tree |
| `contracts/pfos/_PFOS_CONTRACT_INDEX.md:3-30,80-86` | FACT: four blueprint copies and original ingestion provenance | Authoritative product direction; not sufficient to prove current remote canonical hierarchy |
| `contracts/pfos/01_PFOS_Product_Constitution_and_Problem_Solution_Logic.md` | FACT: local SHA-256 matches `_INGESTION_MANIFEST.json`; prefix `2763df52cce0648b` | Product constitution; preserve bytes |
| `contracts/pfos/02_PFOS_Data_Architecture_Integrations_and_Security.md` | FACT: local SHA-256 matches manifest; prefix `47e381d37f1850d1` | Data/security; finance runtime language overridden by server steering |
| `contracts/pfos/03_PFOS_Financial_Intelligence_Decision_Forecasting_and_Learning.md` | FACT: local SHA-256 matches manifest; prefix `098ac967ba387038` | Deterministic financial product direction |
| `contracts/pfos/04_PFOS_UX_UI_User_Journeys_Research_and_Delivery_Roadmap.md` | FACT: local SHA-256 matches manifest; prefix `f86c614174450619` | PFOS experience direction; distinct from original build Contract 4 |
| `contracts/pfos/05_PFOS_Agent_Orchestration_Skill_and_Knowledge_Integration.md:1-14` | FACT: NIZAM-derived 2026-08-18 contract exists | Corrects stale index/steering statements that 05 was never authored |
| `contracts/pfos/06_PFOS_Database_and_Knowledge_Model.md:228-257` | FACT: safe-integer persistence and one money implementation | Server storage authority; does not make browser JSON and server SQLite one runtime store |
| `contracts/pfos/09..11` | FACT: benchmark/routing/governance contracts listed at index lines 89-108 | LLM-tier authority, not monetary truth |
| `contracts/pfos/12_PFOS_Two_Agent_VPS_Deployment_and_Operations.md` | FACT: derived deployment/isolation/backup contract | Governing server operations, subject to human-only restrictions |
| `contracts/pfos/13_NIZAM_v1.4_Production_Controller_Delta.md:3-8,95-98` | FACT: cites Drive-safe v1.3; explicitly proposed and non-superseding | Corroborates reported v1.3 lineage, does not prove exact master bytes or adoption |
| `contracts/pfos/14_NIZAM_Single_Window_Telegram_Ingress.md:1-16` | FACT: title/content now Slack; 2026-08-31 ingress amendment | Replaces live Telegram identity drawing only, preserves profiles/stores/caps |
| `contracts/pfos/15_NIZAM_Daily_Transaction_Capture_and_Candidate_Staging.md:1-35,66-76` | FACT: 2026-09-02 staging contract, explicit owner promotion | Daily capture authority; no automatic canonical ledger write |
| `docs/research/2026-09-02-ynab-live-product-teardown.md` | FACT: recovered local teardown under original UI contract | Research evidence, not automatic authority to replace current behavior |
| `docs/architecture/CURRENT_FINANCIAL_ARCHITECTURE_GAP_ANALYSIS.md` | FACT: older gap report | Historical; multiple absence claims contradicted by current schema/sync code |
| `contracts/CONTRACT_6_multicurrency_ledger_integrity.md:7,28-42` | FACT: DRAFT banner remains; some described capabilities now implemented | DRAFT is not implementation authority; ADR-0003 separately ratifies D1-A through D4-A for landed work |
| `.kiro/specs/unified-personal-operating-intelligence/requirements.md:5` | FACT: DRAFT, documentation-only authorization boundary | Design evidence; does not authorize host/credential/production operations |
| `.kiro/specs/agentic-profile-baseline/`, `src/server/hermes/baselineEvidence.ts` | FACT: pre-existing untracked evidence assessment work | Protected in-flight work; neither changed nor adopted as completed baseline |
| `Module BINA_BUILD.txt` | FACT: supplied discovery inventory with FACT/INFERENCE/MISSING labels | Discovery map, not independent verification of source contents |

## Reported upstream lineage, still MISSING independent retrieval

The attachment reports: early MAL ladder/workflows -> MAL Financial Operating System
Blueprint (2026-07-21) -> PFA -> July offline-first/YNAB and Telegram research -> PFOS
constitution/data/intelligence/UX -> unified v1.3 FINAL -> transaction forensics and August
snapshot/strategy -> Hermes integration -> later continuous monitoring.

The following remain named discovery targets, not verified current authority:
- `INDEX — 05_FINANCE` and `PFOS_Personal_CFO` remote index/folder.
- `NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE`.
- Reported superseded PRE_NR_INDEX, STAGING, v1.2 TURN2, v1.1 TURN1 versions.
- MAL Financial OS blueprint, ladder, baseline/scenario/decision workflows and PFA README.
- Original July YNAB/offline-first research, Hermes/NIZAM architecture documents.
- Current financial snapshot, strategy decision log, investigation handover and forensics layout.

No private transaction content was necessary or retrieved. `mcp list` reported no configured
MCP servers for this profile. The configured ingestion grant declares exactly `drive.file`:
its cached access token returned HTTP 401 and was expired; renewal through its existing refresh
grant returned HTTP 400. No consent or broader scope was requested. Consequently remote absence,
canonical status and chronological supersession cannot be established from this session.

## Adjudication

1. Preserve local source bytes and implemented capabilities. Do not rebuild from the attachment.
2. Exact original UI contract is FOUND, not missing.
3. Four blueprints are byte-consistent with local ingestion evidence, not freshly compared to Drive.
4. v1.4 proposal is not a master-contract supersession; Slack amendment is narrower and explicit.
5. Old referenced spec directories were intentionally removed under ADR-0003 D6-B (line 217).
   Commit `7a43d2f` subsequently restored nine steering files, not the old specs. The ADR
   statement that steering remains deleted is stale. The recovery spec neither restores nor
   marks those old specs complete.
6. Refreshing a historical gap report is safer than implementing its already-fixed findings again.

Independent lineage review was reconciled against ADR-0003 lines 214-217 and commits
`b448953` then `7a43d2f`. Per-currency formatting remains an explicitly open decision;
DRAFT C6 does not invalidate independently ratified implementation decisions. The reviewer
repeated an old absent-05 claim; rejected here because full PFOS Contract 05 exists on disk.
