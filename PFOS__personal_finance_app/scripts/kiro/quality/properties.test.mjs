/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 4 (KDE07). */
import test from 'node:test';
import assert from 'node:assert/strict';
import fc from 'fast-check';
import { readFileSync } from 'node:fs';
import { validateResearch } from '../research.mjs';
import { assetPath } from '../browser-server.mjs';

const options = { seed: 20260916, numRuns: 500 };
const evidence = JSON.parse(readFileSync(new URL('../../../docs/kiro/operational-excellence/phase-2-evidence.json', import.meta.url), 'utf8'));

test('generated JSON never crashes research validation or invents valid input', () => {
  fc.assert(fc.property(fc.jsonValue(), (value) => {
    const findings = validateResearch(value);
    assert.ok(Array.isArray(findings)); assert.ok(findings.length > 0);
  }), options);
});
test('arbitrary unapproved execution states fail closed', () => {
  fc.assert(fc.property(fc.string().filter((s) => s !== 'NOT_RUN'), (state) => {
    const value = structuredClone(evidence); value.candidates[0].execution = state;
    assert.ok(validateResearch(value).includes('CANDIDATE_SCHEMA'));
  }), options);
});
test('generated path traversal is never served', () => {
  const segment = fc.stringMatching(/^[a-z]{1,12}$/);
  fc.assert(fc.property(segment, (name) => {
    assert.throws(() => assetPath(`/../${name}.js`));
    assert.throws(() => assetPath(`/%2e%2e/${name}.js`));
    assert.throws(() => assetPath(`/${name}/../app.js`));
  }), options);
});
test('known-false property is detected and replayed with the same counterexample', () => {
  const property = fc.property(fc.integer({ min: 0, max: 100 }), (n) => n + 1 === n);
  const result = fc.check(property, options);
  assert.equal(result.failed, true); assert.ok(result.counterexample);
  const replay = fc.check(property, { ...options, path: result.counterexamplePath });
  assert.equal(replay.failed, true); assert.deepEqual(replay.counterexample, result.counterexample);
});
