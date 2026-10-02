/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE06). */
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { ROOT } from './validate.mjs';
import { serveBuild } from './browser-server.mjs';

let server;
let browser;
let phase = 'preflight';
try {
  if (process.argv.length !== 2 || process.versions.node.split('.')[0] !== '24') throw new Error('RUNTIME');
  const executablePath = process.env.NIZAM_BROWSER_EXECUTABLE;
  if (!executablePath || !existsSync(executablePath)) throw new Error('BROWSER_REQUIRED');
  const { chromium } = await import('playwright-core');
  phase = 'serve-built-app';
  server = await serveBuild(join(ROOT, 'dist'));
  phase = 'launch-isolated-browser';
  browser = await chromium.launch({ executablePath, headless: true, chromiumSandbox: true, timeout: 30_000 });
  const context = await browser.newContext({ serviceWorkers: 'block', acceptDownloads: false });
  let blockedRequests = 0;
  await context.route('**/*', async (route) => {
    if (new URL(route.request().url()).origin !== server.origin) { blockedRequests++; await route.abort(); }
    else await route.continue();
  });
  await context.routeWebSocket('**/*', (socket) => { blockedRequests++; socket.close(); });
  const page = await context.newPage();
  page.setDefaultTimeout(15_000);
  const errors = [];
  page.on('pageerror', () => errors.push('PAGE_ERROR'));
  page.on('console', (message) => { if (message.type() === 'error') errors.push('CONSOLE_ERROR'); });
  phase = 'app-navigation';
  await page.goto(server.origin, { waitUntil: 'networkidle', timeout: 30_000 });
  const nav = page.getByRole('navigation', { name: 'Main navigation' });
  await nav.waitFor();
  for (const [label, hash] of [['Budget', '#/budget'], ['Settings', '#/settings'], ['Reports', '#/reports']]) {
    await nav.getByRole('link', { name: label, exact: true }).click();
    await page.waitForURL((url) => url.hash === hash);
    assert.ok((await page.locator('main').innerText()).trim().length > 0);
    if (label !== 'Budget') await page.getByRole('heading', { name: label, exact: true }).waitFor();
  }
  phase = 'reload';
  await page.reload({ waitUntil: 'networkidle' });
  await nav.waitFor();
  assert.equal(new URL(page.url()).hash, '#/reports');
  assert.ok((await page.locator('main').innerText()).trim().length > 0);
  assert.deepEqual(errors, []);
  assert.equal(blockedRequests, 0, 'Unexpected external request attempt');
  console.log(JSON.stringify({ localBrowserSmoke: 'PASS', routes: 3, reload: true,
    pageErrors: errors.length, blockedExternalRequests: blockedRequests, kiroActivation: 'UNVERIFIED' }));
} catch {
  console.error(JSON.stringify({ localBrowserSmoke: 'FAIL', phase,
    detail: phase === 'preflight' ? 'Require Node 24, installed pinned dependency, and NIZAM_BROWSER_EXECUTABLE.' : 'Inspect the indicated local phase with synthetic data; raw output withheld.' }));
  process.exitCode = 1;
} finally {
  try { await browser?.close(); } catch { process.exitCode = 1; console.error('BROWSER_CLOSE_FAILED'); }
  try { await server?.close(); } catch { process.exitCode = 1; console.error('SERVER_CLOSE_FAILED'); }
}
