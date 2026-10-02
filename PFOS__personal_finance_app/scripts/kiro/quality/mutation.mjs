/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 4 (KDE07). */
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

if (process.argv.length !== 2 || process.versions.node.split('.')[0] !== '24') throw new Error('PREFLIGHT');
const base = join(homedir(), '.aki', 'tmp'); mkdirSync(base, { recursive: true });
const root = mkdtempSync(join(base, 'kde-mutation-'));
const cli = fileURLToPath(new URL('node_modules/@stryker-mutator/core/bin/stryker.js', import.meta.url));
writeFileSync(join(root, 'package.json'), JSON.stringify({ private: true, type: 'module' }));
writeFileSync(join(root, 'subject.mjs'), 'export const withinBudget = (attempt, limit) => attempt > 0 && attempt <= limit;\n');
writeFileSync(join(root, 'subject.test.mjs'), `import test from 'node:test';
import assert from 'node:assert/strict';
import { withinBudget } from './subject.mjs';
test('synthetic attempt boundary', () => {
  for (const [a, l, expected] of [[0,2,false],[-1,2,false],[1,2,true],[2,2,true],[3,2,false],[1,0,false]])
    assert.equal(withinBudget(a,l), expected);
});\n`);
writeFileSync(join(root, 'stryker.config.json'), JSON.stringify({
  mutate: ['subject.mjs'], files: ['subject.mjs', 'subject.test.mjs', 'package.json'],
  testRunner: 'command', commandRunner: { command: `"${process.execPath}" --test subject.test.mjs` },
  coverageAnalysis: 'off', concurrency: 1, reporters: ['clear-text', 'json'],
  jsonReporter: { fileName: 'mutation.json' }, thresholds: { high: 100, low: 100, break: 100 },
  timeoutMS: 5000, timeoutFactor: 2, cleanTempDir: false, plugins: [],
}, null, 2));
const result = spawnSync(process.execPath, [cli, 'run', 'stryker.config.json'], {
  cwd: root, encoding: 'utf8', timeout: 180_000, maxBuffer: 2_000_000,
});
writeFileSync(join(root, 'run.log'), (result.stdout ?? '') + (result.stderr ?? ''));
if (result.status !== 0 || result.error) {
  console.error(JSON.stringify({ mutationTrial: 'FAIL', exitCode: result.status, detail: 'Inspect owned kde-mutation temporary run.log' }));
  process.exitCode = 1;
} else {
  const report = JSON.parse(readFileSync(join(root, 'mutation.json'), 'utf8'));
  const mutants = Object.values(report.files).flatMap((file) => file.mutants);
  assert.ok(mutants.length > 0); assert.ok(mutants.every((mutant) => mutant.status === 'Killed'));
  console.log(JSON.stringify({ mutationTrial: 'PASS', mutants: mutants.length,
    killed: mutants.length, scope: 'synthetic attempt boundary only', kiroActivation: 'NOT_TESTED' }));
}
