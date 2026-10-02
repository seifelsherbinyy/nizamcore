/**
 * NIZAM · S1 channel registry — spec transaction-capture-pipeline, increment 3
 * Implemented by: PFOS Contract 06 / Phase 2.4 (evidence and discovery; design §B/S1)
 * Depends on: nothing. Pure data plus two lookups. No I/O, no clock, no repository.
 *
 * ## What a channel descriptor is, and what it deliberately cannot say
 *
 * A descriptor says WHERE evidence comes from and HOW its identity is formed. It says nothing about how
 * the evidence is interpreted, because interpretation is S3 and later. In particular a descriptor has no
 * field for a parser, a currency, a default account or a money unit — those are not omissions to be
 * filled in later, they are the boundary. Per ADR-0003 D7-C an edge relay forwards bytes and a content
 * hash, nothing more.
 *
 * ## Why `retainsRawPayload` is per channel rather than always true
 *
 * `source_events.raw_payload` is the most sensitive column in the store, and the tier-1 seed load already
 * declines to populate it: its payload would be the owner's ledger rows, the store already holds them
 * parsed, and a second copy in a text column is a second place they can leak from. A chat reply is the
 * opposite case — the bytes ARE the only record, so losing them loses the evidence. So the decision is a
 * property of the channel, declared here once, rather than a judgement made at each call site.
 *
 * ## Why the checkpoint is `document_index` and NOT a new `kv` table
 *
 * Discovery needs to know what it has already seen. The obvious shape is a key-value checkpoint, and
 * there is **no `kv` table in this schema** — the tables are `accounts`, `source_events`, `transactions`,
 * `transaction_links`, `obligations`, `statements`, `decisions`, `assets`, `valuations`, `fx_rates`,
 * `spend_ledger`, `model_telemetry`, `update_dedup`, `work_queue`, `document_index` and `audit_log`.
 * Adding one would be a migration, and **no migration is authorized** (Contract 6 §3 I3.1–I3.5 is DRAFT).
 *
 * It is not needed. `document_index` already IS the discovery pointer table: its `content_hash` is
 * UNIQUE, `indexDocument` is a conflict-ignoring insert, it carries `source_event_id`, and its own header
 * states the reason a retired pointer is tombstoned rather than deleted — *"a deleted pointer would make
 * the same document look new and be indexed again"*. That is the checkpoint requirement, already built.
 *
 * And correctness does not depend on the checkpoint at all: S2's idempotency is structural, so
 * re-discovering the same artifact is a no-op regardless. The pointer makes discovery CHEAPER, never
 * more correct — which is the right way round, because a checkpoint that correctness depended on would
 * be a second source of truth about what has been ingested.
 */

import { CAPTURE_CHANNEL } from './dailyCapture.ts';

/** How a channel's idempotency key is formed. Declared, never inferred from the payload. */
export const KEY_STRATEGIES = [
  /** The artifact's own stable reference — a file path plus its content digest. */
  'ref_and_digest',
  /** An owner-local date plus a within-day sequence. Used by the chat channel. */
  'date_and_sequence',
] as const;
export type KeyStrategy = (typeof KEY_STRATEGIES)[number];

export interface ChannelDescriptor {
  /** The `source_events.channel` value. Stable forever: it is half of the idempotency key. */
  readonly channel: string;
  /** How identity is formed for this channel. */
  readonly keyStrategy: KeyStrategy;
  /**
   * Whether the verbatim bytes are retained in `source_events.raw_payload`.
   * False does NOT mean the evidence is discarded — it means the parsed record is the retained form.
   */
  readonly retainsRawPayload: boolean;
  /** `document_index.document_class` for this channel's pointer rows. */
  readonly documentClass: string;
  /**
   * True when this channel may only ever produce CANDIDATES, never canonical rows.
   * Contract 6 §5 I5.2: Telegram, SMS and email may only produce candidates in a staging collection
   * distinct from `transactions[]`. Declared here so the restriction is data rather than a remembered
   * rule, and so increment 6 can refuse a promotion the channel was never allowed to originate.
   */
  readonly candidateOnly: boolean;
}

/** The channel every canonical-ledger row is keyed under. Mirrors `seedLoad.CANONICAL_LEDGER_CHANNEL`. */
export const CANONICAL_LEDGER_CHANNEL = 'ledger:canonical';
/** A statement or ledger FILE the owner supplied. Authoritative intake per Contract 6 §5 I5.1. */
export const FILE_CHANNEL = 'file:statement';

/**
 * The conversational daily capture. Candidate-only per I5.2.
 *
 * IMPORTED rather than declared, and that is the point. This registry originally spelled the channel
 * `'chat:daily-capture'` while `dailyCapture.ts` had been writing `'owner_daily_capture'` since Contract
 * 15 — two names for one channel. Because `captureEvent` refuses an unregistered channel, the effect
 * would have been that the chat channel could never capture at all: every reply refused as
 * `CHANNEL_UNKNOWN`. The defect was invisible until increment 4 tried to wire the two together.
 *
 * The channel string is half of `UNIQUE (channel, idempotency_key)`, so it is an identity, not a label —
 * a second spelling is a second identity space, and rows written under one are invisible to the other.
 * There is therefore exactly ONE declaration of it, in the module that has been using it, and this
 * registry reads that.
 */
export { CAPTURE_CHANNEL as CHAT_CAPTURE_CHANNEL } from './dailyCapture.ts';

/**
 * Every channel this tier knows. A frozen tuple rather than a mutable map, so a channel cannot be
 * registered at runtime by a module that happens to be loaded — the set is a read, not a side effect.
 */
export const CHANNEL_DESCRIPTORS: readonly ChannelDescriptor[] = Object.freeze([
  Object.freeze({
    channel: CANONICAL_LEDGER_CHANNEL,
    keyStrategy: 'ref_and_digest' as const,
    // The tier-1 seed load's reason, preserved: the payload would be the owner's ledger rows.
    retainsRawPayload: false,
    documentClass: 'ledger-export',
    candidateOnly: false,
  }),
  Object.freeze({
    channel: FILE_CHANNEL,
    keyStrategy: 'ref_and_digest' as const,
    retainsRawPayload: true,
    documentClass: 'statement-file',
    candidateOnly: false,
  }),
  Object.freeze({
    channel: CAPTURE_CHANNEL,
    keyStrategy: 'date_and_sequence' as const,
    // The bytes ARE the only record of a chat reply. Losing them loses the evidence.
    retainsRawPayload: true,
    documentClass: 'chat-capture',
    candidateOnly: true,
  }),
]);

/** Look up a descriptor. Returns null rather than throwing, so a caller must handle the unknown case. */
export function descriptorFor(channel: string): ChannelDescriptor | null {
  return CHANNEL_DESCRIPTORS.find((d) => d.channel === channel) ?? null;
}

/** True when the channel is registered. */
export function isKnownChannel(channel: string): boolean {
  return descriptorFor(channel) !== null;
}

/**
 * True when this channel may only produce candidates.
 *
 * An UNKNOWN channel answers `true` — fail closed. A channel nobody registered is the last thing that
 * should be trusted to originate canonical financial truth.
 */
export function isCandidateOnly(channel: string): boolean {
  return descriptorFor(channel)?.candidateOnly ?? true;
}
