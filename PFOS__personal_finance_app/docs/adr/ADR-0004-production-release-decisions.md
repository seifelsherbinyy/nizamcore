# ADR-0004 — Durable decisions for the Slack-finance production release

**Status:** ACCEPTED (owner-approved 2026-09-22)
**Owner authority:** plan `NIZAM-SLACK-FINANCE-PRODUCTION-2026-09-22`, `durable_decisions` block, approved in
session and executed on the owner's instruction to continue to completion.
**Supersedes:** nothing. **Amends:** nothing. It *records* decisions that were previously open.
**Phase:** P1 of that plan.

---

## Why this file exists

The preceding decision package was carried in conversation under the labels **R3–R12** and was never
written to this repository. When the session record was compacted, those labels lost their content: only
R1 and R2 had been transcribed (into `contracts/CONTRACT_6_multicurrency_ledger_integrity.md` §5.7 and
`.kiro/specs/transaction-capture-pipeline/requirements.md` §2.12a). `docs/kiro/prompts/` holds no `011`
artifact and `docs/plans/` holds no master-plan file, so there was nothing durable to adopt.

This ADR replaces ephemeral labels with **repository-verifiable decisions**. Each one states what was
decided, what it forbids, whether it needs a migration, and where its enforcement lives. A decision that
cannot be checked against code or a check is not recorded here.

**The lesson, stated so it is not relearned:** a decision that exists only in a conversation does not
exist. Anything meant to govern implementation is transcribed before implementation starts.

---

## D-H — disposition of the dirty working tree

**Decision: reviewed partition.** Three buckets, three treatments.

| Bucket | Treatment |
|---|---|
| Project material | Committed in reviewed atomic groups. |
| Personal / non-project material | Moved to a private quarantine **outside** this public repository. |
| Ambiguous material | Held **unopened**, and the owner is asked for its disposition. |

**A local exclude is not a disposition.** Hiding a path from `git status` via `.git/info/exclude` would
turn `AC14` green while leaving the file exactly where it was, in a public repository's working directory.
That is the appearance of a clean release rather than a clean release, so it is prohibited as a substitute.
`.gitignore` remains correct for **generated runtime data** — build output, dependency trees, local stores —
because those are regenerable artifacts rather than material with a disposition question.

**A personal path name is never written into a tracked ignore file.** Naming a private matter in
`.gitignore` publishes the name, which is the harm the move exists to prevent.

**Why this and not the alternatives.** Committing everything would publish third-party personal material
irreversibly on a public remote. Ignoring everything would leave delivered project work invisible and the
release unreviewable. The partition is the only option that makes `AC14`/`AC15` green **and** publishes
nothing that should not be published.

**Recorded classification (P0, 2026-09-22).** 114 entries: **105 project**, **8 non-project**, **1**
resolved by the repository's own recorded reasoning. **No ambiguous entry remained**, so the plan's `H0`
gate was not raised. The eight non-project paths are listed with their sizes in the quarantine manifest,
not here — this file names no private matter.

The single resolved entry is a workstation keep-awake script. `.gitignore` already documents that family as
having "no importer, no project role, no secret, no deployment particular"; the capitalised sibling was
simply not matched by the existing pattern, so the pattern is extended rather than a new decision invented.

---

## D-J — notification durability

**Decision: transactional outbox.** Migration required (**schema version 10**).

A posting and the *intent* to notify commit in **one** transaction. Relay is a separate step that reads the
outbox. The guarantee is **at-least-once with deduplication**.

**Forbidden claim: exactly-once delivery.** No artifact may assert it. A sender and a receiver cannot agree
on a single delivery across a network partition, so the honest guarantee is at-least-once plus an
idempotent consumer, and the deduplication is what makes it *behave* once.

**What this replaces.** Commit-then-compose, under which a crash between commit and send lost the
notification silently. The loss was disclosed rather than fixed; the outbox fixes it.

---

## D-K — audit-log integrity

**Decision: append-only database triggers.** Migration required (**schema version 11**).

`UPDATE` and `DELETE` on the audit trail are refused by the engine, not by convention in application code.
The precedent is already in this repository: `src/server/signals/signalStoreSchema.ts` carries
`signals_append_only_update` / `signals_append_only_delete` and their audit-mirror pair, and `AC19` asserts
all four exist. The finance-side trail gets the same treatment for the same reason — a guard in application
code protects only the callers that remember to use it.

