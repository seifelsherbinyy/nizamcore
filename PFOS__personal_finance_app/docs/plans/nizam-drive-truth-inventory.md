# NIZAM Drive Truth Inventory — canonical Drive state as observed 2026-09-20

Status: **INVENTORY AND RECONCILIATION ONLY. No implementation authorized by this document.**
No Drive write was performed. No file under `src/` or `tests/` is changed. No migration is proposed.
No owner decision is answered here; two are opened and one is narrowed, all in
`nizam-financial-objectives-alignment-plan.md` §4, which remains the single decision register.

Companion documents, none of which this one supersedes:

- `docs/plans/nizam-transaction-capture-pipeline-plan.md` (Rev 2) — segments S1–S12, decisions D-A–D-K.
- `docs/plans/nizam-financial-objectives-alignment-plan.md` (Rev 1) — objectives O1–O11, decisions D-L–D-W.
- `.kiro/specs/transaction-capture-pipeline/` and `.kiro/specs/financial-snapshot-interface/` — the live boards.

---

## §0 Why this document exists, and the identifier rule it obeys

The task that produced it asked for the canonical Drive state to be inspected and reconciled against the
repository, because every precedence ladder in the objectives pack names a rank-3 parent document
(**PFOS v1.3 FINAL**) that the repository does not contain. That absence is recorded as **G-2** in the
alignment plan and as the substance of **D-M**. Until this session, no one had looked.

### 0.1 The identifier rule — why you will not find a Drive id below

`.kiro/steering/two-agent-vps.md` §0b lists, as items that must never appear in a tracked file **not even
as an example**, "Google Drive folder ids, file ids, or account addresses". §7 requires a harness check
that `ops/**` and all fixtures contain no deployment particular. The originating task separately
prohibited "any Drive identifier of a private document in any committed artifact".

The task's own Phase-1 output specification asked that every inventory row "carry a Drive id". **That
instruction is overridden by steering**, which outranks a task instruction. Resolution, so the inventory
is still usable:

- This document cites **aliases** (`DOC-PFOS-V13-FINAL`, `DRIVE-ROOT-CURRENT`, …).
- The alias→id resolver lives **outside the repository tree** at
  `~/.gdrive_personal/nizam_alias_map.json`, alongside the connector that needs it.
- **Never copy that resolver into the repository.** It is the one artifact here that would fail the §7
  check on sight.

### 0.2 Data discipline — three Drive artifacts are radioactive

Three retrieved artifacts contain **real financial data**: the raw SMS transactional history
(`DOC-SMS-RAW`), the forensics summary (`SHEET-FORENSICS`) and the historical ledger CSV
(`LEDGER-CSV-MASTER`). Every figure in them is a real amount from the owner's accounts.

**None of them may be committed, quoted with figures, or used as a test fixture.** `money-rules.md`,
`AGENTS.md` ("synthetic fixtures and redacted identifiers") and the harness check AC07 all bite here.
Where a count from the forensics summary is cited below it is a **message count**, never an amount.

### 0.3 Evidence labels

| Label | Meaning |
|---|---|
| **VERIFIED** | Observed this session, in this session's output, and reproducible by the command named. |
| **UNVERIFIED** | Plausible and recorded, but not observed. Never used to support a conclusion. |
| **BLOCKED** | Could not be observed because a gate or a defect prevented it. The gate is named. |

---

## §1 Connector and authorization state

| Item | State | Evidence |
|---|---|---|
| Connector | `~/.gdrive_personal/connector/gdrive_connector.py`, venv-local Python | **VERIFIED** |
| Account | owner's personal Google account | **VERIFIED** via `whoami` |
| Granted scope | **`drive.readonly`, exactly and only** | **VERIFIED** via `whoami` |
| Re-authorization | **Not performed, and deliberately not performed.** `whoami` succeeded against the existing token, so the credential already exists and works. Minting or refreshing one would be a credential operation, which is owner-in-the-loop under `two-agent-vps.md` §2a. | **VERIFIED** |
| Writes | **None. Zero Drive write operations this session.** | **VERIFIED** — the granted scope makes a write impossible, and no write was attempted. |
| Subcommands | `auth, whoami, ls, read, tree, inspect, search, download` | **VERIFIED** via `--help` |

### 1.1 The scope contradiction, recorded as a finding

**Finding F-DRIVE-1 (severity: MEDIUM, design-level, no action this session).**

