#!/usr/bin/env node
/** Contract 05 baseline addendum, Phase 0: local evidence report only. No live probe. */
import { readFileSync } from 'node:fs';
import { assessBaseline } from '../../src/server/hermes/baselineEvidence.ts';

try {
  if (process.argv.length > 3) throw new Error('arguments');
  const input = process.argv[2] ?? new URL('../../docs/architecture/agentic-profile-baseline.json', import.meta.url);
  const report = assessBaseline(JSON.parse(readFileSync(input, 'utf8')), new Date().toISOString());
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.allCurrent ? 0 : 2;
} catch {
  console.error('BASELINE_INPUT_INVALID');
  process.exitCode = 1;
}
