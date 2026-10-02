/** Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP). */
import { lstatSync, readdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
export const OUTPUT = 'docs/kiro/workspace-permissions.yaml';
const TEST_PATH = /^src\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\.test\.tsx?$/;
export const DEVELOPMENT_COMMANDS = Object.freeze([
  'npm run typecheck', 'npm run lint', 'npm run build', 'npm test',
  'npm ls --depth=0', 'npm outdated --offline', 'curl.exe --version',
  'node --test scripts/kiro/develop.test.mjs',
  'node --test scripts/kiro/permissions.test.mjs scripts/kiro/develop.test.mjs',
  'npm test -- --run', 'npm run verify:all -- --all',
  'npm run dev -- --host 127.0.0.1', 'npm run preview -- --host 127.0.0.1',
  'node --test scripts/kiro/permissions.test.mjs',
  'node scripts/kiro/permissions.mjs', 'node scripts/kiro/validate.mjs',
  'git status', 'git status --short', 'git status --porcelain=v1',
  'git diff --no-ext-diff --no-textconv',
  'git diff --no-ext-diff --no-textconv --stat',
  'git diff --no-ext-diff --no-textconv --check',
  'git diff --no-ext-diff --no-textconv --cached',
  'git log -5 --oneline', 'git log -10 --oneline', 'git log -20 --oneline',
  'git ls-files', 'git ls-files --modified', 'git ls-files --others --exclude-standard',
  'git branch --show-current', 'git branch --list', 'git rev-parse --show-toplevel',
  'git --version', 'node --version', 'npm --version',
  'pwd', 'Get-Location', 'Get-ChildItem', 'Get-ChildItem src', 'Get-ChildItem tests',
]);
export const MAX_PATTERNS = 64;
export const ALLOW_BATCH_SIZE = 8;
export const SHELL_PATTERNS = Object.freeze([...DEVELOPMENT_COMMANDS,
  ...['ts', 'tsx'].flatMap((extension) => [
    `npm test -- src/*.test.${extension}`, `npm test -- --run src/*.test.${extension}`,
    `node node_modules/vitest/vitest.mjs run src/*.test.${extension}`,
  ]),
  'node scripts/kiro/develop.mjs *',
  'rg *', 'Get-Content *', 'Get-ChildItem *', 'Get-Command *', 'Test-Path *',
]);
const EDIT_PATHS = ['./src/**', './tests/**', './docs/**', './scripts/**', './.kiro/specs/**'];
const SENSITIVE_PATHS = [
  '**/.env', '**/.env.*', '**/.secrets/**', '**/*.pem', '**/*.key',
  './data/**', './FINANCIAL/**', './ops/**',
];
const DOCUMENTATION_HOSTS = [
  'kiro.dev', 'www.typescriptlang.org', 'react.dev', 'vite.dev', 'vitest.dev',
  'nodejs.org', 'docs.npmjs.com', 'git-scm.com', 'developer.mozilla.org',
];

/** Names only: never read a ledger, secret, gate record or test body. */
export function discoverTests(root = ROOT) {
  const paths = [];
  function walk(relative) {
    const directory = join(root, relative);
    if (lstatSync(directory).isSymbolicLink()) throw new Error('SYMLINK_DIRECTORY');
    for (const item of readdirSync(directory, { withFileTypes: true })) {
      const path = `${relative}/${item.name}`;
      if (item.isSymbolicLink()) throw new Error('SYMLINK_ENTRY');
      if (item.isDirectory()) walk(path);
      else if (item.isFile() && /\.test\.tsx?$/.test(item.name)) paths.push(path);
    }
  }
  walk('src');
  return paths.sort();
}

export function commandInventory(testPaths) {
  if (!Array.isArray(testPaths) || testPaths.length === 0) throw new Error('EMPTY_TEST_INVENTORY');
  if (new Set(testPaths).size !== testPaths.length) throw new Error('DUPLICATE_TEST_PATH');
  const commands = [...DEVELOPMENT_COMMANDS];
  for (const path of [...testPaths].sort()) {
    if (typeof path !== 'string' || !TEST_PATH.test(path)) throw new Error('UNSAFE_TEST_PATH');
    commands.push(`npm test -- ${path}`, `npm test -- --run ${path}`,
      `node node_modules/vitest/vitest.mjs run ${path}`);
  }
  return commands;
}

export function permissionPolicy(commands) {
  if (!Array.isArray(commands) || commands.length === 0
    || commands.some((value) => typeof value !== 'string' || !/^[A-Za-z0-9_./=: -]+$/.test(value))
    || new Set(commands).size !== commands.length) throw new Error('INVALID_COMMAND_INVENTORY');
  const allowRules = [];
  for (let index = 0; index < SHELL_PATTERNS.length; index += ALLOW_BATCH_SIZE) {
    allowRules.push({ capability: 'shell', effect: 'allow',
      match: SHELL_PATTERNS.slice(index, index + ALLOW_BATCH_SIZE) });
  }
  const policy = { rules: [
    ...allowRules,
    { capability: 'shell', effect: 'ask', exclude: [...SHELL_PATTERNS] },
    { capability: 'fs_read', effect: 'allow', match: ['./**'] },
    { capability: 'fs_read', effect: 'ask', exclude: ['./**'] },
    { capability: 'fs_write', effect: 'allow', match: [...EDIT_PATHS] },
    { capability: 'fs_write', effect: 'ask', exclude: [...EDIT_PATHS] },
    { capability: 'filesystem', effect: 'ask', match: [...SENSITIVE_PATHS] },
    { capability: 'web_fetch', effect: 'allow', match: [...DOCUMENTATION_HOSTS] },
    { capability: 'web_fetch', effect: 'ask', exclude: [...DOCUMENTATION_HOSTS] },
    { capability: 'web_search', effect: 'allow' },
    { capability: 'diagnostics', effect: 'allow' },
    { capability: 'context', effect: 'allow' },
    { capability: 'skill', effect: 'allow' },
    { capability: 'subagent', effect: 'allow' },
    { capability: 'mcp', effect: 'ask' },
  ] };
  assertPatternBudget(policy);
  return policy;
}

export function assertPatternBudget(policy) {
  for (const rule of policy.rules) {
    for (const key of ['match', 'exclude']) {
      const limit = key === 'match' && rule.effect === 'allow' && rule.capability === 'shell'
        ? ALLOW_BATCH_SIZE : MAX_PATTERNS;
      if ((rule[key]?.length ?? 0) > limit) throw new Error('POLICY_PATTERN_BUDGET');
    }
  }
}

/** Emit only our schema subset; JSON-quoted scalars are valid YAML strings. */
export function renderPolicy(commands) {
  const lines = [
    '# Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP).',
    '# Generated review template, NOT loaded from this repository by Kiro.',
    '# Compact development patterns. Not a sandbox; review cwd, scripts and environment.',
    `# ${commands.length} concrete coverage cases; ${SHELL_PATTERNS.length} runtime shell patterns.`,
    'rules:',
  ];
  for (const rule of permissionPolicy(commands).rules) {
    lines.push(`  - capability: ${rule.capability}`, `    effect: ${rule.effect}`);
    for (const key of ['match', 'exclude']) {
      if (!rule[key]) continue;
      lines.push(`    ${key}:`);
      lines.push(...rule[key].map((value) => `      - ${JSON.stringify(value)}`));
    }
  }
  return `${lines.join('\n')}\n`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length > 1 || (args.length === 1 && args[0] !== '--write')) throw new Error('UNSUPPORTED_ARGUMENTS');
  const tests = discoverTests();
  const commands = commandInventory(tests);
  if (commands.length < 500) throw new Error('INSUFFICIENT_COMMAND_COVERAGE');
  if (args[0] === '--write') writeFileSync(join(ROOT, OUTPUT), renderPolicy(commands), { flag: 'wx' });
  console.log(JSON.stringify({ tests: tests.length, concreteCommands: commands.length,
    templateWritten: args[0] === '--write', kiroActivation: 'UNVERIFIED' }));
}
