/**
 * Channel-aware memory provenance and reply binding, with no transport or writer effects.
 * Owning authority: PFOS Contract 14 section 12; Contracts 06/12. Phase 14.2.
 * Spec: dual-channel-memory CM01-CM03. Only trusted provider adapters supply metadata.
 */
import { createHash } from 'node:crypto';
import { z } from 'zod';

export const CHANNEL_MEMORY_VERSION = 'dual-channel-memory-v1' as const;
const reference = z.string().min(1).max(200).regex(/^[A-Za-z0-9._:-]+$/);
const platform = z.enum(['telegram', 'slack']);
const profile = z.enum(['nizam', 'pfos']);
const conversationType = z.enum(['private', 'channel']);
const bindingSchema = z.object({
  platform, account: reference, sender: reference, conversation: reference, conversationType,
}).strict().refine(value => value.platform !== 'telegram' || value.conversationType === 'private');
const policySchema = z.object({
  version: z.literal(CHANNEL_MEMORY_VERSION), ownerRef: reference, profile,
  bindings: z.array(bindingSchema).min(1).max(20),
}).strict();
const originSchema = z.object({
  platform, account: reference, sender: reference, conversation: reference, conversationType,
  thread: reference.nullable(), event: reference, isBot: z.literal(false),
  occurredAt: z.string().datetime(),
}).strict().refine(value => value.platform !== 'telegram' ||
  (value.conversationType === 'private' && value.thread === null));
export type ChannelOrigin = z.infer<typeof originSchema>;
export type ChannelMemoryPolicy = z.infer<typeof policySchema>;
export interface PreparedChannelMemory {
  readonly provenance: {
    readonly version: typeof CHANNEL_MEMORY_VERSION;
    readonly platform: ChannelOrigin['platform'];
    readonly profile: ChannelMemoryPolicy['profile'];
    readonly direction: 'inbound' | 'outbound';
    readonly occurredAt: string;
    readonly conversationRef: string;
    readonly recordId: string;
    readonly sourceRef: string;
  };
  /** Only this object reaches model context, subject to native context/privacy policy. */
  readonly modelContext: {
    readonly respondingVia: ChannelOrigin['platform'];
    readonly conversationRef: string;
  };
  /** Protected transport only. Never pass this binding to a model or Drive metadata. */
  readonly replyBinding: {
    readonly platform: ChannelOrigin['platform'];
    readonly account: string;
    readonly conversation: string;
    readonly thread: string | null;
  };
}
function digest(parts: readonly (string | null)[]): string {
  return createHash('sha256').update(JSON.stringify(parts), 'utf8').digest('hex');
}

/** No caller-supplied "authenticated" flag: provider signature/session validation precedes this API. */
export function prepareChannelMemory(rawPolicy: unknown, rawOrigin: unknown,
  direction: 'inbound' | 'outbound'): PreparedChannelMemory {
  const policyResult = policySchema.safeParse(rawPolicy);
  const originResult = originSchema.safeParse(rawOrigin);
  if (!policyResult.success || !originResult.success || !['inbound', 'outbound'].includes(direction)) {
    throw new Error('CHANNEL_MEMORY_REFUSED');
  }
  const policy = policyResult.data;
  const origin = originResult.data;
  const matches = policy.bindings.filter(binding => binding.platform === origin.platform &&
    binding.account === origin.account && binding.sender === origin.sender &&
    binding.conversation === origin.conversation && binding.conversationType === origin.conversationType);
  if (matches.length !== 1) throw new Error('CHANNEL_MEMORY_REFUSED');
  const session = [CHANNEL_MEMORY_VERSION, policy.ownerRef, policy.profile, origin.platform,
    origin.account, origin.conversation, origin.thread];
  const conversationRef = 'conversation-' + digest(session);
  const recordId = 'memory-' + digest([...session, origin.event, direction]);
  const sourceRef = origin.platform + ':' + recordId;
  return Object.freeze({
    provenance: Object.freeze({ version: CHANNEL_MEMORY_VERSION, platform: origin.platform,
      profile: policy.profile, direction, occurredAt: origin.occurredAt, conversationRef, recordId, sourceRef }),
    modelContext: Object.freeze({ respondingVia: origin.platform, conversationRef }),
    replyBinding: Object.freeze({ platform: origin.platform, account: origin.account,
      conversation: origin.conversation, thread: origin.thread }),
  });
}
