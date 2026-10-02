/**
 * Independent canonical/replica receipt assessment, not storage or cryptographic verification.
 * Owning authority: PFOS Contract 14 section 12; Contracts 06/12. Phase 14.2.
 * Spec: dual-channel-memory CM04-CM05. Evidence must originate in trusted native adapters.
 */
import { z } from 'zod';
const ref = z.string().min(1).max(200);
const hash = z.string().regex(/^[0-9a-f]{64}$/);
const sourceSchema = z.object({ recordId: ref, version: z.number().int().positive().safe(), contentHash: hash }).strict();
const canonicalSchema = sourceSchema.extend({ contentStored: z.literal(true) }).strict();
const mirrorSchema = z.object({
  source: sourceSchema, remoteRef: ref, destinationVersion: ref, ciphertextHash: hash,
  scope: z.literal('drive.file'), encrypted: z.literal(true), privacyApproved: z.literal(true),
}).strict();
export type MemorySource = z.infer<typeof sourceSchema>;
export interface MemoryStatus {
  readonly vps: 'not_verified' | 'saved';
  readonly drive: 'unavailable' | 'pending' | 'synced';
}
function sameSource(a: MemorySource, b: MemorySource): boolean {
  return a.recordId === b.recordId && a.version === b.version && a.contentHash === b.contentHash;
}

/** Separate inputs represent actual write and independent read-back, never an LLM assertion. */
export function assessMemoryReceipts(expected: unknown, canonicalWrite: unknown, canonicalReadBack: unknown,
  mirrorWrite: unknown, mirrorReadBack: unknown): MemoryStatus {
  const source = sourceSchema.safeParse(expected);
  const written = canonicalSchema.safeParse(canonicalWrite);
  const read = canonicalSchema.safeParse(canonicalReadBack);
  const saved = source.success && written.success && read.success &&
    sameSource(source.data, written.data) && sameSource(source.data, read.data);
  if (!saved) return { vps: 'not_verified', drive: 'unavailable' };
  if (mirrorWrite === null && mirrorReadBack === null) return { vps: 'saved', drive: 'unavailable' };
  const mirror = mirrorSchema.safeParse(mirrorWrite);
  const remote = mirrorSchema.safeParse(mirrorReadBack);
  if (!mirror.success || !remote.success || !sameSource(source.data, mirror.data.source) ||
    !sameSource(source.data, remote.data.source)) return { vps: 'saved', drive: 'pending' };
  const synced = mirror.data.remoteRef === remote.data.remoteRef &&
    mirror.data.destinationVersion === remote.data.destinationVersion &&
    mirror.data.ciphertextHash === remote.data.ciphertextHash;
  return { vps: 'saved', drive: synced ? 'synced' : 'pending' };
}
