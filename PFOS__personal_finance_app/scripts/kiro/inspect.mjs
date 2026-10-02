/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE05). */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { ROOT, localFile, validateWorkspace } from './validate.mjs';

try {
  if (process.argv.length !== 2) throw new Error('ARGUMENTS');
  const pkg = JSON.parse(readFileSync(localFile(ROOT, 'package.json'), 'utf8'));
  let alwaysBytes = 0;
  let manualBytes = 0;
  for (const name of readdirSync(join(ROOT, '.kiro/steering'))) {
    if (!name.endsWith('.md')) continue;
    const text = readFileSync(localFile(ROOT, `.kiro/steering/${name}`), 'utf8');
    if (/^---\r?\ninclusion: manual\r?\n---/.test(text)) manualBytes += Buffer.byteLength(text);
    else alwaysBytes += Buffer.byteLength(text);
  }
  const findings = validateWorkspace();
  console.log(JSON.stringify({ node: process.versions.node, requiredNode: pkg.engines.node,
    skills: readdirSync(join(ROOT, '.kiro/skills')).length,
    workspaceSteeringBytes: { always: alwaysBytes, manual: manualBytes },
    globalConfiguration: 'NOT_READ', kiroActivation: 'UNVERIFIED', findings }, null, 2));
  process.exitCode = findings.length ? 1 : 0;
} catch {
  console.error('INSPECTION_INPUT_INVALID');
  process.exitCode = 1;
}
