/**
 * NIZAM · S1 file channel adapter — spec transaction-capture-pipeline, increment 3
 * Implemented by: PFOS Contract 06 / Phase 2.4 (evidence and discovery; design §B/S1)
 * Depends on: ../recordIdentity.ts, ../sourceRegistry.ts. Pure. No filesystem access here.
 *
 * ## An adapter forwards bytes. That is the whole contract.
 *
 * ADR-0003 D7-C: an edge relay forwards bytes and a content hash, nothing more. So this module computes
 * an identity and a digest and hands both on. It does NOT parse an amount, choose a currency, infer a
 * direction, resolve an account, split a row or decide what a malformed line probably meant. A
 * source-level test over this whole directory asserts the absence, because the absence is the property —
 * an adapter that computed a figure would be a contract violation that still passed every unit test of
 * its own behaviour.
 *
 * Reading the file is the CALLER's job. This module takes bytes that were already read, so it stays pure
 * and its tests need no filesystem. The impure edge lives in the discovery consumer, behind a port.
 *
 * ## Why the digest is over the bytes and the key is over the reference plus the digest
 *
 * Two different questions. The DIGEST answers "are these the same bytes" — it is what makes a re-upload
 * of an unchanged file a no-op. The KEY answers "is this the same artifact" — it pairs the owner's own
 * reference with the digest, so the same file supplied twice under one name is one artifact, while a file
 * whose CONTENT changed under the same name produces a different key and is therefore a new artifact
 * rather than a silent overwrite.
 *
 * That second case is the one worth being careful about: if the key were the reference ALONE, a corrected
 * statement re-uploaded under the same filename would collide with the original and be reported as an
 * `EVIDENCE_CONFLICT` — technically true but unhelpful, because it is not a conflict, it is a new
 * version. Including the digest in the key makes it a new artifact, which is what it is.
 */
import { rawPayloadDigest } from '../recordIdentity.ts';
import { FILE_CHANNEL, descriptorFor } from '../sourceRegistry.ts';
import { sourceEventIdFor } from '../recordIdentity.ts';

/** A file the owner supplied, already read into memory by the caller. */
export interface DiscoveredFile {
  /**
   * The owner's own reference for the artifact. A path, a Drive alias, a picker handle.
   * NEVER a literal in tracked source — it is resolved from the runtime environment.
   */
  readonly documentRef: string;
  /** The bytes, verbatim, exactly as read. Not trimmed, not re-cased, not re-wrapped. */
  readonly rawBytes: string;
}

/**
 * The append this adapter proposes, shaped exactly like `SourceEventAppend` so the repository takes it
 * unchanged, plus the two pointer fields `document_index` needs.
 *
 * Structurally identical to what `buildCapturedSourceEvent` produces for the chat channel, which is the
 * point: S2 does not care which channel an artifact came from.
 */
export interface FileSourceEvent {
  readonly id: string;
  readonly channel: string;
  readonly idempotencyKey: string;
  readonly contentHash: string;
  /** Present only when the channel descriptor retains it. `null` is a decision, not an omission. */
  readonly rawPayload: string | null;
  readonly documentRef: string;
  /** For the `document_index` pointer row. */
  readonly byteCount: number;
  readonly documentClass: string;
}

/**
 * Build the S1/S2 append for a supplied file.
 *
 * Computes: a digest of the bytes, an identity from the reference plus that digest, and the event id.
 * Computes nothing else. There is no branch in this function that inspects the CONTENT of `rawBytes`
 * beyond hashing it and measuring its length.
 */
export function buildFileSourceEvent(file: DiscoveredFile): FileSourceEvent {
  const descriptor = descriptorFor(FILE_CHANNEL);
  // Unreachable while FILE_CHANNEL is registered; asserted rather than assumed so a registry edit that
  // removed it fails loudly here instead of silently producing an unclassified pointer.
  if (descriptor === null) {
    throw new Error('NIZAM ingest: the file channel is not registered in CHANNEL_DESCRIPTORS');
  }

  const contentHash = rawPayloadDigest(file.rawBytes);
  const idempotencyKey = `${file.documentRef}\u0000${contentHash}`;

  return Object.freeze({
    id: sourceEventIdFor(FILE_CHANNEL, idempotencyKey),
    channel: FILE_CHANNEL,
    idempotencyKey,
    contentHash,
    rawPayload: descriptor.retainsRawPayload ? file.rawBytes : null,
    documentRef: file.documentRef,
    // Byte length of the UTF-8 encoding, not the JS string length, so a multi-byte payload is measured
    // as the store will hold it.
    byteCount: Buffer.byteLength(file.rawBytes, 'utf8'),
    documentClass: descriptor.documentClass,
  });
}