---

## D-Z — foreign-exchange evidence

**Decision: source-event raw payload plus a derived read.** **No migration.**

**Invariant: no FX conversion at ingest.** A rate observed in a source document is evidence about that
document. It is stored with the event and read through a derived accessor when a presentation layer needs
it. Converting at ingest would bake a rate into a stored monetary fact, and the fact would then be
unreproducible from its own source.

This is `money-rules.md` applied to currency: money is an integer count of milliunits in a stated currency,
and a conversion is a *derived view*, never a stored substitution.

---

## D-8 — deterministic admission before model tiering

**Decision: pre-tier admission.**

**Invariant:** local capture, deterministic financial reads, clarification requests and refusals never
reach model classification and never touch model spend.

The ordering is the mechanism. A refusal that has already been classified has already cost money and has
already shown the input to a model. Admission therefore runs first, and only what survives it can be
tiered. `src/server/hermes/ingressRouter.ts` already encodes the shape this depends on: a refusal carries
effect `none`, and `assertRoutedFinancialResult` requires module `mal` with effect `pfos_read`.

---

## D-SLACK-1 — sole live owner ingress

**Decision:** the `nizamfinancialapp` Slack Socket Mode process.

**Invariant: one consumer per Slack envelope.** Two processes reading the same subscription would each
believe they owned the turn, and the owner would receive two answers to one question — or worse, two
effects from one instruction.

This is consistent with the transport authority already in force: `src/server/hermes/ingressPolicy.ts` v2
names Slack Socket Mode as the **sole** transport with exactly `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` and
`SLACK_ALLOWED_USERS`, and `assertRevokedTelegramAliasesNotPresent` refuses any process presenting one of
the five revoked legacy aliases. **This ADR introduces no transport change; it records the consumer.**

---

## D-SLACK-2 — financial answer authority

**Decision:** deterministic PFOS engines only.

**Invariant: a model may explain, but may never source or modify money.** Every numeric financial value in
an answer comes from a deterministic engine reading the canonical store. A model may phrase, summarise or
explain that value. If the engine has no value, the answer says so — a model does not supply the gap.

This restates the standing tenet rather than creating it, and it is recorded here because a live channel is
exactly where the tenet would erode first.

---

## D-INGEST-1 — production ingestion state machine

**Decision:** evidence → candidate → **explicit** promotion.

**Invariant: an unverified candidate is excluded from every financial read.** Not most reads. Every read —
balances, budgets, forecasts, obligations, reports, reconciliation, duplicate lookups, coverage answers and
any mirror-bound payload.

The enforcement already exists and is not re-invented here: Contract 6 **§5.7** (`I5.7.1`–`I5.7.5`) permits
staging to be the disjoint `status='pending' AND verification_level='unverified'` subset of `transactions`
and makes distinctness a requirement **on every read**; requirement **§2.12a** narrows the reconciliation
universe to canonical statuses for the same reason.

---

## D-RELEASE-1 — the four commits already ahead of the remote

**Decision: audit, then include — and the audit passed.**

Audited 2026-09-22: `ba43912`, `2702235`, `5a5b882`, `5652edf`. Six files, **all** under `ops/`, **1,665
insertions, no deletions**, all documentation. An independent scan for credential shapes, private-key
blocks and address literals returned **zero** hits, and the harness's own `AC09` and `AC18` already pass
over this tree, which includes these commits.

**Fallback if an audit had failed** — recorded because the decision is only meaningful with its alternative:
branch from `origin/master` and cherry-pick only the reviewed commits. **Never** rewrite remote history to
remove one.

---

## What this ADR does not do

It approves no migration *execution*, no push, no deployment and no credential action. It records
decisions. Migrations 10, 11 and 12 are **authored and owned** under the plan's P3/P4 and are applied only
through the documented deployment mechanism, each with the rollback rule stated beside it.

**Migration numbering, corrected against the code — and corrected twice, which is the point.** The plan
named these `M009`/`M010`/`M011`. The migrator refuses an edited already-applied migration by checksum
(`T10`), so a wrong number is not a naming preference: it either collides with applied history or leaves a
hole in a series that must strictly increase.

**First correction (wrong).** I read `SCHEMA_VERSION = 9` and concluded the series held 1–9, making the
outbox version 10.