The connector holds **`drive.readonly`**, which reaches the owner's whole Drive. The application
contract is **`drive.file` only** — `tech.md` says "scope `drive.file` ONLY … never request full `drive`
scope", and `drive-db.md` repeats it. These are **not in conflict today**, because they are two different
clients: the connector is a local read-only inspection tool, and the app is the thing bound to
`drive.file`.

They *would* conflict the moment app behaviour is designed around what the connector can see. That is a
live risk rather than a theoretical one, because PFOS v1.3 FINAL §13.4 and its §51 authority matrix both
assume a "research brain" that **searches across pre-existing Drive documents** — which `drive.file`
cannot reach, since it grants access only to app-created files plus files the owner explicitly picks.

**Rule this document adopts and recommends:** the connector is an *inspection instrument for planning*.
Nothing it can read may be assumed reachable by the application. Any design that needs broad Drive
search is blocked on a scope decision that `tech.md` currently forbids outright.

### 1.2 The connector defect that blocked retrieval, and the workaround

**Finding F-DRIVE-2 (severity: LOW, external tool, worked around — not repaired).**

`gdrive_connector.py` `cmd_read` ends in `print(text[:20000])`. On Windows the console encoder is
cp1252, and every Google Docs export begins with a UTF-8 BOM (`\ufeff`), so the command dies:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\ufeff' in position 0
```

This affected **every Google Doc**, which is most of the canonical corpus. Two notes for whoever hits it
next:

- `PYTHONUTF8=1` set through `cmd`'s `set VAR & …` chaining **fails worse** — the trailing space becomes
  part of the value and Python aborts with `preconfig_init_utf8_mode: invalid PYTHONUTF8 environment
  variable value`.
- **The working route is `download`, not `read`.** `cmd_download` writes raw bytes to the ingress
  sandbox with no console encoding step, so it is immune; it also avoids `read`'s 20,000-character
  truncation, which matters because the main contract is 136,320 characters.

The connector lives outside this repository and **was not modified**. Everything below was retrieved by
`download` and then read from the sandbox.

---

## §2 Drive inventory — the canonical corpus

### 2.1 Two roots share the name `47_NIZAM`

| Alias | Name | Modified | State |
|---|---|---|---|
| `DRIVE-ROOT-CURRENT` | `47_NIZAM` | 2026-08-31 | **VERIFIED** present, 7 children. |
| `DRIVE-ROOT-LEGACY` | `47_NIZAM` | 2026-05-21 | **VERIFIED** present. Contents not enumerated this session. |

**They were not merged, and must not be merged as a housekeeping act.** Two independent authorities say
so. The knowledge map's own naming rule: *"Do not treat newest modified timestamp as automatically
authoritative"* and *"Files named SUPERSEDED remain historical/reference unless a later explicit decision
changes that status."* And `BOOTSTRAP.json` records **DEF-001**, a defect where two byte-identical
`MASTER_INDEX.md` files existed 80 seconds apart; the resolution renamed the older one and taught the
upsert helper to **refuse** a name-based write when more than one file shares the name. Same-name
collision is a known, already-bitten hazard in this Drive.

**Classification of the legacy root is deferred, not skipped.** It needs a content-level comparison, and
the knowledge map's own "UNRESOLVED / REVIEW" section already lists root-level duplicate candidates as
requiring exactly that, with *"no deletion has been performed"*. Deciding it is an owner call about the
owner's Drive, and it is not on this task's critical path.

### 2.2 The finance domain

`DRIVE-FIN-PFOS` = `05_FINANCE/PFOS_Personal_CFO`. **VERIFIED**, 15 items at depth 4:

```
PFOS_Personal_CFO/
  01_Product_Blueprints/
    01_PFOS_Product_Constitution_and_Problem_Solution_Logic.md
    02_PFOS_Data_Architecture_Integrations_and_Security.md
    03_PFOS_Financial_Intelligence_Decision_Forecasting_and_Learning.md
    04_PFOS_UX_UI_User_Journeys_Research_and_Delivery_Roadmap.md
  02_Transaction_Forensics/
    00_Raw_Evidence/
      00_RAW__SMS_Transactional_History__2026-07-25_to_2026-08-26     <- REAL DATA
    01_Processed_Ledger/
      PFOS_Transaction_Forensics_2026-08-26                          <- REAL DATA
  PFOS_Financial_Investigation_Handover_2026-08-19
