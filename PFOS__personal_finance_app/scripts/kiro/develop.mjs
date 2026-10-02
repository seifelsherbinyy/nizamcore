/** Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP14). */
import { readdirSync, lstatSync, realpathSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { ROOT, localFile } from './validate.mjs';

export const QUALITY_ACTIONS = Object.freeze(['lint', 'format-check', 'format']);
const SOURCE_PATH = /^src\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\.tsx?$/;

/** Validate the entire request before resolving tools or executing anything. */
export function planDevelopment(args, root = ROOT, cwd = process.cwd()) {
  if (!Array.isArray(args) || args.length !== 2 || !QUALITY_ACTIONS.includes(args[0])
    || typeof args[1] !== 'string' || args[1].trim() !== args[1] || !SOURCE_PATH.test(args[1])) throw new Error('INVALID_DEVELOPMENT_REQUEST');
  if (realpathSync(cwd) !== realpathSync(root)) throw new Error('WRONG_WORKSPACE');
  const [action, path] = args;
  const target = localFile(root, path);
  const tool = localFile(root, action === 'lint'
    ? 'node_modules/eslint/bin/eslint.js' : 'node_modules/prettier/bin/prettier.cjs');
  return {
    executable: process.execPath,
    args: action === 'lint' ? [tool, '--max-warnings', '0', '--', target]
      : [tool, action === 'format' ? '--write' : '--check', '--', target],
    options: { cwd: realpathSync(root), shell: false, stdio: 'inherit' },
  };
}

export function runDevelopment(args, { root = ROOT, cwd = process.cwd(), spawn = spawnSync } = {}) {
  const plan = planDevelopment(args, root, cwd);
  const result = spawn(plan.executable, plan.args, plan.options);
  if (result.error || result.signal || !Number.isInteger(result.status)) throw new Error('DEVELOPMENT_PROCESS_FAILED');
  return result.status;
}

/** Names only, no source contents, credentials, gate records or external paths. */
export function discoverSources(root = ROOT) {
  const paths = [];
  function walk(relative) {
    const directory = join(root, relative);
    if (lstatSync(directory).isSymbolicLink()) throw new Error('SYMLINK_DIRECTORY');
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = `${relative}/${entry.name}`;
      if (entry.isSymbolicLink()) throw new Error('SYMLINK_ENTRY');
      if (entry.isDirectory()) walk(path);
      else if (entry.isFile() && /\.tsx?$/.test(entry.name)) {
        if (path.trim() !== path || !SOURCE_PATH.test(path)) throw new Error('UNSAFE_SOURCE_PATH');
        paths.push(path);
      }
    }
  }
  walk('src');
  return paths.sort();
}

export function semanticInventory(paths = discoverSources()) {
  if (!Array.isArray(paths) || !paths.length || new Set(paths).size !== paths.length
    || paths.some((path) => typeof path !== 'string' || path.trim() !== path || !SOURCE_PATH.test(path))) throw new Error('INVALID_SOURCE_INVENTORY');
  return [...paths].sort().flatMap((path) => [
    ...QUALITY_ACTIONS.map((action) => ({ id: `${action}:${path}`, command: `node scripts/kiro/develop.mjs ${action} ${path}` })),
    ...(/\.test\.tsx?$/.test(path) ? [{ id: `test:${path}`, command: `npm test -- ${path}` }] : []),
  ]);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.exitCode = runDevelopment(process.argv.slice(2)); }
  catch (error) {
    console.error(error instanceof Error ? error.message : 'DEVELOPMENT_FAILED');
    process.exitCode = 1;
  }
}
