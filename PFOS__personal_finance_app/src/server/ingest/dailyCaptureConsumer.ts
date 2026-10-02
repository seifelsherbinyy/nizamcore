/**
 * NIZAM · S3 for the chat channel — spec transaction-capture-pipeline, increment 4
 * Implemented by: PFOS Contract 15 / Phase 2.5 (wire daily capture; Contract 06 §5 I5.2 staging)
 * Depends on: ./dailyCapture.ts (CONSUMED, never modified), ./discovery.ts, ./sourceRegistry.ts,
 *             and the source-event repository through an injected port.
 *
 * ## This is a WORKER BRANCH, not a Hermes tool
 *
 * Nothing here is registered in `HERMES_TOOL_NAMES`, which stays at ten. This module is not reachable
 * across the tool boundary at all, and that is deliberate rather than incidental: `runtimeAdapter`'s
 * `AUTHORITY_KEY` pattern refuses any payload or result key matching `amount|balance|currency|milliunit|
 * money|price|...`, so a capture result — which is *made of* those fields — is **unrepresentable** across
 * that boundary. A tool that returned candidates could not pass its own validator.
 *
 * So the shape is: the scheduler's existing `finance` tick invokes this; a model may phrase a question the
 * owner reads; the owner's reply arrives as bytes; and the deterministic parser in `dailyCapture.ts` turns
 * bytes into candidates or refusals. **A model never composes an amount, a currency, a sign or an
 * account.** That is Contract 6 §5 I5.5, and it is enforced here by the model never being on the path.
 *
 * ## The three legs, and why they are separate functions
 *
 *   PROMPT  `promptFor` — the ask. Byte-identical for a given owner-local date, carries no digit.
 *   APPEND  `ingestReply` leg 1 — the reply becomes S2 evidence BEFORE anything tries to parse it.
 *   PARSE   `ingestReply` leg 2 — S3, deterministic, over bytes already durable.
 *
 * The append happens first and its success does not depend on the parse. An unparseable reply is still
 * the owner's evidence: it is stored, its `parse_state` moves to `rejected`, and a future grammar may read
 * what this one could not. That independence is Contract 15 §9.1 criterion 3's whole point, and it is why
 * these are two legs of one call rather than one fused step.
 *
 * ## A typed refusal is permanent; only transport retries
 *
 * A malformed line does not become well formed on a second attempt, so no refusal here is retried. What a
 * refusal earns is ONE fixed clarifying question — composed by `clarifyingQuestionFor`, not by a model —
 * and the owner's answer re-enters as a NEW reply at a NEW sequence, appended as NEW evidence. It never
 * patches the stored row, because the stored row is what actually arrived.
 */
import {
  CAPTURE_CHANNEL,
  buildCapturedSourceEvent,
  clarifyingQuestionFor,
  composeDailyCapturePrompt,
  parseDailyCaptureReply,
  type CaptureContext,
  type CaptureRefusal,
  type DailyCapturePrompt,
} from './dailyCapture.ts';
import { captureEvent, type CaptureOutcome, type DiscoveryPorts } from './discovery.ts';
import { descriptorFor } from './sourceRegistry.ts';
import type { TransactionCandidate } from '../../lib/db/schema.ts';

/** The ask. A thin pass-through, so there is exactly one prompt composer in the system. */
export function promptFor(ownerLocalDate: string): DailyCapturePrompt {
  return composeDailyCapturePrompt(ownerLocalDate);
}

/** One refusal, paired with the fixed question it earns. */
export interface RefusalWithQuestion {
  readonly refusal: CaptureRefusal;
  /** Fixed text from `clarifyingQuestionFor`. A model may relay it; it never authors it. */
  readonly question: string;
}

