/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 4 (KDE06/07). */
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { chromium } from 'playwright-core';
import { ROOT } from '../validate.mjs';
import { serveBuild } from '../browser-server.mjs';

const require = createRequire(import.meta.url);
let browser;
let server;
let phase = 'preflight';
try {
  const executablePath = process.env.NIZAM_BROWSER_EXECUTABLE;
  if (process.argv.length !== 2 || process.versions.node.split('.')[0] !== '24'
    || !executablePath || !existsSync(executablePath)) throw new Error('PREFLIGHT');
  server = await serveBuild(join(ROOT, 'dist'));
  browser = await chromium.launch({ executablePath, headless: true, chromiumSandbox: true, timeout: 30_000 });
  const context = await browser.newContext({ serviceWorkers: 'block', acceptDownloads: false });
  let blocked = 0;
  await context.route('**/*', async (route) => {
    if (new URL(route.request().url()).origin !== server.origin) { blocked++; await route.abort(); }
    else await route.continue();
  });
  await context.routeWebSocket('**/*', (socket) => { blocked++; socket.close(); });
  const page = await context.newPage(); page.setDefaultTimeout(15_000);
  const scan = async () => {
    await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
    return page.evaluate(async () => {
      const result = await globalThis.axe.run();
      return { violations: result.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
        incomplete: result.incomplete.map((v) => v.id) };
    });
  };
  const document = (body) => `<!doctype html><html lang="en"><head><title>Synthetic accessibility fixture</title></head><body><main><h1>Fixture</h1>${body}</main></body></html>`;
  phase = 'negative-control';
  await page.goto(server.origin, { waitUntil: 'networkidle' });
  await page.setContent(document('<button></button><img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==">'));
  const bad = await scan();
  assert.ok(bad.violations.some((v) => v.id === 'button-name'));
  assert.ok(bad.violations.some((v) => v.id === 'image-alt'));
  phase = 'positive-control';
  await page.setContent(document('<button>Continue</button>'));
  const good = await scan(); assert.deepEqual(good.violations, []);
  phase = 'built-app';
  const routes = [];
  for (const hash of ['#/budget', '#/settings', '#/reports']) {
    await page.goto(server.origin + '/' + hash, { waitUntil: 'networkidle' });
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('navigation', { name: 'Main navigation' }).waitFor();
    routes.push({ route: hash, ...await scan() });
  }
  assert.equal(blocked, 0);
  const violations = routes.reduce((count, row) => count + row.violations.length, 0);
  console.log(JSON.stringify({ fixtureControls: 'PASS', browserVersion: browser.version(), routes,
    blockedExternalRequests: blocked, appAccessibility: violations ? 'FAIL' : 'PASS', kiroActivation: 'NOT_TESTED' }));
  if (violations) process.exitCode = 1;
} catch {
  console.error(JSON.stringify({ accessibilityTrial: 'FAIL', phase })); process.exitCode = 1;
} finally {
  try { await browser?.close(); } catch { process.exitCode = 1; console.error('BROWSER_CLOSE_FAILED'); }
  try { await server?.close(); } catch { process.exitCode = 1; console.error('SERVER_CLOSE_FAILED'); }
}
