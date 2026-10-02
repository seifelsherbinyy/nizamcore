/**
 * NIZAM · Shared record identity and the two dedup keys — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S7 and §C.1)
 * Depends on: node:crypto only. No repository, no clock, no counter, no I/O.
 *
 * ## Why this module exists rather than a fifth idempotency mechanism
 *
 * Four independent idempotency mechanisms already run in this codebase: the DDL's unique
 * `(channel, idempotency_key)` on `source_events`, `enqueueWork`'s conflict-ignoring insert,
 * `updateDedupRepo.claimDelivery` where the insert IS the decision, and the content-derived ids in
 * `seedLoad.ts`. This module adds NONE. It LIFTS the fourth out of `seedLoad.ts` so that every channel
 * derives identity the same way, and lifts the content fingerprint out of `dailyCapture.ts` for the same
 * reason. Both were already correct; they were merely private to one caller.
 *
 * ## The two dedup layers, which are different questions and must not be collapsed
 *
 *  LAYER 1 — RAW EVIDENCE IDEMPOTENCY (S2). "Did this exact source artifact already arrive?"
 *    Keyed on `(channel, idempotencyKey)`, where the key is supplied by the channel adapter and the
 *    bytes are hashed by `rawPayloadDigest`. Catches a redelivered SMS or a re-uploaded file. Cheap,
 *    exact, and it must run BEFORE any parsing — v1.3 FINAL §27.6 J2 orders it that way, and the SMS
 *    corpus shows it fires at roughly 3 in 254.
 *
 *  LAYER 2 — NORMALIZED RECORD FINGERPRINT (S7). "Do two DIFFERENT source artifacts describe the same
 *    economic event?" Keyed on the financially consequential fields AFTER normalization, which is why
 *    it cannot run before S4: it reads `normalizedPayee`.
 *
 * A raw duplicate caught at layer 1 never reaches layer 2. A layer-2 collision is SURFACED, never
 * auto-deleted, because a same-day same-amount same-payee repeat is legitimate (two coffees).
 *
 * ## What is deliberately excluded from the fingerprint
 *
 * `memo` and `categoryId` are NOT hashed (Contract 15 §7.1). Both are owner-editable after the fact, so
 * including them would let an annotation change a record's identity and resurrect a duplicate.
 */
import { createHash } from 'node:crypto';

/** Direction of a movement. Structurally identical to `CaptureDirection` and `LedgerDirection`. */
export type IngestDirection = 'in' | 'out';

/** Field separator inside an identity pre-image. A NUL cannot occur in any of the joined values. */
const FIELD_SEP = '\u0000';
/** Separator for the wide ledger-row hash, distinct so the two pre-images can never coincide. */
const ROW_SEP = '\u0001';

function sha256(text: string): string {
  return createHash('sha256').update(text, 'utf8').digest('hex');
}

/**
 * A stable account id, so a second run resolves to the same row rather than creating a second.
 * Lifted verbatim from `seedLoad.ts`; the pre-image and the 24-character truncation are unchanged, so
 * ids already in the store still resolve.
 */
export function accountIdFor(account: { readonly name: string; readonly last4: string }): string {
  return `acct_${sha256(`${account.name}${FIELD_SEP}${account.last4}`).slice(0, 24)}`;
}

/**
 * A stable transaction identity. Content-derived, so re-running collides instead of appending.
 *
 * Lifted from `seedLoad.ts`, with the channel promoted from a module constant to a parameter — that is
 * the ONLY change. Called with the same channel it produces the same id, byte for byte, which is what
 * makes this a lift rather than a rewrite.
 */
export function transactionIdFor(channel: string, duplicateKey: string): string {
  return `txn_${sha256(`${channel}${FIELD_SEP}${duplicateKey}`).slice(0, 32)}`;
}

/** The source-event identity for the same pair. Same pre-image, different prefix. */
export function sourceEventIdFor(channel: string, duplicateKey: string): string {
  return `sev_${sha256(`${channel}${FIELD_SEP}${duplicateKey}`).slice(0, 32)}`;
}

/** A period key. The grain the statements table is unique on. */
export function periodKeyOf(accountId: string, statementMonth: string): string {
  return `stmt_${sha256(`${accountId}${FIELD_SEP}${statementMonth}`).slice(0, 24)}`;
}

/**
 * LAYER 1. A digest of the bytes exactly as they arrived.
 *
 * Takes the raw payload with NO trimming, re-casing or re-wrapping, because the bytes are the owner's
 * evidence and a future parser may read what this one cannot. Two deliveries that differ by a single
 * byte produce different digests, which is what lets S2 report `EVIDENCE_CONFLICT` rather than silently
 * keeping one of them.
 */
export function rawPayloadDigest(rawPayload: string): string {
  return sha256(rawPayload);
}

/**
 * LAYER 2. Deterministic fingerprint over the financially consequential fields ONLY.
 *
 * Lifted from `dailyCapture.captureContentHash` with the field order, the separator and the hash all
 * unchanged, so a fingerprint computed here equals one computed there for the same input.
 *
 * The MAGNITUDE is hashed rather than the signed amount, with `direction` carried as its own field, so
 * `out 5` and `in 5` hash differently by construction rather than by a sign convention someone has to
 * remember.
 */
export function contentFingerprint(fields: {
  readonly date: string;
  readonly direction: IngestDirection;
  /** Integer milliunits, non-negative. Rendered as an integer; no decimal form enters the pre-image. */
  readonly magnitude: number;
  readonly currency: string;
  readonly accountId: string;
  readonly normalizedPayee: string;
}): string {
  const canonical = [
    fields.date,
    fields.direction,
    String(fields.magnitude),
    fields.currency,
    fields.accountId,
    fields.normalizedPayee,
  ].join(FIELD_SEP);
  return sha256(canonical);
}

/**
 * The wide row hash used to detect that an upstream row CHANGED under an unchanged idempotency key.
 *
 * Distinct from `contentFingerprint` in both purpose and pre-image: the fingerprint asks "is this the
 * same economic event", this asks "did the source's own bytes for this row change". A different answer
 * here is the disagreement `source_events` reports rather than absorbs.
 */
export function rowContentHash(parts: readonly (string | number | boolean | null | undefined)[]): string {
  return sha256(parts.map((p) => (p === null || p === undefined ? '' : String(p))).join(ROW_SEP));
}
