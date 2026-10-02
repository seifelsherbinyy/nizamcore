# Plan: scheduled daily findings digest, Drive as source of truth

Status: DRAFT PLAN ONLY. Nothing below has been implemented. No native VPS
file, service, cron entry, credential, or G1-G8 gate has been touched.
Scope: native `nizamcore` (a sibling system to this finance-app repo), governed
by `.kiro/steering/two-agent-vps.md`. This repo has read-only VPS access; any
implementation step needs an explicit write-access grant and owner review.

## What the owner asked for
A scheduled (daily) job that assesses the latest findings, evaluates them, and
sends the owner an assessment/summary -- treating Google Drive-held data as
the real source of truth the assessment is checked against.

## What already exists on the VPS (confirmed by read-only inspection)
- **Governor scheduler**: 4 Cairo-gated cron slots/day (`refresh_1000`,
  `volatile_1140`, `primary_1200`, `reconcile_1300`), DST-safe dual-UTC-slot +
  once-per-Cairo-day guard. Contract-owned: comment cites
  `NIZAM-DAILY-ORCHESTRATION-04` (file not yet located -- see Gap 0).
- **YAWMIYAT daily journal cron**: one Cairo-gated slot (14:30) runs
  `tools/journal_daily.sh` -> `tools/journal_enrich.py` -> `yawmiyat.py`.
  Comment: "Daily YAWMIYAT enrichment + Drive reconcile. Enrichment is
  idempotent; drives are safe to retry."
- **`tools/g3_proof.py`**: a proven, runnable (on synthetic data only) chain
  matching almost exactly what was asked for: raw/session -> WHOOP enrichment
  -> Assessment -> Evaluation -> Analysis -> longitudinal/index update ->
  reconcile, using the same helpers the scheduler already calls.
- **`tools/g5_proof.py`**: a proven, runnable (on synthetic data only) full
  Drive round trip: capture -> canonical commit -> local SHA read-back ->
  HIMAYAH egress gate -> real `nizam_drive.py` upsert -> Drive read-back SHA
  match -> retrieval/index lookup -> THABAT ledger append. Its own docstring
  states raw-journal Drive egress is **paused by default (G1 conditional)**
  and this proof explicitly flips the flag on for its synthetic session only,
  then restores it -- it never touches the real journal.
- **Separate BADAN health system** (`/opt/personal-health`) has its own
  `reconcile.sh` (6-hourly) and `daily-ingest.sh` (Cairo-gated) -- a second,
  independent scheduled pipeline for WHOOP data, feeding the same
  assessment chain g3_proof exercises.

## What is missing or gated (the actual gaps)
1. **Contract not located.** The cron comment names an owning contract
   (`NIZAM-DAILY-ORCHESTRATION-04`) but a file search under
   `nizamcore/contracts` for it found nothing. Per NIZAM rule, no policy
   (what counts as a "finding," what Drive content is authoritative for
   what, what may be sent to the owner) should be implemented without a
   located or authored governing contract. **This blocks Phase 0 below.**
2. **Live capture writes metadata only, not content.** Confirmed this
   session: a live Telegram/Hermes turn appends only an `EVENT_LEDGER` row
   (trace_id, target, confidence, booleans, char counts) via
   `ledger_writer.append`. The raw text never reaches `journal_persistence.py`
   or `yawmiyat.py`. So today's "latest findings" have very little real
   content to assess -- the daily YAWMIYAT job is enriching whatever gets
   captured through some other route (manual entry?), not the live bot path.
3. **Drive raw-journal egress is a paused human gate (G1).** g5_proof's own
   docstring says so. I will not flip this flag; only the owner can decide
   to un-pause G1. Until then, "Google Drive as real source of truth" can
   only mean whatever is *already* synced under the existing
   `strict_local_drive -> drive_nizam_journals` allow-list, not full raw
   journal content.
4. **No proactive owner-notification channel found.** Grepped
   `tools/` and `governor/` for a send-to-owner / digest-push primitive:
   none exists. The only Telegram path found (`webhook.py`/`poller.py`) is
   reactive -- it replies to an inbound message, it does not originate one.
   A daily push needs either: (a) a new outbound call using whatever Telegram
   bot token/credential already authorizes the reactive path (reuse, no new
   credential), or (b) some other channel the owner prefers.

## Proposed phased plan (none of this is authorized to start yet)

**Phase 0 -- contract.** Ask the owner where `NIZAM-DAILY-ORCHESTRATION-04`
(or its successor) lives, or authorize drafting a new contract/spec that
pins down: what a "finding" is, which store is authoritative for which data
(Drive vs local ledger vs Dexie cache), what may leave the device in a daily
message (HIMAYAH classification rules already exist and should be reused,
not re-invented), and the send channel. This must exist before any of the
following phases writes policy code.

**Phase 1 -- close the capture gap.** Wire live-turn raw text into a durable
writer (reuse `yawmiyat.py`, the one with real production callers -- not the
orphaned `journal_persistence.py`, unless the contract says otherwise) so
the daily enrichment job has real content to assess, not just ledger
metadata. Bounded, tested, reviewed before merge.

**Phase 2 -- promote the assessment chain from proof to schedule.** Take
`g3_proof.py`'s already-proven stage order (enrichment -> Assessment ->
Evaluation -> Analysis -> index update -> reconcile) and run it against real
data on its own Cairo-gated cron slot, same idempotency/run-record pattern as
the existing governor blocks. Output: a dated assessment artifact + run
record, not yet sent anywhere.

**Phase 3 -- Drive reconciliation (gated, owner decision required).** Only
if/when the owner explicitly un-pauses G1: wire the already-proven
`g5_proof.py` round trip for real sessions, so Drive genuinely becomes the
synced source of truth rather than an unused capability. Until that
decision, Phase 2's assessment treats local storage as authoritative and
says so in its own output (no silent assumption of Drive parity).

**Phase 4 -- the daily message to the owner.** Compose a short, BLUF-style
digest (latest findings, what changed since yesterday, any gaps/anomalies
like the metadata-only capture gap found this session) and send it once
Phase 2 (and, if authorized, Phase 3) completes each day, over whichever
channel Phase 0's contract designates.

**Phase 5 -- verification.** Dry-run every phase against synthetic data first
(same discipline as g3_proof/g5_proof: never touch the real journal during
testing), then one owner-observed live run, before it runs unattended.

## Explicit non-negotiables carried into every phase
- No G1-G8 gate is flipped by me. Phase 3 does not start without the owner's
  explicit word.
- No credential is minted, rotated, or newly requested; any Telegram send
  reuses the existing authorized bot path if one is confirmed to exist.
- No native VPS file, cron entry, or service is edited without a write-access
  grant and an explicit go-ahead, separate from this plan being written.
- Money rules, `drive.file`-only scope, and synthetic-fixture-only testing
  discipline apply throughout; none of this plan changes those.

## Immediate open question for the owner
Point me to the `NIZAM-DAILY-ORCHESTRATION-04` contract file (or confirm none
exists) so Phase 0 can close, and confirm whether you want write access to
`nizamcore` requested next, or want Phase 1 scoped in more detail first.
