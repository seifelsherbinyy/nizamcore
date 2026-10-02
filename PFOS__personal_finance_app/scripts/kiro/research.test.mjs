/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 2 (KDE03/05/07). */
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, symlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, dirname } from 'node:path';
import { spawnSync } from 'node:child_process';
import { AUTHORITY, ROOT } from './validate.mjs';
import { RESEARCH_PATH, validateResearch, validateResearchWorkspace } from './research.mjs';

function fixture() {
  return { schemaVersion: 1, authority: AUTHORITY, phase: 'RESEARCH2', sources: [{
    id: 'S001', repository: 'synthetic/tool', kind: 'readme',
    url: 'https://github.com/synthetic/tool/blob/main/README.md',
    retrievedAt: '2026-09-16T00:00:00.000Z', sha256: 'a'.repeat(64),
    excerpt: 'Synthetic source, no upstream execution.', locator: 'line 1',
  }], candidates: [{ repository: 'synthetic/tool', domains: 'ABCDEFGHIJKLMNOPQ'.split(''),
    depth: 'ASSESSED', disposition: 'PATTERN_ONLY', sources: ['S001'],
    nativeAlternative: 'Existing local tools', reason: 'No runtime integration needed',
    nextAction: 'Keep existing tooling', execution: 'NOT_RUN', kiroActivation: 'NOT_TESTED',
  }] };
}
function temporaryRoot() {
  const base = join(homedir(), '.aki', 'tmp'); mkdirSync(base, { recursive: true });
  return mkdtempSync(join(base, 'kde-research-test-'));
}
function writeFixture(value) {
  const root = temporaryRoot(); const file = join(root, RESEARCH_PATH);
  mkdirSync(dirname(file), { recursive: true }); writeFileSync(file, value);
  return root;
}