**Second correction (right, and verified by reading the series itself).** `SCHEMA_VERSION` in
`src/lib/db/schema.ts` is the **browser** Drive-JSON document version. It has nothing to do with the server
store. The server series is `MIGRATIONS` in `src/server/db/migrations.ts`, and it ends at **version 8**
(`ingestion_provenance_and_document_sets`); `SCHEMA_STATEMENTS` confirms keys `1,2,3,4,5,6,7,8` over 18
tables. So the next free version is **9**.

| Migration | Version | Owner | Rollback rule |
|---|---|---|---|
| Notification outbox | **9** | PFOS Contract 06 | Preserve the table and **disable the relay before** rolling the code back. Data is never dropped to undo a deploy. |
| Audit append-only triggers | **10** | PFOS Contract 06 | Retain all rows; restore the prior compatible trigger set. |
| Financial snapshots and receipts | **11** | PFOS Contract 06 | Append-only; unique version triple; **no monetary column** in a receipt; conflict-ignoring insert with read-back. |

**Why this is recorded rather than quietly fixed.** Two schema-version constants exist in this repository
for two different stores, and they are one apart, which is the most confusable possible arrangement. The
next reader who needs a migration number should find this paragraph and read `MIGRATIONS`, not infer from
whichever constant they happen to open first.

---

## Amendment 1 — D-H meets AC11 (recorded 2026-09-22, same day)

**What happened.** Staging the project material surfaced **30 `AC11` findings across 16 files**: an
organization-specific term in a tracked file. Every one of those files had been untracked for the whole
life of the repository, so the check had never been able to see them. `AC11` was not being lenient before;
it was being starved.

**One finding was not a documentation nicety.** `.agents/skills/validate-mcp-skills/**` documents
another organization's internal tooling. On a public remote that is a disclosure, not a style problem.
My P0 classification had put `.agents/` in the *project* bucket, which was wrong — it is IDE
agent-harness tooling, not this product — and `AC11` caught the mistake before the push. Recorded plainly
because an inventory that classified something wrong once will do it again, and the check is what stopped
it, not the inventory.

**The conflict, stated before it is resolved.** D-H says project material is committed. `AC11` says a
tracked file carries no organization-specific term. For a research corpus that cites another
organization's public documentation *by name*, both cannot hold. Two ways out were rejected:

- **Sanitize the corpus.** A provenance manifest whose publisher has been anonymized is no longer
  evidence, it is an assertion. That trades a verifiable citation for an unverifiable one.
- **Rewrite the URLs so the checker stops matching.** That is evading the gate, which is forbidden, and it
  would leave a check that passes while the term is still there.

**Resolution — the distinction is product versus input.**

| Treatment | Paths | Why |
|---|---|---|
| **Sanitized** | `src/server/hermes/financialResponse.ts`, `scripts/kiro/permissions.test.mjs`, `.kiro/specs/hermes-governed-workflows/design.md` | Product and core authority. In all three the organization name was **incidental**: a citation label, an arbitrary synthetic command name, and an unrelated host mentioned only to say it is unrelated. Nothing was lost — the claim ids `C006` / `C007` / `S045` still anchor the evidence. |
| **Retained on disk, not published** | `.agents/`, `docs/kiro/prompts/`, `docs/kiro/operational-excellence/`, `docs/kiro/slack-financial-pillar-response-design.md`, `docs/plans/nizam-transaction-capture-pipeline-research-annex.md`, `scripts/kiro/assembleSlackFinance.mjs`, `scripts/kiro/researchSlackFinance.mjs` and its test | Inputs to the work, not the released product. Nothing is deleted, nothing is moved, and the released design cites their claims by claim id rather than by publisher. |

**This is not the prohibited local exclude.** D-H bans an exclude used *instead of* deciding. Here the
decision is substantive: these artifacts are inputs, and the repository's own genericity rule forbids
publishing their vocabulary. The reasoning is written into `.gitignore` beside the entries, so the next
reader finds the decision at the point of enforcement rather than having to come here for it.

**Consequence to carry into CI (P6).** The suite currently counts tests in files that are present on this
machine but no longer tracked. A clean checkout will therefore see **fewer** tests than `AC04`'s floor
demands. That must be settled when CI is built — by scoping the floor to tracked tests, not by lowering it.
