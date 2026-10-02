/**
 * NIZAM · S1/S2 discovery consumer — spec transaction-capture-pipeline, increment 3
 * Implemented by: PFOS Contract 06 / Phase 2.4 (evidence and discovery; design §B/S1–S2)
 * Depends on: ./sourceRegistry.ts, ./channels/fileChannel.ts, the source-event and document-index
 *             repositories (CONSUMED, never modified), and injected ports for every impure edge.
 *
 * ## This is a CONSUMER, not a clock
 *
 * `src/server/process/scheduler.ts` is the single clock: storeless, payload-free per tick, re-reads its
 * kill sentinel every tick, bounded retry `{1000ms, 15000ms, 3 attempts}`, never crashes on a failed
 * tick. It stays UNMODIFIED, and `SCHEDULER_TARGETS` stays the two-member tuple `['life', 'finance']` —
 * a third member is a compile error and a test in this increment asserts it still is.
 *
 * So discovery is a function the existing `finance` tick invokes. It takes its ports, does one pass, and
 * answers a report. It owns no timer, no interval, no process and no port of its own.
 *
 * ## Capture durability and parse success are INDEPENDENT
 *
 * `runDiscovery` appends evidence and stops. It does not parse, and it does not care whether anything
 * later can. An unparseable payload still lands, because the bytes are the owner's and a future parser
 * may read what this one cannot — which is exactly why `source_events` retains `raw_payload` and why
 * `parse_state` starts at `pending` rather than being decided here.
 *
 * ## The three outcomes, and why the third is not a choice this layer may make
 *
 *   APPENDED          new key, row created.
 *   ALREADY_PRESENT   same key, same bytes. A no-op. `appended: false`.
 *   EVIDENCE_CONFLICT same key, DIFFERENT bytes.
 *
 * The third is neither a duplicate nor new: the upstream artifact changed under a key that claimed to
 * identify it. The stored row is left EXACTLY as it was and the disagreement is reported. Silently
 * preferring the stored version loses a correction; silently preferring the new one rewrites history.
 * Both are decisions about the owner's data that this layer has no standing to make, so it makes neither.
 *
 * ## One channel's failure costs no other channel its tick
 *
 * Each channel is attempted inside its own try. A channel that raises produces a typed failure entry for
 * that tick and the pass continues. Nothing here retries: the scheduler's bounded policy already owns
 * retry, and a second backoff nested inside the first would multiply the budget rather than share it.
 */
import type {
  DocumentIndexRepository,
} from '../db/repositories/documentIndexRepository.ts';
import type {
  SourceEventsRepository,
} from '../db/repositories/sourceEventsRepository.ts';
import { buildFileSourceEvent, type DiscoveredFile } from './channels/fileChannel.ts';
import { descriptorFor } from './sourceRegistry.ts';

/** Why a capture did not simply append. Never carries the payload. */
export const DISCOVERY_REFUSAL_CODES = [
  /** Same key, different bytes. The stored row is untouched. */
  'EVIDENCE_CONFLICT',
  /** The channel is not in `CHANNEL_DESCRIPTORS`. Fail closed rather than invent a descriptor. */
  'CHANNEL_UNKNOWN',
  /** The channel's own lister raised. Bounded to this tick. */
  'CHANNEL_UNAVAILABLE',
  /**
   * The payload cannot be stored byte-identically, so it is refused rather than truncated.
   *
   * Found by the increment-3 test suite, not predicted: `source_events.raw_payload` is a `TEXT` column
   * in a STRICT table, and SQLite terminates a TEXT value at the first NUL byte. A payload containing
   * `\u0000` therefore round-trips as the empty string — silently, with the insert reporting success.
   *
   * That directly breaks this layer's one promise, that the retained bytes are the bytes that arrived.
   * Storing the column as a BLOB would fix it and would be a MIGRATION, which is not authorized
   * (Contract 6 §3 I3.1–I3.5 is DRAFT). So the invariant is held the other way: if the bytes cannot be
   * retained faithfully, the capture is REFUSED and nothing is written. A refusal the owner can see beats
   * a success that quietly kept nothing.
   */
  'PAYLOAD_NOT_STORABLE',
] as const;
export type DiscoveryRefusalCode = (typeof DISCOVERY_REFUSAL_CODES)[number];

export type CaptureOutcome =
  | { readonly kind: 'appended'; readonly sourceEventId: string }
  | { readonly kind: 'already_present'; readonly sourceEventId: string }
  | {
    readonly kind: 'refused';
    readonly code: DiscoveryRefusalCode;
    /** Present when a row exists to point at. Never the bytes. */
    readonly sourceEventId?: string;
  };

export interface DiscoveryPorts {
  readonly events: SourceEventsRepository;
  readonly documents: DocumentIndexRepository;
}

/**
 * Capture one already-read file as evidence.
 *
 * Appends to `source_events` first, then records the `document_index` pointer. That order matters: the
 * evidence is the record and the pointer is the index of it, so a crash between them leaves evidence
 * without an index (recoverable, and the next pass re-indexes it because `indexDocument` is
 * conflict-ignoring) rather than an index pointing at evidence that does not exist.
 */
export function captureFile(file: DiscoveredFile, ports: DiscoveryPorts): CaptureOutcome {
  return captureEvent(buildFileSourceEvent(file), ports);
}

