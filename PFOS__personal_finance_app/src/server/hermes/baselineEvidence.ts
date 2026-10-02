/**
 * Agentic Profile baseline evidence assessment, not runtime authorization.
 * Owning contract: Contract 05 addendum 05_AGENTIC_PROFILE_BASELINE.md.
 * Phase 0: offline baseline reconciliation, AB01-AB06.
 * Depends on: existing Zod; no I/O, clock reads or production runtime hooks.
 */
import { z } from 'zod';

const checks = z.enum(['code', 'runtime', 'persistence', 'schedule', 'mirror']);
const capabilityId = z.enum([
  'ingress', 'journal', 'retrieval', 'capacity', 'scheduler', 'calendar', 'recovery', 'finance',
]);
const environment = z.enum(['WORKSPACE', 'CORE_SNAPSHOT', 'VPS']);
const hash = z.string().regex(/^[a-f0-9]{64}$/u);
const reference = z.string().min(1).max(128).regex(/^[a-zA-Z0-9][a-zA-Z0-9:_-]*$/u);
const instant = z.string().refine((value) => {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/u.test(value)) return false;
  const time = Date.parse(value);
  return Number.isFinite(time) && new Date(time).toISOString() === (value.length === 20 ? value.slice(0, -1) + '.000Z' : value);
}, 'Invalid UTC instant');

export type BaselineCapability = z.infer<typeof capabilityId>;
type Check = z.infer<typeof checks>;
const requirements: Readonly<Record<BaselineCapability, readonly Check[]>> = Object.freeze({
  ingress: Object.freeze(['code', 'runtime'] as const),
  journal: Object.freeze(['code', 'persistence'] as const),
  retrieval: Object.freeze(['code', 'runtime'] as const),
  capacity: Object.freeze(['code', 'runtime'] as const),
  scheduler: Object.freeze(['code', 'schedule'] as const),
  calendar: Object.freeze(['code', 'runtime'] as const),
  recovery: Object.freeze(['code', 'mirror'] as const),
  finance: Object.freeze(['code', 'runtime'] as const),
});
const FRESHNESS_MS = 24 * 60 * 60 * 1000;

const receipt = z.object({
  id: reference,
  basis: z.enum(['OBSERVED', 'USER_REPORTED', 'HISTORICAL']),
  outcome: z.enum(['PASS', 'FAIL', 'UNKNOWN']),
  environment,
  snapshotHash: hash.nullable(),
  check: checks,
  observedAt: instant.nullable(),
  sourceRef: reference,
}).strict().refine((value) => value.basis !== 'OBSERVED' || (value.snapshotHash !== null && value.observedAt !== null), {
  message: 'Observed evidence requires a snapshot',
});
const capability = z.object({
  id: capabilityId,
  environment,
  snapshotHash: hash.nullable(),
  receipts: z.array(receipt).max(100),
}).strict();

export const baselineManifestSchema = z.object({
  schemaVersion: z.literal('1.0.0'),
  recordedAt: instant,
  capabilities: z.array(capability).length(8),
}).strict().superRefine((manifest, context) => {
  const ids = new Set(manifest.capabilities.map((item) => item.id));
  const receiptIds = new Set<string>();
  if (ids.size !== 8) context.addIssue({ code: 'custom', message: 'Duplicate or missing capability' });
  for (const item of manifest.capabilities) {
    for (const evidence of item.receipts) {
      if (receiptIds.has(evidence.id)) context.addIssue({ code: 'custom', message: 'Duplicate receipt' });
      receiptIds.add(evidence.id);
      if (!requirements[item.id].includes(evidence.check)) {
        context.addIssue({ code: 'custom', message: 'Unsupported capability check' });
      }
      if (evidence.observedAt !== null && Date.parse(evidence.observedAt) > Date.parse(manifest.recordedAt)) {
        context.addIssue({ code: 'custom', message: 'Receipt postdates manifest' });
      }
    }
  }
});
export type BaselineManifest = z.infer<typeof baselineManifestSchema>;
type Capability = z.infer<typeof capability>;
export type BaselineState = 'CURRENT' | 'PARTIAL' | 'REPORTED' | 'HISTORICAL' | 'UNKNOWN';
export type BaselineBlocker =
  | 'BASELINE_UNKNOWN' | 'MISSING_CHECK' | 'UNOBSERVED_EVIDENCE' | 'STALE_EVIDENCE'
  | 'BASELINE_MISMATCH' | 'ENVIRONMENT_MISMATCH' | 'CHECK_FAILED'
  | 'CONFLICTING_EVIDENCE' | 'CHECK_UNKNOWN';

