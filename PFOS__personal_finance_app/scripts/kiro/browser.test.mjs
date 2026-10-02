/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE06). */
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { ROOT } from './validate.mjs';
import { assetPath, serveBuild } from './browser-server.mjs';

test('browser assets accept root and known content types', () => {
  assert.equal(assetPath('/'), 'index.html');
  assert.equal(assetPath('/assets/app.js?version=1'), 'assets/app.js');
});
for (const value of ['/../secret.json', '/%2e%2e/secret.json', '//remote.test/x.js', '/a%5cb.js',
  '/%00.js', '/x.env', '/a//x.js', '/a/./x.js', 'https://remote.test/a.js', '/bad%zz']) {
  test(`browser asset path rejects ${value}`, () => assert.throws(() => assetPath(value)));
}
test('server confines content, headers, methods and junctions', async () => {
  const base = join(homedir(), '.aki', 'tmp'); mkdirSync(base, { recursive: true });
  const dir = mkdtempSync(join(base, 'kde-browser-test-'));
  writeFileSync(join(dir, 'index.html'), '<h1>Synthetic</h1>');
  writeFileSync(join(dir, 'app.js'), 'void 0;');
  mkdirSync(join(dir, 'target')); writeFileSync(join(dir, 'target', 'hidden.json'), '{}');
  symlinkSync(join(dir, 'target'), join(dir, 'link'), process.platform === 'win32' ? 'junction' : 'dir');
  const server = await serveBuild(dir);
  try {
    assert.equal(new URL(server.origin).hostname, '127.0.0.1');
    const page = await fetch(server.origin); assert.equal(page.status, 200); assert.match(await page.text(), /Synthetic/);
    const js = await fetch(server.origin + '/app.js'); assert.equal(js.headers.get('content-type'), 'text/javascript');
    assert.equal(js.headers.get('x-content-type-options'), 'nosniff');
    assert.equal((await fetch(server.origin, { method: 'HEAD' })).status, 200);
    assert.equal(await (await fetch(server.origin, { method: 'HEAD' })).text(), '');
    assert.equal((await fetch(server.origin, { method: 'POST' })).status, 405);
    assert.equal((await fetch(server.origin + '/absent.js')).status, 404);
    assert.equal((await fetch(server.origin + '/link/hidden.json')).status, 404);
  } finally { await server.close(); }
});
test('missing build never starts a server', async () => {
  await assert.rejects(serveBuild(join(ROOT, 'nonexistent-kde-build')));
});
test('browser runner requires explicit executable without leaking env', () => {
  const env = { ...process.env }; delete env.NIZAM_BROWSER_EXECUTABLE;
  const result = spawnSync(process.execPath, [join(ROOT, 'scripts/kiro/browser-smoke.mjs')], { env, encoding: 'utf8' });
  assert.equal(result.status, 1); assert.equal(JSON.parse(result.stderr).phase, 'preflight');
});
