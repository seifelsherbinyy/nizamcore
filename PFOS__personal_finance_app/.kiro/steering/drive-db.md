# Drive-as-Database (design contract)

> **AMENDED 2026-09-20 under decision D-S(a).** Drive is the durable **evidence and recovery mirror**; the
> **server tier (`finance.db`) is canonical**. This resolves the three-way conflict between this file's
> former "Drive is the canonical store" line, PFOS governance-pack file 14 ("Drive is one-way reviewed
> mirror/archive, not live ledger"), and objective O1 §8. It matches what `tech.md` **D1** already stated:
> "the SERVER tier will use VPS + SQLite - this Drive-JSON store is the Profile-A build, NOT the final
> database." Recorded in `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` §3.1 as the resolution of conflict **C-1**,
> together with pipeline decision **D-A** (server `finance.db` canonical).
> **Unchanged by the amendment:** the `drive.file` scope, the no-keys-in-Drive rule, atomic writes,
> snapshots, the concurrency protocol, the Dexie offline mirror, and the one-time Picker import.
> Superseded wording is quoted in the amendment record at the end of this file, not deleted.

- **Scope:** `https://www.googleapis.com/auth/drive.file` — the app only ever sees files it created + files the user explicitly picks. NEVER request `drive` (full) scope.
- **Canonical store: the server tier's `finance.db`** (`src/server/db/**`, `node:sqlite`, WAL, `synchronous=FULL`, checksum-ordered append-only migrations). Exactly one authoritative writer per canonical domain — `transactionsRepository` for monetary facts. No second writer, in either tier.
- **Drive's role: the durable evidence and recovery mirror.** `nizam_db.json` inside a NIZAM app folder is a **derived projection** of canonical state, not the source of it. A projection carries a `mirrorOf { storeRef, schemaVersion, projectedAt, sourceAuditVersion }` stamp so a reader can always tell a mirror from a source. Schema in `src/lib/db/schema.ts`, validated with zod.
- **A Drive edit or a newly uploaded file is EVIDENCE, never a canonical mutation.** Required flow: `Drive discovery → EvidenceRecord → parse/normalize → dedupe/reconcile → canonical writer → derived projection → Drive read-back receipt`. Nothing discovered in Drive writes canonical state directly.
- **Drive holds encrypted DATA only — never keys, secrets, tokens, credentials, OTPs/PINs, private keys or `.env` values.** Unreviewed transaction candidates are device-local and must not reach a Drive-bound payload.
- **Writes are atomic:** write to a temp file then update; keep the previous version id; drop a dated snapshot `nizam_db.YYYYMMDD-HHmm.json` on each successful save (retain N).
- **Persistence is not landed until read-back confirms it.** A successful upload response alone is insufficient; a failed mirror must be detectable and must never masquerade as success.
- **Concurrency:** use Drive file version/etag; if remote changed since last pull -> run 3-way merge (base = last-synced, local = cache, remote = drive). Fallback: last-write-wins WITH an audit entry in `meta.conflicts`.
- **Offline:** Dexie is the working mirror; a `dirty` queue flushes to Drive when online.
- **Import of EXISTING data:** the master_ledger CSV (and credit_limits) are imported ONCE via Google Picker (grants drive.file on the picked file), parsed per `data/ledgers/LEDGER_SCHEMA.md`, deduped, and merged — through the ingestion pipeline and the canonical writer, not by writing Drive directly.
- **No external/organizational data** is ever read or written by this app — it is a personal-finance app bound to the user's own personal Drive only.

## Amendment record (D-S(a), 2026-09-20)

**Superseded wording, retained for traceability:**

> - **Canonical store:** one JSON file `nizam_db.json` inside a NIZAM app folder in the user's Drive. Schema in `src/lib/db/schema.ts`, validated with zod.

**Why it was superseded.** `tech.md` D1 had already declared the Drive-JSON store the Profile-A build
rather than the final database, and the repository has held two canonical stores with no bridge, no shared
identity and divergent correction semantics — recorded as finding **F7** in
`docs/plans/nizam-transaction-capture-pipeline-plan.md`. Leaving this file asserting Drive as canonical
kept the highest-ranked authority in the project contradicting both the decision and the code.

**What still needs doing before the mirror can be trusted with real data**, each tracked as a finding in
the pipeline plan and as tasks in `.kiro/specs/transaction-capture-pipeline/tasks.md`:
**F5** candidates are currently serialized into Drive despite being called device-local (fix is decision
**D-G**, shared with `hermes-governed-workflows` D-5 — answer it once, there); **F6** `saveDb` has no
`If-Match` on the media PATCH, so a concurrent remote write can be overwritten; **F12** no tombstones, so
a deletion can resurrect. Until those land, **do not enable the mirror for real data.**

**Not changed by this amendment:** `money-rules.md` in any respect; the `drive.file` scope; the
no-keys-in-Drive rule; `AC08`, which enforces the scope and is unaffected. No schema version was bumped
and no migration was performed.