export interface CapabilityAssessment {
  readonly id: BaselineCapability;
  readonly state: BaselineState;
  readonly requiredChecks: readonly Check[];
  readonly blockers: readonly BaselineBlocker[];
  readonly evidenceRefs: readonly string[];
}
export interface BaselineAssessment {
  readonly assessedAt: string;
  readonly allCurrent: boolean;
  readonly authorizesExecution: false;
  readonly capabilities: readonly CapabilityAssessment[];
}

function assessCapability(item: Capability, nowMs: number): CapabilityAssessment {
  const blockers = new Set<BaselineBlocker>();
  if (item.snapshotHash === null) blockers.add('BASELINE_UNKNOWN');
  for (const check of requirements[item.id]) {
    const candidates = item.receipts.filter((entry) => entry.check === check);
    if (candidates.length === 0) blockers.add('MISSING_CHECK');
    const observed = candidates.filter((entry) => entry.basis === 'OBSERVED' && entry.observedAt !== null);
    if (candidates.length > 0 && observed.length === 0) blockers.add('UNOBSERVED_EVIDENCE');
    const matching = observed.filter((entry) =>
      entry.environment === item.environment && entry.snapshotHash === item.snapshotHash);
    const fresh = matching.filter((entry) => entry.observedAt !== null && nowMs - Date.parse(entry.observedAt) < FRESHNESS_MS);
    const passed = fresh.some((entry) => entry.outcome === 'PASS');
    const failed = fresh.some((entry) => entry.outcome === 'FAIL');
    if (failed) blockers.add(passed ? 'CONFLICTING_EVIDENCE' : 'CHECK_FAILED');
    if (!passed) {
      if (observed.some((entry) => entry.environment !== item.environment)) blockers.add('ENVIRONMENT_MISMATCH');
      if (observed.some((entry) => entry.snapshotHash !== item.snapshotHash)) blockers.add('BASELINE_MISMATCH');
      if (matching.length > fresh.length) blockers.add('STALE_EVIDENCE');
      if (fresh.some((entry) => entry.outcome === 'UNKNOWN')) blockers.add('CHECK_UNKNOWN');
    }
  }
  const bases = new Set(item.receipts.map((entry) => entry.basis));
  const state: BaselineState = blockers.size === 0 ? 'CURRENT'
    : bases.has('OBSERVED') ? 'PARTIAL'
      : bases.has('USER_REPORTED') ? 'REPORTED'
        : bases.has('HISTORICAL') ? 'HISTORICAL' : 'UNKNOWN';
  return Object.freeze({
    id: item.id, state,
    requiredChecks: requirements[item.id],
    blockers: Object.freeze([...blockers].sort()),
    evidenceRefs: Object.freeze(item.receipts.map((entry) => entry.sourceRef)),
  });
}

/** Supplied evidence is untrusted; consistency is checked, origin is not authenticated. */
export function assessBaseline(input: unknown, now: string): BaselineAssessment {
  const clock = instant.safeParse(now);
  const parsed = baselineManifestSchema.safeParse(input);
  if (!clock.success || !parsed.success) throw new Error('BASELINE_INPUT_INVALID');
  const nowMs = Date.parse(clock.data);
  if (Date.parse(parsed.data.recordedAt) > nowMs) throw new Error('BASELINE_INPUT_INVALID');
  const capabilities = parsed.data.capabilities.map((item) => assessCapability(item, nowMs));
  return Object.freeze({
    assessedAt: clock.data,
    allCurrent: capabilities.every((item) => item.state === 'CURRENT'),
    authorizesExecution: false,
    capabilities: Object.freeze(capabilities),
  });
}
