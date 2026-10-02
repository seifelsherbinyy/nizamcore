// @vitest-environment node
/**
 * Owning contract: Contract 05 addendum 05_AGENTIC_PROFILE_BASELINE.md.
 * Phase 0: AB01-AB06 independent evidence and real CLI acceptance tests.
 * Synthetic fixtures only; no host, credentials, network or runtime probes.
 */
import { afterAll, describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { assessBaseline, type BaselineManifest } from './baselineEvidence.ts';

const NOW = '2026-09-11T12:00:00.000Z';
const HASH = 'a'.repeat(64);
// Intentionally independent of the implementation's requirements table (AB02).
const REQUIRED = [
  ['ingress', ['code', 'runtime']],
  ['journal', ['code', 'persistence']],
  ['retrieval', ['code', 'runtime']],
  ['capacity', ['code', 'runtime']],
  ['scheduler', ['code', 'schedule']],
  ['calendar', ['code', 'runtime']],
  ['recovery', ['code', 'mirror']],
  ['finance', ['code', 'runtime']],
] as const;

function currentManifest(now = NOW): BaselineManifest {
  return {
    schemaVersion: '1.0.0', recordedAt: now,
    capabilities: REQUIRED.map(([id, checks]) => ({
      id, environment: 'VPS', snapshotHash: HASH,
      receipts: checks.map((check) => ({
        id: `${id}-${check}`, basis: 'OBSERVED', outcome: 'PASS',
        environment: 'VPS', snapshotHash: HASH, check,
        observedAt: now, sourceRef: `synthetic-${id}-${check}`,
      })),
    })),
  };
}

function first(manifest: BaselineManifest) { return manifest.capabilities[0]!; }
function evidence(manifest: BaselineManifest) { return first(manifest).receipts[0]!; }
function result(manifest: BaselineManifest, now = NOW) {
  return assessBaseline(manifest, now).capabilities[0]!;
}

// Unknown input, not a cast that bypasses the production parser.
const malformed: [string, (manifest: BaselineManifest) => unknown][] = [
  ['unsupported version', (m) => ({ ...m, schemaVersion: '2.0.0' })],
  ['unknown top-level field', (m) => ({ ...m, rawText: 'synthetic-private-marker' })],
  ['unknown capability field', (m) => { Object.assign(first(m), { requiredChecks: [] }); return m; }],
  ['unknown receipt field', (m) => { Object.assign(evidence(m), { payload: 'synthetic-private-marker' }); return m; }],
  ['unknown capability', (m) => { Object.assign(first(m), { id: 'other' }); return m; }],
  ['missing capability', (m) => { m.capabilities.pop(); return m; }],
  ['duplicate capability', (m) => { m.capabilities[1] = first(m); return m; }],
  ['duplicate receipt across capabilities', (m) => { m.capabilities[1]!.receipts[0]!.id = evidence(m).id; return m; }],
  ['unsupported check', (m) => { evidence(m).check = 'mirror'; return m; }],
  ['unknown basis', (m) => { Object.assign(evidence(m), { basis: 'TRUSTED' }); return m; }],
  ['unknown outcome', (m) => { Object.assign(evidence(m), { outcome: 'SUCCESS' }); return m; }],
  ['unknown environment', (m) => { Object.assign(first(m), { environment: 'OTHER' }); return m; }],
  ['uppercase hash', (m) => { first(m).snapshotHash = HASH.toUpperCase(); return m; }],
  ['short receipt hash', (m) => { evidence(m).snapshotHash = 'abc'; return m; }],
  ['observed null hash', (m) => { evidence(m).snapshotHash = null; return m; }],
  ['observed null timestamp', (m) => { evidence(m).observedAt = null; return m; }],
  ['empty reference', (m) => { evidence(m).sourceRef = ''; return m; }],
  ['long reference', (m) => { evidence(m).sourceRef = 'a'.repeat(129); return m; }],
  ['raw reference', (m) => { evidence(m).sourceRef = 'raw synthetic text'; return m; }],
  ['receipt after manifest', (m) => { evidence(m).observedAt = '2026-09-11T12:00:00.001Z'; return m; }],
  ['excess receipts', (m) => { first(m).receipts = Array.from({ length: 101 }, (_, i) => ({ ...evidence(m), id: `synthetic-${i}` })); return m; }],
];

describe('AB01 closed manifest and clock refusal', () => {
  it.each(malformed)('rejects %s without echoing payload', (_name, mutate) => {
    expect(() => assessBaseline(mutate(currentManifest()), NOW)).toThrow(/^BASELINE_INPUT_INVALID$/u);
  });
  it.each([null, [], {}, 'synthetic-private-marker'])('rejects nonmanifest %j', (input) => {
    expect(() => assessBaseline(input, NOW)).toThrow('BASELINE_INPUT_INVALID');
  });
  it.each([
    '2026-02-30T00:00:00Z', '2025-02-29T00:00:00Z', '2026-13-01T00:00:00Z',
    '2026-09-11T24:00:00Z', '2026-09-11', '2026-09-11T12:00:00+00:00',
    '2026-09-11T12:00:00.12Z', 'not-a-date',
  ])('rejects invalid or noncanonical instant %s', (instant) => {
    const manifest = currentManifest();
    manifest.recordedAt = instant;
    expect(() => assessBaseline(manifest, NOW)).toThrow('BASELINE_INPUT_INVALID');
    expect(() => assessBaseline(currentManifest(), instant)).toThrow('BASELINE_INPUT_INVALID');
    const invalidReceipt = currentManifest();
    evidence(invalidReceipt).observedAt = instant;
    expect(() => assessBaseline(invalidReceipt, NOW)).toThrow('BASELINE_INPUT_INVALID');
  });
  it('rejects a future manifest', () => {
    expect(() => assessBaseline(currentManifest(), '2026-09-11T11:59:59Z')).toThrow('BASELINE_INPUT_INVALID');
  });
  it.each(['2024-02-29T00:00:00Z', '2026-09-11T12:00:00Z', NOW])('accepts valid UTC %s', (instant) => {
    expect(assessBaseline(currentManifest(instant), instant).allCurrent).toBe(true);
  });
});

describe('AB02 independent literal requirements', () => {
  it.each(REQUIRED)('requires every %s check', (id, required) => {
    const report = assessBaseline(currentManifest(), NOW);
    expect(report.capabilities.find((c) => c.id === id)?.requiredChecks).toEqual(required);
    for (const check of required) {
      const manifest = currentManifest();
      const capability = manifest.capabilities.find((c) => c.id === id)!;
      capability.receipts = capability.receipts.filter((r) => r.check !== check);
      const missing = assessBaseline(manifest, NOW);
      expect(missing.allCurrent).toBe(false);
      expect(missing.capabilities.find((c) => c.id === id)?.blockers).toEqual(['MISSING_CHECK']);
    }
  });
});

describe('AB03-AB04 evidence qualification and disagreement', () => {
  it('reports all-current without granting execution authority', () => {
    const report = assessBaseline(currentManifest(), NOW);
    expect(report.allCurrent).toBe(true);
    expect(report.authorizesExecution).toBe(false);
    expect(report.capabilities).toHaveLength(8);
    expect(report.capabilities.every((c) => c.state === 'CURRENT' && c.blockers.length === 0)).toBe(true);
  });
  it.each(['USER_REPORTED', 'HISTORICAL'] as const)('does not promote %s PASS or FAIL', (basis) => {
    const manifest = currentManifest();
    for (const receipt of first(manifest).receipts) { receipt.basis = basis; receipt.observedAt = null; receipt.snapshotHash = null; }
    expect(result(manifest).state).toBe(basis === 'USER_REPORTED' ? 'REPORTED' : 'HISTORICAL');
    expect(result(manifest).blockers).toEqual(['UNOBSERVED_EVIDENCE']);
    first(manifest).receipts.push({ ...evidence(manifest), id: 'synthetic-failure', outcome: 'FAIL' });
    expect(result(manifest).blockers).not.toContain('CHECK_FAILED');
  });
  it('reports missing baseline and empty evidence as unknown, not absence', () => {
    const manifest = currentManifest();
    first(manifest).snapshotHash = null;
    first(manifest).receipts = [];
    expect(result(manifest)).toMatchObject({ state: 'UNKNOWN', blockers: ['BASELINE_UNKNOWN', 'MISSING_CHECK'] });
  });
  it('cannot fill a null target hash from receipts', () => {
    const manifest = currentManifest(); first(manifest).snapshotHash = null;
    expect(result(manifest).blockers).toEqual(['BASELINE_MISMATCH', 'BASELINE_UNKNOWN']);
  });
  it.each(['WORKSPACE', 'CORE_SNAPSHOT'] as const)('rejects %s evidence for VPS', (environment) => {
    const manifest = currentManifest(); evidence(manifest).environment = environment;
    expect(result(manifest)).toMatchObject({ state: 'PARTIAL', blockers: ['ENVIRONMENT_MISMATCH'] });
  });
  it('requires an exact snapshot match', () => {
    const manifest = currentManifest(); evidence(manifest).snapshotHash = 'b'.repeat(64);
    expect(result(manifest).blockers).toEqual(['BASELINE_MISMATCH']);
  });
  it.each([
    ['2026-09-10T12:00:00.001Z', []],
    ['2026-09-10T12:00:00.000Z', ['STALE_EVIDENCE']],
    ['2026-09-10T11:59:59.999Z', ['STALE_EVIDENCE']],
  ])('pins the 24-hour inclusive expiry at %s', (observedAt, blockers) => {
    const manifest = currentManifest(); evidence(manifest).observedAt = observedAt as string;
    expect(result(manifest).blockers).toEqual(blockers);
  });
  it('reevaluates the same manifest at a later injected clock', () => {
    expect(assessBaseline(currentManifest(), '2026-09-12T12:00:00Z').allCurrent).toBe(false);
  });
  it.each([['FAIL', 'CHECK_FAILED'], ['UNKNOWN', 'CHECK_UNKNOWN']] as const)('blocks observed %s', (outcome, blocker) => {
    const manifest = currentManifest(); evidence(manifest).outcome = outcome;
    expect(result(manifest).blockers).toEqual([blocker]);
  });
  it('preserves fresh pass/fail conflict regardless of receipt order or newer pass', () => {
    const manifest = currentManifest();
    first(manifest).receipts.push({ ...evidence(manifest), id: 'synthetic-failure', outcome: 'FAIL', observedAt: '2026-09-11T11:00:00Z' });
    expect(result(manifest).blockers).toEqual(['CONFLICTING_EVIDENCE']);
    first(manifest).receipts.reverse();
    expect(result(manifest).blockers).toEqual(['CONFLICTING_EVIDENCE']);
  });
  it('does not let old, mismatched or unobserved failures veto matching current passes', () => {
    const manifest = currentManifest();
    const failed = { ...evidence(manifest), outcome: 'FAIL' as const };
    first(manifest).receipts.push(
      { ...failed, id: 'old', observedAt: '2026-09-10T12:00:00Z' },
      { ...failed, id: 'other-snapshot', snapshotHash: 'b'.repeat(64) },
      { ...failed, id: 'other-environment', environment: 'WORKSPACE' },
      { ...failed, id: 'reported', basis: 'USER_REPORTED' },
      { ...failed, id: 'historical', basis: 'HISTORICAL' },
    );
    expect(result(manifest).state).toBe('CURRENT');
  });
  it('is deterministic, does not mutate input, and freezes its output', () => {
    const manifest = currentManifest();
    const before = JSON.stringify(manifest);
    const report = assessBaseline(manifest, NOW);
    expect(assessBaseline(manifest, NOW)).toEqual(report);
    expect(JSON.stringify(manifest)).toBe(before);
    expect([report, report.capabilities, ...report.capabilities.flatMap((c) => [c, c.blockers, c.requiredChecks, c.evidenceRefs])].every(Object.isFrozen)).toBe(true);
  });
});

describe('AB05-AB06 repository manifest and real Node CLI', () => {
  const tempRoot = join(homedir(), '.aki', 'tmp');
  mkdirSync(tempRoot, { recursive: true });
  const directory = mkdtempSync(join(tempRoot, 'nizam-baseline-test-'));
  afterAll(() => rmSync(directory, { recursive: true, force: true }));
  const cli = resolve('scripts/inspect/agentic-baseline.mjs');
  function run(args: string[] = []) {
    return spawnSync(process.execPath, [cli, ...args], { cwd: directory, encoding: 'utf8', timeout: 10000 });
  }
  function input(contents: string): string {
    const file = join(directory, 'synthetic-input.json'); writeFileSync(file, contents); return file;
  }
  it('wires the package command to the tested CLI', () => {
    const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
    expect(pkg.scripts['inspect:agentic-baseline']).toBe('node scripts/inspect/agentic-baseline.mjs');
  });
  it('repository manifest makes no current attestation or invented hash', () => {
    const manifest = JSON.parse(readFileSync('docs/architecture/agentic-profile-baseline.json', 'utf8')) as BaselineManifest;
    expect(assessBaseline(manifest, NOW).allCurrent).toBe(false);
    for (const capability of manifest.capabilities) {
      expect(capability.snapshotHash).toBeNull();
      for (const receipt of capability.receipts) {
        expect(receipt.basis).not.toBe('OBSERVED');
        expect(receipt.outcome).toBe('UNKNOWN');
        expect(receipt.snapshotHash).toBeNull();
        expect(receipt.observedAt).toBeNull();
      }
    }
  });
  it('default manifest works outside repository cwd and returns incomplete exit 2', () => {
    const child = run();
    expect(child.error).toBeUndefined(); expect(child.status).toBe(2); expect(child.stderr).toBe('');
    const report = JSON.parse(child.stdout);
    expect(report.allCurrent).toBe(false); expect(report.authorizesExecution).toBe(false);
    expect(report.capabilities).toHaveLength(8);
    expect(Object.keys(report).sort()).toEqual(['allCurrent', 'assessedAt', 'authorizesExecution', 'capabilities']);
    expect(Object.keys(report.capabilities[0]).sort()).toEqual(['blockers', 'evidenceRefs', 'id', 'requiredChecks', 'state']);
  });
  it('returns exit 0 for synthetic current evidence, never execution authority', () => {
    const child = run([input(JSON.stringify(currentManifest(new Date().toISOString())))]);
    expect(child.status).toBe(0); expect(child.stderr).toBe('');
    expect(JSON.parse(child.stdout)).toMatchObject({ allCurrent: true, authorizesExecution: false });
  });
  it.each(['{synthetic-private-marker', JSON.stringify({ secret: 'synthetic-private-marker' })])('refuses malformed input without echoing it', (contents) => {
    const child = run([input(contents)]);
    expect(child.status).toBe(1); expect(child.stdout).toBe(''); expect(child.stderr.trim()).toBe('BASELINE_INPUT_INVALID');
  });
  it('refuses nonexistent files and extra arguments generically', () => {
    for (const args of [[join(directory, 'missing.json')], ['synthetic-private-marker', 'extra']]) {
      const child = run(args);
      expect(child.status).toBe(1); expect(child.stdout).toBe(''); expect(child.stderr.trim()).toBe('BASELINE_INPUT_INVALID');
    }
  });
});