/**
 * Capture an already-built event. The shared S2 path for EVERY channel.
 *
 * Exposed because the two key strategies produce genuinely different conflict behaviour, and the
 * difference is worth stating rather than discovering:
 *
 *   `ref_and_digest` (files) — the digest is IN the key, so changed bytes produce a DIFFERENT key. A
 *      corrected statement re-uploaded under the same filename is therefore a NEW ARTIFACT, not a
 *      conflict. `EVIDENCE_CONFLICT` is unreachable for this strategy, by construction.
 *
 *   `date_and_sequence` (chat) — the key is independent of content, so the same owner-local date and
 *      sequence CAN legitimately arrive with different bytes. That is the real conflict case, and it is
 *      why this code path exists at all.
 *
 * A reader who only saw `captureFile` would reasonably conclude the conflict branch was dead code. It is
 * not; it belongs to the other strategy.
 */
export function captureEvent(
  event: {
    readonly id: string;
    readonly channel: string;
    readonly idempotencyKey: string;
    readonly contentHash: string;
    readonly rawPayload: string | null;
    readonly documentRef: string;
    readonly byteCount: number;
    readonly documentClass: string;
  },
  ports: DiscoveryPorts,
): CaptureOutcome {
  if (descriptorFor(event.channel) === null) {
    return Object.freeze({ kind: 'refused' as const, code: 'CHANNEL_UNKNOWN' as const });
  }

  // Refuse rather than truncate. See PAYLOAD_NOT_STORABLE above for why this is a refusal and not a
  // sanitisation: removing the NUL would store bytes the owner never sent, under a hash of bytes that
  // were never stored, which is worse than declining.
  if (event.rawPayload !== null && event.rawPayload.includes('\u0000')) {
    return Object.freeze({ kind: 'refused' as const, code: 'PAYLOAD_NOT_STORABLE' as const });
  }

  const result = ports.events.append({
    id: event.id,
    channel: event.channel,
    idempotencyKey: event.idempotencyKey,
    contentHash: event.contentHash,
    rawPayload: event.rawPayload,
    documentRef: event.documentRef,
  });

  // The same key naming different bytes. Report it; change nothing.
  if (!result.contentHashMatches) {
    return Object.freeze({
      kind: 'refused' as const,
      code: 'EVIDENCE_CONFLICT' as const,
      sourceEventId: result.row.id,
    });
  }

  // The pointer. Conflict-ignoring on content hash, so re-running is a no-op here too.
  ports.documents.indexDocument({
    id: `doc_${event.id.slice('sev_'.length)}`,
    documentRef: event.documentRef,
    contentHash: event.contentHash,
    byteCount: event.byteCount,
    documentClass: event.documentClass,
    sourceEventId: result.row.id,
  });

  return Object.freeze(
    result.appended
      ? { kind: 'appended' as const, sourceEventId: result.row.id }
      : { kind: 'already_present' as const, sourceEventId: result.row.id },
  );
}

/** One channel's lister. Impure by nature, so it is injected and mocked deterministically (D-B(c)). */
export interface ChannelLister {
  readonly channel: string;
  /** Answers the artifacts currently visible. May raise; the caller bounds that to one tick. */
  list(): readonly DiscoveredFile[];
}

export interface DiscoveryReport {
  readonly appended: number;
  readonly alreadyPresent: number;
  readonly refusals: readonly { readonly channel: string; readonly code: DiscoveryRefusalCode }[];
  /** Channels attempted this pass, in order. A halted deployment attempts none. */
  readonly channelsAttempted: readonly string[];
}

export interface DiscoveryDeps extends DiscoveryPorts {
  readonly listers: readonly ChannelLister[];
  /**
   * The halt check, injected. Discovery discovers NOTHING when halted — and the caller still writes
   * liveness, because being halted is a state to report, not a reason to look dead.
   */
  readonly halted: () => boolean;
}

/**
 * One discovery pass. Answers a report; never throws.
 *
 * Reports COUNTS and CODES. No amount, no payee, no account and no payload reaches the report, because a
 * report is what a caller writes into a log or an artifact.
 */
export function runDiscovery(deps: DiscoveryDeps): DiscoveryReport {
  if (deps.halted()) {
    return Object.freeze({
      appended: 0,
      alreadyPresent: 0,
      refusals: Object.freeze([]),
      channelsAttempted: Object.freeze([]),
    });
  }

  let appended = 0;
  let alreadyPresent = 0;
  const refusals: { channel: string; code: DiscoveryRefusalCode }[] = [];
  const channelsAttempted: string[] = [];

  for (const lister of deps.listers) {
    channelsAttempted.push(lister.channel);

    let files: readonly DiscoveredFile[];
    try {
      files = lister.list();
    } catch {
      // Bounded to this tick. No retry here: the scheduler already owns the retry budget.
      refusals.push({ channel: lister.channel, code: 'CHANNEL_UNAVAILABLE' });
      continue;
    }

    for (const file of files) {
      try {
        const outcome = captureFile(file, deps);
        if (outcome.kind === 'appended') appended += 1;
        else if (outcome.kind === 'already_present') alreadyPresent += 1;
        else refusals.push({ channel: lister.channel, code: outcome.code });
      } catch {
        refusals.push({ channel: lister.channel, code: 'CHANNEL_UNAVAILABLE' });
      }
    }
  }

  return Object.freeze({
    appended,
    alreadyPresent,
    refusals: Object.freeze(refusals),
    channelsAttempted: Object.freeze(channelsAttempted),
  });
}
