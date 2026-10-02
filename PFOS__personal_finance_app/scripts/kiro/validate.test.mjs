/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE03). */
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, symlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { AUTHORITY, ROOT, localFile, skillMetadata, validateRegistry, validateWorkspace } from './validate.mjs';

const required = ['nizam-investigate', 'nizam-implement', 'nizam-debug', 'nizam-test-repair',
  'nizam-code-quality', 'nizam-docs-research', 'nizam-repository', 'nizam-vps-inspect',
  'nizam-service-diagnostics', 'nizam-deploy', 'nizam-validate', 'nizam-browser-test'];
const registry = JSON.parse(readFileSync(join(ROOT, 'docs/kiro/capability-registry.json'), 'utf8'));
const read = (path) => readFileSync(localFile(ROOT, path), 'utf8');
const sample = read('.kiro/skills/nizam-debug/SKILL.md');
const fixture = () => structuredClone(registry);

test('actual workspace has exactly the twelve required skills and validates', () => {
  assert.deepEqual(registry.capabilities.map((row) => row.id).sort(), [...required].sort());
  assert.deepEqual(validateWorkspace(), []);
});
test('valid LF and CRLF metadata have identical semantics', () => {
  const lf = sample.replaceAll('\r\n', '\n');
  assert.deepEqual(skillMetadata(lf), skillMetadata(lf.replaceAll('\n', '\r\n')));
});
for (const [label, value] of [['null', null], ['array', []], ['empty', {}], ['version', { ...registry, schemaVersion: 2 }],
  ['unknown field', { ...registry, allowed: true }], ['missing capabilities', { ...registry, capabilities: [] }]]) {
  test(`registry refuses ${label}`, () => assert.deepEqual(validateRegistry(value, read), ['REGISTRY_SCHEMA']));
}
for (const [label, mutate] of [
  ['duplicate identity', (r) => r.capabilities.push(r.capabilities[0])],
  ['invented readiness', (r) => { r.capabilities[0].activation = 'VERIFIED'; }],
  ['unsupported kind', (r) => { r.capabilities[0].kind = 'mcp'; }],
  ['empty prompt', (r) => { r.capabilities[0].positive = ''; }],
  ['equal prompts', (r) => { r.capabilities[0].negative = r.capabilities[0].positive; }],
  ['unknown permission', (r) => { r.capabilities[0].autoApprove = ['*']; }],
  ['traversal reference', (r) => { r.capabilities[0].references = ['../private.md']; }],
  ['duplicate reference', (r) => { r.capabilities[0].references.push(r.capabilities[0].references[0]); }],
  ['path mismatch', (r) => { r.capabilities[0].path = '.kiro/skills/other/SKILL.md'; }],
]) test(`capability refuses ${label}`, () => { const value = fixture(); mutate(value); assert.ok(validateRegistry(value, read).length > 0); });
test('missing authority refuses without echoing exception text', () => {
  const findings = validateRegistry(registry, (path) => { if (path === AUTHORITY) throw new Error('sensitive-fixture'); return read(path); });
  assert.ok(findings.includes('AUTHORITY_MISSING')); assert.ok(!JSON.stringify(findings).includes('sensitive-fixture'));
});
test('missing reference fails', () => {
  assert.ok(validateRegistry(registry, (path) => { if (path.startsWith('docs/kiro/references/')) throw new Error('missing'); return read(path); }).length > 0);
});
test('duplicate descriptions are detected', () => {
  const description = skillMetadata(read(registry.capabilities[0].path)).description;
  const findings = validateRegistry(registry, (path) => path === registry.capabilities[1].path
    ? read(path).replace(/^description: .+$/m, `description: ${JSON.stringify(description)}`) : read(path));
  assert.ok(findings.includes('DUPLICATE_DESCRIPTION'));
});
for (const [label, transform] of [
  ['missing frontmatter', (s) => s.slice(4)],
  ['duplicate key', (s) => s.replace('name: nizam-debug', 'name: nizam-debug\nname: nizam-debug')],
  ['unknown field', (s) => s.replace('name: nizam-debug', 'name: nizam-debug\nallowed-tools: shell')],
  ['invalid JSON scalar', (s) => s.replace(/^description: .+$/m, 'description: "unterminated')],
  ['too long description', (s) => s.replace(/^description: .+$/m, `description: "${'x'.repeat(1025)}"`)],
  ['too long body', (s) => s + '\n'.repeat(151)],
  ['missing workflow', (s) => s.replace('## Workflow', '## Other')],
]) test(`metadata refuses ${label}`, () => assert.throws(() => skillMetadata(transform(sample))));
for (const path of ['../private.md', '/absolute.md', 'C:/private.md', 'a\\b.md', 'a//b.md', './a.md', 'a/../b.md', 'x.md:stream', '']) {
  test(`local reader refuses unsafe path ${JSON.stringify(path)}`, () => assert.throws(() => localFile(ROOT, path)));
}
test('local reader refuses directory and absent file', () => {
  assert.throws(() => localFile(ROOT, '.kiro')); assert.throws(() => localFile(ROOT, 'nonexistent-kde-file.md'));
});
test('missing workspace fails closed', () => assert.deepEqual(validateWorkspace(join(ROOT, 'nonexistent-kde-root')), ['WORKSPACE_INPUT_INVALID']));
test('junction component cannot redirect a read', () => {
  const base = join(homedir(), '.aki', 'tmp'); mkdirSync(base, { recursive: true });
  const dir = mkdtempSync(join(base, 'kde-symlink-test-'));
  mkdirSync(join(dir, 'target')); writeFileSync(join(dir, 'target', 'sample.md'), 'synthetic');
  symlinkSync(join(dir, 'target'), join(dir, 'link'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => localFile(dir, 'link/sample.md'), /SYMLINK_PATH/);
});
test('CLI accepts no arguments and resolves root independently of cwd', () => {
  const result = spawnSync(process.execPath, [join(ROOT, 'scripts/kiro/validate.mjs')], { cwd: homedir(), encoding: 'utf8' });
  assert.equal(result.status, 0); assert.equal(JSON.parse(result.stdout).kiroActivation, 'UNVERIFIED');
});
test('CLI refuses unsupported arguments', () => {
  const result = spawnSync(process.execPath, [join(ROOT, 'scripts/kiro/validate.mjs'), '--skip'], { encoding: 'utf8' });
  assert.equal(result.status, 1); assert.deepEqual(JSON.parse(result.stdout).findings, ['UNSUPPORTED_ARGUMENTS']);
});
