/** Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP13-17). */
import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { planDevelopment, runDevelopment, semanticInventory, discoverSources } from './develop.mjs';
import { SHELL_PATTERNS } from './permissions.mjs';

function fixture() {
  const parent = join(homedir(), '.aki', 'tmp');
  mkdirSync(parent, { recursive: true });
  const root = mkdtempSync(join(parent, 'nizam-develop-'));
  for (const path of ['src/example.ts', 'node_modules/eslint/bin/eslint.js', 'node_modules/prettier/bin/prettier.cjs']) {
    mkdirSync(join(root, path, '..'), { recursive: true });
    writeFileSync(join(root, path), '// synthetic, never executed\n');
  }
  return root;
}

test('each action resolves one local tool and target with no shell', () => {
  const root = fixture();
  for (const [action, flag] of [['lint', '--max-warnings'], ['format-check', '--check'], ['format', '--write']]) {
    const plan = planDevelopment([action, 'src/example.ts'], root, root);
    assert.equal(plan.executable, process.execPath);
    assert.equal(plan.options.shell, false);
    assert.equal(plan.args[1], flag);
    assert.equal(plan.args.at(-2), '--');
    assert.equal(plan.args.at(-1), join(root, 'src/example.ts'));
    assert.equal(runDevelopment([action, 'src/example.ts'], {
      root, cwd: root, spawn: (...args) => {
        assert.deepEqual(args, [plan.executable, plan.args, plan.options]);
        return { status: 7 };
      },
    }), 7);
  }
});

test('malformed requests and missing files never spawn', () => {
  const root = fixture();
  const invalid = [[], ['lint'], ['install', 'src/example.ts'], ['lint', 'src/example.ts', '--fix'],
    ['lint', 'src/../example.ts'], ['lint', '../src/example.ts'], ['lint', 'src/example.ts;echo'],
    ['lint', 'src/example.ts\n'], ['lint', 'src/*'], ['lint', 'src/a b.ts'],
    ['lint', 'C:/src/example.ts'], ['lint', 'src\\example.ts'], ['lint', 'src/$(x).ts'],
    ['lint', 'src/missing.ts'], ['lint', null], ['lint', 1], null];
  for (const args of invalid) {
    let calls = 0;
    assert.throws(() => runDevelopment(args, { root, cwd: root, spawn: () => { calls++; } }));
    assert.equal(calls, 0);
  }
  assert.throws(() => planDevelopment(['lint', 'src/example.ts'], root, homedir()), /WRONG_WORKSPACE/);
});

test('source and executable directory junctions fail closed', () => {
  const root = fixture();
  symlinkSync(join(root, 'src'), join(root, 'src/linked'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => planDevelopment(['lint', 'src/linked/example.ts'], root, root), /SYMLINK_PATH/);
  assert.throws(() => discoverSources(root), /SYMLINK_ENTRY/);
  const other = mkdtempSync(join(homedir(), '.aki/tmp/nizam-linked-tool-'));
  mkdirSync(join(other, 'src'));
  writeFileSync(join(other, 'src/example.ts'), '// synthetic\n');
  symlinkSync(join(root, 'node_modules'), join(other, 'node_modules'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => planDevelopment(['lint', 'src/example.ts'], other, other), /SYMLINK_PATH/);
});

test('process errors/signals cannot report success', () => {
  const root = fixture();
  for (const result of [{ error: new Error('synthetic') }, { status: null }, { status: 0, signal: 'SIGTERM' }]) {
    assert.throws(() => runDevelopment(['lint', 'src/example.ts'], { root, cwd: root, spawn: () => result }), /DEVELOPMENT_PROCESS_FAILED/);
  }
});

test('500+ semantic action/target pairs, not aliases or hypothetical ecosystem commands', () => {
  const paths = discoverSources();
  const operations = semanticInventory(paths);
  assert.ok(operations.length >= 500);
  assert.equal(operations.length, paths.length * 3 + paths.filter((p) => /\.test\.tsx?$/.test(p)).length);
  assert.equal(new Set(operations.map((op) => op.id)).size, operations.length);
  assert.deepEqual(semanticInventory([...paths].reverse()), operations);
  for (const { command } of operations) assert.ok(SHELL_PATTERNS.some((pattern) => {
    const regex = pattern.split('*').map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*');
    return new RegExp(`^${regex}$`).test(command);
  }), command);
  for (const paths of [[], ['src/x.ts', 'src/x.ts'], ['src/../x.ts'], ['src/x.ts\n'], ['src/x.ts\r'], [null]]) {
    assert.throws(() => semanticInventory(paths), /INVALID_SOURCE_INVENTORY/);
  }
});

test('real pinned formatter writes and rechecks only an isolated synthetic file', async () => {
  const { cpSync, readFileSync } = await import('node:fs');
  const { ROOT } = await import('./validate.mjs');
  const root = fixture();
  cpSync(join(ROOT, 'node_modules/prettier'), join(root, 'node_modules/prettier'), { recursive: true });
  const path = join(root, 'src/example.ts');
  writeFileSync(path, '// Owner: KWP Phase 3 synthetic fixture\nexport const syntheticValue=1;\n');
  assert.equal(runDevelopment(['format', 'src/example.ts'], { root, cwd: root }), 0);
  assert.match(readFileSync(path, 'utf8'), /syntheticValue = 1;/);
  assert.equal(runDevelopment(['format-check', 'src/example.ts'], { root, cwd: root }), 0);
});
