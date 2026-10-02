# ADR-ZAYD-001: Fold PFOS's financial engine into MAL/Zayd, retire MAL's independent estimation routine

**Status:** Proposed — staged in a local clone, not committed or pushed. Awaiting owner review.
**Date:** 2026-10-02
**Owning repo (after the pending merge):** nizamcore
**Related:** `docs/adr/ADR-0006-repository-merge-into-nizamcore.md` (nizamfinancialapp side, repository-merge decision), `money-rules.md`, `drive-db.md`, `NIZAM__system/docs/CALENDAR_ACTUATION_CONTRACT.md` (same pattern: an amendment reconciling a derived artifact to its governing rule, not a relaxation of an invariant)

## Context

`nizamcore` already has a folder, `MAL__financial_engine/`, that tracks the owner's real personal
finances: debts (HSBC credit cards, Halan/Valu/TRU/Souhoola BNPL, family loans), income, and a
milestone ladder. It is driven by Claude skills (`/mal-baseline`, `/mal-scenario`, `/mal-decision-score`,
etc.) and stores state as `strict_local` (gitignored) markdown and JSONL files.

`nizamfinancialapp` (PFOS) is a separate software product: a deterministic finance engine (integer
milliunits per `money-rules.md`), a Dexie offline cache, and a canonical server-tier store (`finance.db`)
with a Google Drive evidence/recovery mirror under `drive.file` scope, per `drive-db.md`.

The owner directed, on review of a repository-merge plan, that nizamfinancialapp be merged into
`nizamcore` as the primary repository (ADR-0006), and separately directed that PFOS's engine be folded
into MAL rather than kept as a parallel, unconnected folder.

Three concrete conflicts surfaced on inspection and are each resolved below.

## Decision

### D1 — Money representation: MAL's schemas move from float EGP to integer milliunits