test('valid synthetic research is structurally consistent', () => assert.deepEqual(validateResearch(fixture()), []));
test('actual research artifact validates without promoting execution', () => {
  assert.deepEqual(validateResearchWorkspace(), []);
  const data = JSON.parse(readFileSync(join(ROOT, RESEARCH_PATH), 'utf8'));
  assert.equal(data.candidates.length, 99);
  assert.ok(data.candidates.every((row) => row.execution === 'NOT_RUN' && row.kiroActivation === 'NOT_TESTED'));
});
for (const value of [null, [], {}, { ...fixture(), schemaVersion: 2 }, { ...fixture(), phase: 'KDE1' },
  { ...fixture(), approved: true }, { ...fixture(), authority: 'other' }, { ...fixture(), sources: [] },
  { ...fixture(), candidates: [] }, { ...fixture(), candidates: Array(151).fill({}) },
  { ...fixture(), sources: Array(501).fill({}) }]) {
  test(`top-level malformed input ${JSON.stringify(value).slice(0, 70)}`, () => {
    assert.deepEqual(validateResearch(value), ['RESEARCH_SCHEMA']);
  });
}
for (const [label, mutate, expected] of [
  ['duplicate source', (v) => v.sources.push({ ...v.sources[0] }), 'DUPLICATE_SOURCE'],
  ['duplicate repository case', (v) => v.candidates.push({ ...v.candidates[0], repository: 'Synthetic/Tool' }), 'DUPLICATE_CANDIDATE'],
  ['unknown source field', (v) => { v.sources[0].approved = true; }, 'SOURCE_SCHEMA'],
  ['null source', (v) => { v.sources[0] = null; }, 'SOURCE_SCHEMA'],
  ['unknown candidate field', (v) => { v.candidates[0].approved = true; }, 'CANDIDATE_SCHEMA'],
  ['null candidate', (v) => { v.candidates[0] = null; }, 'CANDIDATE_SCHEMA'],
  ['missing domain', (v) => v.candidates[0].domains.pop(), 'DOMAIN_COVERAGE'],
  ['unknown domain', (v) => v.candidates[0].domains.push('Z'), 'CANDIDATE_SCHEMA'],
  ['duplicate domain', (v) => { v.candidates[0].domains[0] = 'B'; }, 'CANDIDATE_SCHEMA'],
  ['dangling citation', (v) => { v.candidates[0].sources = ['S999']; }, 'CITATION_INVALID'],
  ['cross-repository citation', (v) => { v.candidates[0].repository = 'synthetic/other'; }, 'CITATION_INVALID'],
  ['duplicate citation', (v) => v.candidates[0].sources.push('S001'), 'CANDIDATE_SCHEMA'],
  ['empty evidence', (v) => { v.candidates[0].sources = []; }, 'CANDIDATE_SCHEMA'],
  ['orphan evidence', (v) => v.sources.push({ ...v.sources[0], id: 'S002' }), 'ORPHAN_SOURCE'],
  ['invented execution', (v) => { v.candidates[0].execution = 'PASS'; }, 'CANDIDATE_SCHEMA'],
  ['invented activation', (v) => { v.candidates[0].kiroActivation = 'VERIFIED'; }, 'CANDIDATE_SCHEMA'],
  ['invented depth', (v) => { v.candidates[0].depth = 'AUDITED'; }, 'CANDIDATE_SCHEMA'],
  ['unknown disposition', (v) => { v.candidates[0].disposition = 'INSTALL_NOW'; }, 'CANDIDATE_SCHEMA'],
  ['unresolved promotion', (v) => { v.candidates[0].depth = 'UNRESOLVED'; }, 'CANDIDATE_SCHEMA'],
  ['empty native alternative', (v) => { v.candidates[0].nativeAlternative = ' '; }, 'CANDIDATE_SCHEMA'],
  ['oversized reason', (v) => { v.candidates[0].reason = 'x'.repeat(2001); }, 'CANDIDATE_SCHEMA'],
  ['missing next action', (v) => { delete v.candidates[0].nextAction; }, 'CANDIDATE_SCHEMA'],
  ['malformed candidate identity', (v) => { v.candidates[0].repository = '../tool'; }, 'CANDIDATE_SCHEMA'],
  ['invalid hash', (v) => { v.sources[0].sha256 = 'not-a-hash'; }, 'SOURCE_SCHEMA'],
  ['invalid timestamp', (v) => { v.sources[0].retrievedAt = 'yesterday'; }, 'SOURCE_SCHEMA'],
  ['normalized invalid day', (v) => { v.sources[0].retrievedAt = '2026-02-30T00:00:00.000Z'; }, 'SOURCE_SCHEMA'],
  ['invalid month', (v) => { v.sources[0].retrievedAt = '2026-13-01T00:00:00.000Z'; }, 'SOURCE_SCHEMA'],
  ['empty excerpt', (v) => { v.sources[0].excerpt = ''; }, 'SOURCE_SCHEMA'],
  ['too large excerpt', (v) => { v.sources[0].excerpt = 'x'.repeat(1201); }, 'SOURCE_SCHEMA'],
  ['empty locator', (v) => { v.sources[0].locator = ' '; }, 'SOURCE_SCHEMA'],
  ['unknown source kind', (v) => { v.sources[0].kind = 'PASS'; }, 'SOURCE_SCHEMA'],
  ['malformed source id', (v) => { v.sources[0].id = 'bad'; }, 'SOURCE_SCHEMA'],
]) test(`refuses ${label}`, () => {
  const value = fixture(); mutate(value);
  const findings = validateResearch(value); assert.ok(findings.includes(expected), findings.join(','));
});
for (const url of ['', 'not-a-url', 'http://github.com/synthetic/tool',
  'https://example.test/synthetic/tool', 'https://github.com.evil.test/synthetic/tool',
  'https://user:synthetic@github.com/synthetic/tool', 'https://github.com:444/synthetic/tool',
  'https://github.com/synthetic/tool?token=synthetic', 'https://github.com/synthetic/tool#fragment',
  'https://github.com/synthetic/other', 'https://github.com/synthetic/tool/../other',
  'https://github.com/synthetic/toolbox', 'https://github.com/synthetic/%74ool',
  'https://api.github.com/advisories/synthetic']) {
  test(`refuses unsafe or mismatched URL ${url}`, () => {
    const value = fixture(); value.sources[0].url = url;
    assert.ok(validateResearch(value).includes('SOURCE_SCHEMA'));
  });
}
for (const url of ['https://raw.githubusercontent.com/synthetic/tool/main/README.md',
  'https://api.github.com/repos/synthetic/tool/releases/latest', 'https://github.com/synthetic/tool']) {
  test(`accepts scoped public source ${url}`, () => {
    const value = fixture(); value.sources[0].url = url;
    assert.deepEqual(validateResearch(value), []);
  });
}
test('unresolved discovery is retained but supplies no domain coverage', () => {
  const value = fixture();
  const unresolved = { ...value.candidates[0], repository: 'synthetic/missing', depth: 'UNRESOLVED',
    disposition: 'UNRESOLVED', sources: [] };
  value.candidates.push(unresolved); assert.deepEqual(validateResearch(value), []);
  value.candidates.shift(); assert.ok(validateResearch(value).includes('DOMAIN_COVERAGE'));
});
test('filesystem accepts valid fixture and refuses malformed, missing and oversized input', () => {
  assert.deepEqual(validateResearchWorkspace(writeFixture(JSON.stringify(fixture()))), []);
  assert.deepEqual(validateResearchWorkspace(writeFixture('{synthetic-private')), ['RESEARCH_INPUT_INVALID']);
  assert.deepEqual(validateResearchWorkspace(temporaryRoot()), ['RESEARCH_INPUT_INVALID']);
  assert.deepEqual(validateResearchWorkspace(writeFixture('x'.repeat(2_000_001))), ['RESEARCH_TOO_LARGE']);
});
test('junction cannot redirect fixed research read', () => {
  const root = temporaryRoot(); const target = temporaryRoot();
  symlinkSync(target, join(root, 'docs'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.deepEqual(validateResearchWorkspace(root), ['RESEARCH_INPUT_INVALID']);
});
test('CLI works outside repo, refuses arguments and does not echo them', () => {
  const script = join(ROOT, 'scripts/kiro/research.mjs');
  const good = spawnSync(process.execPath, [script], { cwd: homedir(), encoding: 'utf8' });
  assert.equal(good.status, 0);
  assert.deepEqual(JSON.parse(good.stdout), { structuralValidation: 'PASS', findings: [], externalExecution: 'NOT_RUN', kiroActivation: 'NOT_TESTED' });
  const bad = spawnSync(process.execPath, [script, 'synthetic-private'], { encoding: 'utf8' });
  assert.equal(bad.status, 1); assert.deepEqual(JSON.parse(bad.stdout).findings, ['UNSUPPORTED_ARGUMENTS']);
  assert.ok(!(bad.stdout + bad.stderr).includes('synthetic-private'));
});
