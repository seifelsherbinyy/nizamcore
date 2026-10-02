/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 4 (KDE04/07). */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const read = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
test('installed versions and lock match exact authorized dependencies', () => {
  const manifest = read('package.json'); const lock = read('package-lock.json');
  assert.deepEqual(manifest.dependencies, { '@stryker-mutator/core': '10.0.0', 'axe-core': '4.13.0', 'fast-check': '4.10.1' });
  assert.deepEqual(lock.packages[''].dependencies, manifest.dependencies);
  for (const [name, version] of Object.entries(manifest.dependencies)) {
    assert.equal(read(`node_modules/${name}/package.json`).version, version);
    assert.equal(lock.packages[`node_modules/${name}`].version, version);
  }
  assert.equal(read('node_modules/qs/package.json').version, '6.16.0');
  for (const [name, entry] of Object.entries(lock.packages)) {
    if (!name) continue;
    assert.ok(entry.resolved.startsWith('https://registry.npmjs.org/'));
    assert.match(entry.integrity, /^sha512-/); assert.equal(entry.hasInstallScript, undefined);
    assert.ok(entry.license);
  }
});
test('browser trial refuses absent executable and unsupported arguments before launch', () => {
  const env = { ...process.env }; delete env.NIZAM_BROWSER_EXECUTABLE;
  for (const args of [[], ['--remote']]) {
    const result = spawnSync(process.execPath, [fileURLToPath(new URL('accessibility.mjs', import.meta.url)), ...args],
      { env, encoding: 'utf8', timeout: 10_000 });
    assert.equal(result.status, 1); assert.equal(JSON.parse(result.stderr).phase, 'preflight');
  }
});
test('mutation trial refuses unsupported arguments without creating a trial', () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('mutation.mjs', import.meta.url)), '--all'],
    { encoding: 'utf8', timeout: 10_000 });
  assert.equal(result.status, 1); assert.match(result.stderr, /PREFLIGHT/);
});