MAL's `pfa_*` schemas (`NIZAM__system/schemas/pfa_canonical_state.schema.json`,
`pfa_debt_event.schema.json`, `pfa_payment_event.schema.json`) stored every amount as a JSON
`number` field named `*_egp`. This violates `money-rules.md` Rule 1 ("Money is an integer number of
milliunits... NO floating-point money anywhere"), which PFOS's engine already enforces with
round-trip/no-drift unit tests on every money function.

**Resolution:** all three schemas are bumped to `schema_version: "2.0.0"`. Every `*_egp` field is
renamed to `*_milliunits` and typed `integer`. Non-money ratios (`egp_per_usd`, `debt_to_income_ratio`,
interest rate percentages) are left as plain numbers — they are not currency amounts.

**Data migration:** none was needed. The 2026-10-02 review checked both the GitHub `main` clone and the
local `nizamcore-writable` checkout on the owner's machine for real `canonical_state.json` or
`ledgers/*.jsonl` files; neither exists anywhere found. Only the README/schema templates were ever
committed (by design — the data files are `strict_local`). This is therefore a clean schema cutover,
not a float→integer data transform. If a v1 data file surfaces later (e.g. recovered from a chat
transcript or another device), convert at the point of entry into PFOS using `round(egp * 1000)`, never
downstream, per the migration note embedded in `pfa_canonical_state.schema.json`.

### D2 — Canonical store: PFOS's `finance.db` remains the only one

`drive-db.md` already resolved a three-way canonical-store conflict once (D-S(a), 2026-09-20) and states
the invariant plainly: "Exactly one authoritative writer per canonical domain." MAL's `pfa/README.md`
called its own `canonical_state.json` "single source of truth" — a second, undeclared canonical store
for the same real-world facts (the same debts, the same income) that PFOS already owns.

**Resolution:** `canonical_state.json` is redefined as a **generated projection** of PFOS's `finance.db`,
using the same `mirrorOf`-style stamp Drive already carries (`source_of_truth { engine, storeRef,
schemaVersion, projectedAt, sourceAuditVersion }`, now a required field in the v2 schema). MAL/Zayd's
ledgers (`debts.jsonl`, `payments.jsonl`) are append-only mirrors of PFOS events, not independently
maintained records. `decisions.jsonl` and `learnings_log.jsonl` are unaffected — they hold narrative,
not money, and were never a second source of monetary truth.

### D3 — MAL's update routine stops estimating

MAL's `pfa/README.md` v1 update routine: search chat transcripts, scan workspace files, ask the user for
anything MISSING/STALE, reconcile conflicting figures "most-recent-wins," and tag every figure CONFIRMED
/ ESTIMATED / ASSUMPTION / STALE / MISSING. This is an LLM session deciding a monetary figure, which
conflicts with the repository-wide rule (`AGENTS.md`): "Deterministic engines are the financial source
of truth. LLM... code never computes or sources monetary values."

**Resolution:** the four-layer fetch cascade and the confidence-label system are retired. The v2 routine
is a single step: sync from PFOS. If PFOS doesn't have a figure, the field stays `null` and is logged in
`provenance.open_items`, pending entry into PFOS through PFOS's own ingestion path — never through a
PFA-side guess. The `confidence` field is removed from `pfa_debt_event`/`pfa_payment_event` v2 for the
same reason (`source` is now pinned to the `const` `"PFOS_engine"`). `pfa_learning.schema.json` is
unchanged — recording "I noticed X about my spending" is not an estimate of a money figure, it's a
narrative observation, which remains squarely MAL/Zayd's job.

### D4 — Codename collision fixed as part of this change

`MAL.json`'s self-declared `codename: "Sadiq"` was never entered in `NIZAM__system/agent_personas.json`
(the authoritative codename registry), and collided with `QARAR`'s codename of the same name, which *was*
registered there with an explicit `"Codename reserved."` note. This violates the registry's own stated
invariant: `"codename_uniqueness": "no two agents share a codename"`.

**Resolution:** MAL's codename becomes **Zayd**, after Zayd ibn Thabit, the companion entrusted by Abu
Bakr and Umar with managing the Bayt al-Mal (public treasury), known for meticulous, verified
record-keeping — a direct thematic fit for a module that now wraps a deterministic, audited engine rather
than estimating. MAL is now registered in `agent_personas.json` with this codename. The module id and
folder name (`MAL`, `MAL__financial_engine/`) are unchanged — only the identity-collision field moved.
"MAL/Zayd" refers to the same module throughout: MAL is the module id embedded in file paths, folder
names, and existing schema `module` constants (left alone to avoid an unnecessary rename ripple); Zayd is
its presented persona codename, the same relationship "Governor" has to Coordinator+Ammar underneath.

## What this does NOT change

- `money-rules.md` and `drive-db.md` are unchanged by this ADR, exactly as `drive-db.md`'s own prior
  amendment record states a pattern should work: reconcile a derived artifact to its governing rule,
  don't touch the rule itself.
- MAL/Zayd's `strict_local` privacy level is unchanged. No real figure moves to Drive via PFA; it was
  already going there, if at all, via PFOS's own `drive.file`-scoped, encrypted, no-keys-in-Drive sync —
  this ADR does not add a new path for data to leave the device.
- `learnings_log.jsonl` and `decisions.jsonl` are unaffected; they were never a monetary source of truth.
- No code has been committed or pushed. This ADR and the schema/persona-registry edits it documents are
  staged in a local clone pending owner review.

## Open item

PFOS's actual engine code has not yet been physically copied into `nizamcore` — that is the next step,
once the owner confirms the folder placement (`PFOS__personal_finance_app/` or an agreed alternative,
per the repository-merge plan) and this ADR's four decisions. Until then, D2's "sync from PFOS" step has
no PFOS to sync from inside `nizamcore` yet; the schema/routine changes in this ADR are the contract the
sync step will be built against once the engine lands.