export interface IngestReplyResult {
  /** What S2 did with the bytes. Independent of everything below it. */
  readonly evidence: CaptureOutcome;
  /**
   * Candidates, never canonical rows. Contract 6 §5 I5.2: the chat channel may only produce candidates,
   * and a candidate is not financial truth. Promotion is increment 6 and is an explicit owner act.
   */
  readonly candidates: readonly TransactionCandidate[];
  readonly refusals: readonly RefusalWithQuestion[];
  /** True only when the whole reply was exactly the declination token. */
  readonly declined: boolean;
  /** False when the evidence leg refused, in which case no parse was attempted. */
  readonly parsed: boolean;
}

export interface IngestReplyInput {
  readonly ownerLocalDate: string;
  /** 1-based, within the owner-local day. Part of the idempotency key. */
  readonly sequence: number;
  /** The reply, verbatim. Not trimmed, not re-cased. */
  readonly reply: string;
  /**
   * Alias and currency resolution input, supplied per call. Never a stored registry.
   *
   * `sourceEventRef` is deliberately OMITTED from what the caller may supply. It is the provenance anchor
   * naming the `source_events` row this reply was captured as, and this module DERIVES it from the append
   * result below. A caller-supplied anchor could name a row other than the one the bytes actually landed
   * in, which is a provenance lie the type system can prevent — so it does.
   */
  readonly context: Omit<CaptureContext, 'sourceEventRef'>;
}

/**
 * Ingest one reply: append it as evidence, then parse it.
 *
 * Returns a result; never throws for a refusal. A THROW from this function means the store itself is
 * unavailable, which is a transient failure the scheduler's existing bounded retry owns — not something
 * to swallow into a refusal, because a refusal means "these bytes are wrong" and a store outage does not.
 */
export function ingestReply(input: IngestReplyInput, ports: DiscoveryPorts): IngestReplyResult {
  const built = buildCapturedSourceEvent({
    ownerLocalDate: input.ownerLocalDate,
    sequence: input.sequence,
    reply: input.reply,
  });

  const descriptor = descriptorFor(CAPTURE_CHANNEL);
  if (descriptor === null) {
    throw new Error('NIZAM ingest: the daily capture channel is not registered in CHANNEL_DESCRIPTORS');
  }

  // LEG 1 — S2. The bytes become durable evidence before anything interprets them.
  const evidence = captureEvent(
    {
      id: built.id,
      channel: built.channel,
      idempotencyKey: built.idempotencyKey,
      contentHash: built.contentHash,
      rawPayload: built.rawPayload,
      documentRef: `capture/${input.ownerLocalDate}/${String(input.sequence)}`,
      byteCount: Buffer.byteLength(built.rawPayload, 'utf8'),
      documentClass: descriptor.documentClass,
    },
    ports,
  );

  // A refused append means nothing durable exists to parse. Parsing anyway would produce candidates with
  // no evidence row behind them — exactly the orphan S8's record identity cannot repair.
  if (evidence.kind === 'refused') {
    return Object.freeze({
      evidence,
      candidates: Object.freeze([]),
      refusals: Object.freeze([]),
      declined: false,
      parsed: false,
    });
  }

  // LEG 2 — S3. Deterministic, over bytes that are already safe.
  // The provenance anchor is the row the bytes actually landed in, taken from the append result rather
  // than from the caller, so a candidate can never cite an evidence row it did not come from.
  const parse = parseDailyCaptureReply(input.reply, {
    ...input.context,
    sourceEventRef: evidence.sourceEventId,
  });

  const refusals = parse.refusals.map((refusal) =>
    Object.freeze({ refusal, question: clarifyingQuestionFor(refusal) }),
  );

  // The parse verdict is recorded on the evidence row. `rejected` does NOT mean the bytes were discarded;
  // it means this grammar could not read them. The payload stays exactly where it is.
  const nextState = parse.refusals.length > 0 && parse.candidates.length === 0 ? 'rejected' : 'parsed';
  ports.events.setParseState(evidence.sourceEventId, nextState);

  return Object.freeze({
    evidence,
    candidates: parse.candidates,
    refusals: Object.freeze(refusals),
    declined: parse.declined,
    parsed: true,
  });
}