INDEX - 05_FINANCE
NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.1_TURN1
NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE
```

The four blueprints are the four PFOS source documents that v1.3 FINAL §32 lists in its own source
inventory. They are **UNVERIFIED** — present and named, not yet read.

### 2.3 Retrieved artifacts, with hashes

| Alias | Export bytes | SHA-256 of exported bytes | State |
|---|---|---|---|
| `DOC-PFOS-V13-FINAL` | 137,196 | `2766e17bb8583ff7db19384428377da85edd16cce494c259035a545ff56de80d` | **VERIFIED**, read in full (4,634 lines) |
| `DOC-KMAP-INDEX` | 7,174 | `4774590d23151925b1529e60f61f58bffdc755a6948206d58848013f144dbf4f` | **VERIFIED**, read in full |
| `SHEET-FORENSICS` | 1,136 | `ba135edd5bb56ecc4c8bd4647963d5571e12098e158538364ffe73969c4d7877` | **VERIFIED**, read in full |
| `LEDGER-CSV-MASTER` | 495,754 | `8e953e7242f3f5b8e332bcdaf613de8aa0604fcce45bfa70842150404d3e68e9` | **VERIFIED** hash + 1,218 lines. Content not re-read this session. |

Hashes are over the **exported byte stream**, not over the live Google Doc. A Google Doc has no stable
byte identity, so an export hash pins *what was read*, not *what the document is*. Re-exporting after an
edit will differ; re-exporting an unedited doc should not. Recorded so the next session can tell which
happened.

### 2.4 The version lineage of the master contract

**VERIFIED** present on Drive, all four:

| Alias | Name | Modified |
|---|---|---|
| `DOC-PFOS-V11-TURN1` | `…v1.1_TURN1` | — |
| `DOC-PFOS-V13-SUPERSEDED` | `…v1.3_PRE_NR_INDEX_SUPERSEDED` | 2026-08-13 |
| `DOC-PFOS-V13-FINAL` | `…v1.3_FINAL_DRIVE_SAFE` | 2026-08-13 |
| — | v1.0, referenced in §32's source inventory as "baseline to upgrade" | not located |

The two 2026-08-13 documents are distinguishable on content, not on timestamp: the `SUPERSEDED` one is
`PRE_NR_INDEX`, and the `FINAL` one carries §56 `NR-001..NR-089`. **The document retrieved and hashed
above is the later of the two.** That resolves what would otherwise be a second same-day collision.

### 2.5 The retrieval layer

A machine-retrieval layer dated 2026-09-15 sits at the current root: `BOOTSTRAP.json`, `INDEX.json`,
`RETRIEVAL_MANIFEST.json`, `SOURCE_REGISTRY.json`, plus `README_RETRIEVAL.md` (2026-09-10) and
`MASTER_INDEX.md` (2026-09-01). Only `BOOTSTRAP.json` was read. The other four are **UNVERIFIED** and are
the obvious next read, because `SOURCE_REGISTRY.json` is likely the authoritative answer to "what is
canonical" that this document had to reconstruct by hand.

---

## §3 What Drive says that the repository needs to know

### 3.1 `BOOTSTRAP.json` independently corroborates D-A and D-S

`BOOTSTRAP.json` is stamped `NIZAM-HEALTH-INTELLIGENCE v0.2.0`, `generated_by: deterministic_engine`,
`llm_contribution: "none"`. Its `storage_authorities` block assigns:

| Surface | Authority, verbatim |
|---|---|
| drive | "organized durable knowledge, journals, ledgers, reports, indexes, manifests" |
| github | "code, schemas, tests" |
| **vps** | **"runtime databases, ingestion, deterministic analytics, caches, cron, secrets"** |

This was authored for the health domain, by a different engine, at a different date — and it lands on the
**same split** as `tech.md` D1, as the `drive-db.md` amendment made under D-S(a), and as D-A(a)'s
"server `finance.db` is canonical". Three independent artifacts now agree that runtime databases live on
the VPS tier and Drive is the durable-document surface. **D-A and D-S are corroborated, not reopened.**

Its `hard_rules` also restate, unprompted: *"Money is integer milliunits; 1 EGP = 1000 milliunits"*,
*"Drive scope is drive.file only; Drive never holds keys or secrets"*, and *"Missing data stays missing:
null or insufficient_data, never imputed"*. The first two are `money-rules.md` and `tech.md` verbatim.
The third is the same doctrine as the pipeline plan's exception-queue rule, arrived at independently.

### 3.2 A finding about VPS state that this document does not resolve

**Finding F-DRIVE-3 (severity: MEDIUM, UNVERIFIED, recorded not acted on).**

`BOOTSTRAP.json` describes what reads as an **operational host**: `runtime` root `/opt/personal-health`,
a database, a read-only MCP server, and cron with a UTC→Africa/Cairo conversion and a `target_local_time`.
Its `freshness.vps` carries an observed timestamp of 2026-09-15.

`pfos-current.md` D2 records the VPS as "OVHcloud, **NOT provisioned**", and `two-agent-vps.md` §2 keeps
G1 (provision/harden) human-gated.

**It is UNVERIFIED whether these describe the same host.** A health-intelligence runtime at
`/opt/personal-health` and the two-agent finance/life deployment may be entirely separate. Resolving it
by probing the host would be a network operation against infrastructure this session has no authorization
to touch. **Recorded as a question for the owner, and G1 is not marked as anything.** A gate is done when
observed and recorded; nothing here observes G1.

### 3.3 PFOS v1.3 FINAL corroborates the pipeline plan's architecture

Read in full. The parts that bear on work already planned:

**The mandated pipeline shape (§20.1) is the pipeline plan's shape.** Verbatim:
`RAW SOURCE → VALIDATED EVENT → DETERMINISTIC LEDGER → DETERMINISTIC CALCULATION → POLICY → LLM
EXPLANATION`, with the explicit prohibition `Never: RAW TEXT → LLM GUESS → FINANCIAL TRUTH`.

**§5.2 names `Immutable Event Inbox` between the registries and the `Transaction Ledger`** — the staging
surface S8 specifies. **§27.6 J2** gives the per-transaction journey as
`raw event → parse → exact duplicate check → normalize → ledger candidate → recalculate safe-to-spend →
material notice or one correction → later statement match`, and **J4** gives statement reconciliation
including *"resolve reversals/refunds/duplicates"*, an **exception review** step and a **period close**.

**§43 assigns exactly one authoritative writer per canonical domain**, financial ledger → the PFOS
deterministic ledger service, with the dashboard and conversational surface as non-authoritative
consumers. **§52.1 requires `FinancialEvent` to carry an `idempotency key` and a `verification state`.**

Three consequences worth stating plainly:

1. The pipeline plan's segmentation was **not** over-engineering. The canonical contract independently
   requires the same stages, the same candidate-then-reconcile shape, and the same single-writer rule.
2. **The contract is thinner than the plan, not thicker.** It names the stages and leaves every mechanism
   unspecified: there is no fingerprint algorithm, no dedup key composition, no transfer-pair matching
   rule, no split rule, and — searched across all 4,634 lines — **no mention of SMS, OFX, CSV or any
   import format at all.** The plan's S1–S12 mechanisms are additive, and nothing in the contract
   contradicts them.
3. **F7 is upgraded from a finding to a release-gate failure.** The repository currently has two canonical
   stores (the Drive JSON projection and the server tier). §43 plus AC-48 ("no two services can
   independently become authoritative writers for the same canonical domain") place that inside release
   gate RG-5, and §54.2 says no acceptance criterion may be "silently skipped, weakened, or reworded".
   This does not change D-A's answer — it raises the cost of not executing it.

### 3.4 What v1.3 FINAL contradicts

Recorded as findings because each one is a place where adopting the Drive document naively would break a
steering rule.

**F-DRIVE-4 (HIGH) — it ranks itself above the repository's contracts, and does not place steering.**
§55.2's precedence ladder is: safety/platform policy → newest explicit owner direction → **this contract**
→ owning subordinate contract "that does not conflict with this contract" → verified runtime evidence →
historical documentation. `.kiro/steering` appears nowhere in that ladder; it is mentioned only inside
§55.3's research step. The repository's rule is the opposite: steering outranks contracts, which outrank
supporting docs, and `two-agent-vps.md` is authoritative in the server/agent/bot area.

Two facts defuse this, and both must be recorded rather than assumed:

- Its own tier 2 is **"newest explicit owner direction"**, which every later owner decision recorded in
  steering satisfies. The ladder therefore does not actually demote steering; it just fails to name it.
- **The retrieved artifact is the `DRIVE_SAFE` mirror, which by its own §42.3, §55.4 and C-15 is not
  canonical** — *"The LOCAL_FULL sibling remains canonical when the two differ."*

**Adopting a self-declared non-canonical copy as a governing authority would be incoherent.** The correct
posture is the one the repository already has: treat v1.3 FINAL as strong rank-3 evidence of owner
intent, keep steering first, and record the ladder conflict rather than silently resolving it either way.

**F-DRIVE-5 (MEDIUM) — it assumes Telegram throughout; Slack appears zero times.** Its entire interaction
model (§7.1 *"Telegram remains the preferred conversational interface for MVP"*, §27.5 response hierarchy,
§11.2 user-ID allowlist, §50's Telegram column, §44.4 and AC-49's failure-independence criteria) is
written around a Telegram surface. The repository's transport policy is **Slack Socket Mode as the sole
transport, with all Telegram aliases revoked**. The contract predates that decision and has no concept of
it. Its transport-independent rules (Telegram is a non-authoritative consumer; never a canonical writer;
never bypasses a port) transfer to Slack unchanged; its transport-specific rules do not transfer at all.

**F-DRIVE-6 (MEDIUM) — it would fail the §7 no-deployment-particular check if committed.** The
`DRIVE_SAFE` redaction did hold for secrets, personal history and monetary figures: every monetary field
in the document is the literal placeholder `<DETERMINISTIC_ENGINE_VALUE>`, and no hostname, IP, bot id,
numeric Telegram id, webhook path or Drive id appears. But §44.1 and §26.1 retain a **server path**, a
**Drive root folder name**, absolute **`D:\NIZAM` workspace paths**, and §26.4 names historical hosting
providers. Under §0b those are particulars.

**Recommendation: do not commit this document into the repository.** Extract its normative clauses —
§56's `NR-001..NR-089` index is built for exactly that — and cite them. Note also that the `D:\NIZAM`
paths are simply **wrong**: this tree is at `C:\Users\selsherb\NIZAM`. §44.1 anticipates this and
self-limits: *"No new exact repository path is canonical merely because this contract suggests a
component. Implementation agents MUST inspect the current tree before creating files."*

**F-DRIVE-7 (MEDIUM) — §27.1 licenses money into the other repository.** It resolves the PFOS/MAL naming
question by permitting code paths such as `MAL__financial_engine`, which is a `nizamcore` **Python**
namespace. `two-agent-vps.md` §1 holds the invariant *"there will never be a second implementation of
money"* and keeps the finance agent on Node/TypeScript reusing `src/lib/money/`. §27.1's own guard
("MUST NOT create competing financial truth systems", AC-25) points the same way, so this is a naming
trap rather than a real instruction — but followed literally in code it would put money in `nizamcore`.
**The invariant wins.**

**F-DRIVE-8 (LOW) — its mandatory `RECORD` step cannot be executed under the repository's gates.** §55.3
makes every work cycle end in a Drive write confirmed by read-back (§42.3, §55.4, AC-47). Drive OAuth
consent is **G5, human-gated**, and the `drive-db.md` amendment says the mirror stays off for real data
until F5/F6/F12 land. The read-back requirement is therefore a **design obligation for when the mirror is
enabled**, not a per-change action an agent performs. Worth keeping, because it is the same
canonical-read-back-before-acknowledging principle the pipeline plan already adopted for posting.

### 3.5 A seventh numbering namespace

**Finding F-DRIVE-9 (LOW, but a recurring source of confusion).**

v1.3 FINAL has **its own O1–O6** — Scale net worth, Eliminate destructive financial behavior, Daily
financial command, Behavioral self-understanding, Regain discipline, Journal as backbone. These are
**not** the `FINANCIAL/O1..O11` objectives. O1 means "Scale net worth" in one document and "transaction
capture and ledger integrity" in the other.

Six numbering namespaces were already live in this project. **This is the seventh**, and the first that
collides head-on with an existing one on the same letter-and-digit. Its other systems — §0–§56,
`AC-01..AC-50`, `RQ-001..RQ-037`, `C-01..C-20`, `OD-01..OD-08`, `NR-001..NR-089`, `RG-1..RG-7` — do not
collide, and nothing in the document maps any of them onto `contracts/pfos/01..NN`.

**Citation rule this document adopts:** always qualify. `v1.3-O1` for the contract's outcome, `FIN-O1`
for the objective. An unqualified "O1" in any future artifact should be treated as ambiguous.

### 3.6 The SMS evidence is real, and it validates the exception design

`SHEET-FORENSICS` is a 30-day SMS reconstruction over 2026-07-25 to 2026-08-26. Reporting **counts only**:

| Category | Count |
|---|---|
| SMS messages scanned | 254 |
| Purchase-like alerts | 91 |
| Transfer-out alerts | 66 |
| Transfer-in alerts | 58 |
| Declines excluded | 20 |
| OTP / pre-auth excluded | 8 |
| Reversal notices | 7 |
| Exact duplicate SMS | 3 |

Every exception class the pipeline plan designed for **occurs in real data at material volume**: declines
that must not post, pre-authorizations that must not post, reversals that must pair with an original,
exact duplicates that dedup must catch. The summary also carries a line item for external/P2P transfer
outflow *"requiring classification"* — a real, non-empty unresolved-classification queue, which is
precisely the case the plan refuses to guess at.

**This is the strongest available evidence that S1–S12's exception handling is necessary rather than
defensive.** It also means the raw evidence is a **Google Doc of SMS text**, not a bank export — which
bears directly on the D-I source-order question opened below.

---

## §4 Reconciliation against the repository

### 4.1 The originating task's premise was stale — probed, not assumed

The task carried an `integrity_gap_to_repair_first` block asserting that six Increment 0 artifacts
"DOES NOT EXIST". **All six were probed. All six exist.**

| Claimed absent | Probe result |
|---|---|
| `contracts/programs/FINANCIAL_NIZAM_OBJECTIVES.md` | **VERIFIED present** |
| `contracts/programs/financial-nizam-objectives/` | **VERIFIED present**, 12 artifacts |
| `.kiro/specs/financial-snapshot-interface/` | **VERIFIED present**, 3 files |
| `.kiro/specs/transaction-capture-pipeline/` | **VERIFIED present**, 3 files |
| D-N correction in `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` | **VERIFIED present**, 1 match at §3.1 |
| `AMENDED` marker in `.kiro/steering/drive-db.md` | **VERIFIED present**, 1 match |

**Increment 0 was therefore not reverted and not redone.** Acting on the stale premise would have
destroyed verified work. Increment 0 stays `done` on its board; the premise is recorded here as stale so
the next session does not re-litigate it. The `ANSWERED` markers in the alignment plan were also probed:
**8 present**, consistent with the nine decisions marked in Increment 0.

### 4.2 F-TREE-1 — resolved by restoration

The task reported `.kiro/steering/two-agent-vps.md` missing. **Confirmed real**, and repaired.

| Evidence | Observation |
|---|---|
| Working-tree state | unstaged deletion (` D `) — the file was deleted, not renamed, not moved |
| HEAD | tracked and intact at 19,783 characters |
| Successor search | **none.** Keyword candidates (`drive-db`, `product`, `tech`) cover none of its subject matter |
| Inbound citations | **97 across 23 files**, including `contracts/pfos/12` (8×) and `_PFOS_BUILD_LOG.md` (36×) |
| Precedent | commit `7a43d2f restore(steering): recover the nine deleted steering files` |

Resolution: `git -P checkout -- .kiro/steering/two-agent-vps.md`, scoped to that single path so no other
working-tree change could be touched. **Confirmed restored and re-injected as active steering.**

Rejected alternatives: leaving the 97 citations dangling; and hunting for a successor that the search
showed does not exist. Deleting the authoritative document for the server/agent/bot area while 23 files
cite it is a defect, not a cleanup.

### 4.3 Repository state as observed

| Item | Observed |
|---|---|
| HEAD | `5652edf docs(ops): A3 receipt for the live R2 governor timing authority` |
| Branch | 4 commits ahead of `origin` |
| Working tree | dirty; **57** entries at last count, of which 15 are pre-existing owner work under `src/`+`tests/` — **untouched by this session** |
| Gate baseline | **19/21.** AC14 (clean tree) and AC15 (push-ready) fail by construction while the tree is dirty; this is the normal dirty-tree result under D-H, not a regression |
| Test floors | `AC04 --min 3009`, `AC19 PROTECTED_TEST_FLOOR = 2301` |

`AC12` hard-requires exactly 5 rows and parses a single-digit contract number. Anything that adds a
contract must account for both, which is one more reason §5 below does not add one.

---

## §5 Decisions — one narrowed, two opened

These belong to `nizam-financial-objectives-alignment-plan.md` §4, which stays the single register. The
text below is the substance; §4 carries the rows.

### 5.1 D-M — narrowed, **not** answered

**Status: still OPEN. `None offered` stands.**

What this session established:

- **The rank-3 parent exists.** `DOC-PFOS-V13-FINAL`, dated 2026-08-13, retrieved, hashed
  (`2766e17b…e80d`), read in full. G-2's "absent from the tree" was accurate about the *tree*; it is not
  absent from *Drive*.
- **But what exists is the `DRIVE_SAFE` mirror, which declares itself non-canonical.** Its own header,
  §42.3, §55.4 and C-15 all say the **`LOCAL_FULL` sibling is canonical when the two differ**.
- **`LOCAL_FULL` is not on Drive.** A 32-hit search across the knowledge root returned no `LOCAL_FULL`
  variant. It is local-only by design, and **cannot be produced from Drive evidence at all**.

So D-M's option (a) — "produce it and record its index and hash" — is **half-satisfied**: a hash now
exists for the mirror, and the mirror is a usable, substantive rank-3 document. The canonical text
remains unobtainable by any means available to this session.

**The precedence ladder is NOT declared satisfied.** Recording a mirror's hash and calling rank 3 populated
would be exactly the "unfalsifiable rank" defect D-M was opened to name. Option **(b)** — annotate the
ladder to say rank 3 is served by a self-declared mirror, with the canonical sibling outstanding — is
now the cheapest honest resolution, and is what I would recommend if the owner cannot produce
`LOCAL_FULL`. **Only the owner knows whether it exists to be produced.** That is why this stays
`None offered`.

### 5.2 D-Z — opened: where does an FX rate live?

**Status: OPEN. Recommendation offered.**

`FIN-O1` acceptance criterion 10 requires multi-currency handling. The repository has EGP milliunits and
no FX representation. **v1.3 FINAL does not settle it**: searched in full, it has no rule about where an
FX rate is stored, how it is versioned, whether a converted amount may be persisted, or what the
reference currency is. Its only normative FX statement is negative — §41.1 forbids an LLM from being the
source of a currency conversion. Its §17 research backlog lists *"reliable FX sources"* and EGP
purchasing-power methodology as **Priority A prerequisites for advanced PFOS**, i.e. explicitly unsettled.

| Option | Assessment |
|---|---|
| (a) Add FX columns to `transactions` | **Rejected.** `assertMonetaryCoverage` is bidirectional, so a new monetary column forces a coordinated change across every write path — for a capability nothing currently consumes. |
| **(b) Retain the source-supplied FX on `source_events.raw_payload`; derive on read** | **Recommended.** The captured rate is *evidence*, and `source_events` is already the immutable evidence surface. Nothing is persisted that could drift from the ledger, no migration is needed, and the derived figure carries its own as-of date. It also matches v1.3 FINAL §41.1: conversion happens inside the deterministic engine, and the stored fact stays the source's. |
| (c) Defer entirely | **Rejected.** Criterion 10 is an acceptance criterion, not an aspiration. |

**Blocks:** `FIN-O1` criterion 10 and Increment 5 of the snapshot board. Nothing else.

### 5.3 D-Y — opened: D-I's source order is wrong for the evidence that exists

**Status: OPEN. Recommendation offered.**

D-I set an ingestion source order of **statements → SMS → OFX-if-offered**, reasoning that a statement is
the most structured and most trustworthy source. The Drive evidence changes the premise:

- The real, dated, 30-day transactional evidence that **exists right now** is `DOC-SMS-RAW` — a Google
  Doc of **SMS text**, already reconstructed into 254 scanned messages with reversals, declines,
  pre-authorizations and duplicates classified.
- No bank statement corpus was located on Drive this session. `LEDGER-CSV-MASTER` is a **derived ledger**
  (1,218 lines, Jul 2025–Jul 2026), not a set of source statements.
- v1.3 FINAL §27.6 **J4 makes statement reconciliation the *matcher*, not the *first source***: it
  arrives later and matches "provisional entries" that J2 already created from raw events.

So the contract's own journey model, and the evidence actually on hand, both point the same way: **raw
events come first and create candidates; statements arrive later and reconcile them.** D-I inverted that.

| Option | Assessment |
|---|---|
| (a) Keep statements-first | Leaves the only real evidence corpus unusable until a statement corpus is located, and contradicts J2/J4. |
| **(b) Resequence to SMS-first, statements as the reconciliation source, OFX if offered** | **Recommended.** Matches J2→J4, matches the evidence on hand, and does not change S1–S12's mechanisms — only which adapter is built first. |
| (c) Build both adapters before either is exercised | Doubles Increment 1's surface for no earned confidence. |

**One caution against over-reading this.** The SMS corpus is a **Google Doc**, so an SMS adapter's real
input format is unresolved — it may be document text rather than a message-per-row export. That is an
input-format question to settle before Increment 1, not a reason to keep an order the evidence
contradicts.

**Blocks:** Increment 1's adapter choice only. **D-Y does not touch D-C**, which remains the separate
open question of whether the CSV cutover happens at all.

---

## §6 Readiness matrix

**No row is marked done.** Statuses are VERIFIED / UNVERIFIED / BLOCKED only.

| Surface | State | Basis |
|---|---|---|
| **Drive — read access** | **VERIFIED** | `whoami` against an existing token; `drive.readonly`; 4 artifacts retrieved and hashed |
| **Drive — write / mirror** | **BLOCKED** | G5 (OAuth consent) is human-gated; the connector holds a read-only scope; `drive-db.md` keeps the mirror off for real data until F5/F6/F12 |
| **Drive — canonical corpus located** | **VERIFIED in part** | Finance domain enumerated; v1.3 lineage resolved; 4 retrieval-layer JSON artifacts and 4 PFOS blueprints **UNVERIFIED** |
| **Data — real transactional evidence** | **VERIFIED present, UNVERIFIED as ingestible** | 254-message SMS corpus exists and is classified; its raw form is a Google Doc, so the adapter input format is unresolved (D-Y) |
| **Data — statement corpus** | **UNVERIFIED** | None located on Drive this session |
| **VPS** | **UNVERIFIED, contradictory** | `BOOTSTRAP.json` describes an operational runtime; `pfos-current.md` D2 says not provisioned; same-host question unresolved (F-DRIVE-3). G1 is **not** marked |
| **Hermes / Slack transport** | **UNVERIFIED** | Not exercised this session. v1.3 FINAL assumes Telegram throughout and is silent on Slack (F-DRIVE-5) |
| **Repository gate** | **VERIFIED at 19/21** | AC14/AC15 fail by construction on a dirty tree under D-H |

---

## §7 Verification

**This document changes no file under `src/` or `tests/`.** `npm run typecheck`, `npm run lint`,
`npm run build`, `npm test` and `npm run verify:all -- --all` therefore **do not apply to it**, and none
were run for it. Claiming a green gate for a document-only change would be a false receipt. The 19/21
baseline in §4.3 is the **last observed** state, not a fresh run.

What was actually verified, and how:

| Claim | Method |
|---|---|
| Drive auth live, scope `drive.readonly` | connector `whoami` |
| 4 artifacts retrieved | connector `download` → sandbox → read from disk |
| 4 SHA-256 hashes, byte counts, line counts | Python `hashlib` over the exported bytes |
| Two `47_NIZAM` roots, v1.3 lineage, 05_FINANCE tree | connector `search` and `tree --depth 4` |
| v1.3 FINAL read in full | 4,634 lines, complete |
| Six "absent" artifacts present | filesystem probe per artifact |
| `two-agent-vps.md` deleted then restored | `git status --porcelain`, `git show` size, citation count, `git checkout` of one path |
| Repository HEAD, dirty count, ahead-count | `git log`, `git status --porcelain` |

**Not verified, and not claimed:** the VPS host identity; the four retrieval-layer JSON artifacts; the
four PFOS blueprints; the legacy root's contents; whether `LOCAL_FULL` exists anywhere.

---

## §8 What this document does not authorize

No code is written. No test is created or edited. No schema, migration or fixture is produced. No Drive
write is performed and none is authorized. No commit, no push. No credential is created, rotated or
printed. **No gate is advanced** — G1 and G5 are named as blockers, not as progress. D-C, D-E, D-H, D-V,
D-Q, D-G and D-B stay **OPEN** and are not answered here. D-M stays **OPEN** and narrowed. D-Z and D-Y
are **opened with recommendations the owner has not accepted**.

The alias→id resolver at `~/.gdrive_personal/nizam_alias_map.json` **stays outside the tree**.

---

## §9 Revision 1 note

First revision. Nothing superseded.

Method: Drive was inspected with an existing read-only credential rather than a new one. Every artifact
was retrieved by `download` into the connector's sandbox and read from disk, because the connector's
`read` path is broken on Windows for any document with a BOM (F-DRIVE-2). The master contract was read
in full rather than sampled, which is why §3.4's contradiction list can state what the document
*does not* contain — no SMS, no OFX, no CSV, no FX-storage rule — as a search result rather than an
impression.

The two most consequential findings are **§3.3's** corroboration that the canonical contract independently
mandates the pipeline plan's architecture, single-writer rule and candidate-then-reconcile shape — and
**§3.4's** F-DRIVE-4, that the same contract ranks itself above the repository's contracts while omitting
steering from its ladder, in a copy that declares itself non-canonical. The first means the plan is on
solid ground. The second means this document must never be promoted to an authority without the owner
settling the ladder.
