/** Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 2 (KWP). */
import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, symlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { load } from 'js-yaml';
import {
  commandInventory, discoverTests, permissionPolicy, renderPolicy,
  DEVELOPMENT_COMMANDS, ROOT, OUTPUT, SHELL_PATTERNS, assertPatternBudget
} from './permissions.mjs';

const tests = discoverTests();
const commands = commandInventory(tests);
const policy = load(renderPolicy(commands));

// Glob fixture evaluator only. Never execute commands or emulate a shell parser.
function matches(pattern, command) {
  const expression = pattern.split('*').map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*');
  return new RegExp(`^${expression}$`, 's').test(command);
}
function effectFor(command, extraRules = []) {
  const effects = [...policy.rules, ...extraRules]
    .filter((rule) => ['shell', 'all'].includes(rule.capability))
    .filter((rule) => !rule.match || rule.match.some((pattern) => matches(pattern, command)))
    .filter((rule) => !rule.exclude?.some((pattern) => matches(pattern, command)))
    .map((rule) => rule.effect);
  return ['deny', 'ask', 'allow'].find((effect) => effects.includes(effect)) ?? 'ask';
}

test('500+ unique concrete commands from actual repository files, not wildcard padding', () => {
  assert.ok(commands.length >= 500);
  assert.equal(new Set(commands).size, commands.length);
  assert.equal(commands.length, tests.length * 3 + DEVELOPMENT_COMMANDS.length);
  assert.ok(commands.every((command) => !/[\n\r*?;$`|&<>]/.test(command)));
  for (const path of tests) {
    assert.ok(readFileSync(join(ROOT, path), 'utf8').length > 0);
    assert.ok(commands.includes(`npm test -- ${path}`));
    assert.ok(commands.includes(`npm test -- --run ${path}`));
    assert.ok(commands.includes(`node node_modules/vitest/vitest.mjs run ${path}`));
  }
});

test('deterministic inventory and YAML round-trip, bounded lists and disk template agree', () => {
  assert.deepEqual(commandInventory([...tests].reverse()), commands);
  assert.deepEqual(policy, permissionPolicy(commands));
  assert.deepEqual(policy.rules.filter((rule) => rule.capability === 'shell' && rule.effect === 'allow').flatMap((rule) => rule.match),
    policy.rules.find((rule) => rule.capability === 'shell' && rule.effect === 'ask').exclude);
  assert.ok(SHELL_PATTERNS.length < commands.length);
  assert.doesNotThrow(() => assertPatternBudget(policy));
  assert.throws(() => assertPatternBudget({ rules: [{ capability: 'shell', effect: 'ask', exclude: Array(557).fill('synthetic') }] }), /POLICY_PATTERN_BUDGET/);
  assert.equal(readFileSync(join(ROOT, OUTPUT), 'utf8'), renderPolicy(commands));
});

test('schema uses only supported capabilities, effects and rule fields', () => {
  const capabilities = new Set(['shell', 'fs_read', 'fs_write', 'filesystem', 'web_fetch', 'web_search', 'diagnostics', 'context', 'skill', 'subagent', 'mcp']);
  for (const rule of policy.rules) {
    assert.ok(capabilities.has(rule.capability));
    assert.ok(['allow', 'ask', 'deny'].includes(rule.effect));
    assert.ok(Object.keys(rule).every((key) => ['capability', 'effect', 'match', 'exclude'].includes(key)));
    for (const key of ['match', 'exclude']) {
      if (rule[key]) assert.ok(rule[key].length > 0 && rule[key].every((value) => typeof value === 'string'));
    }
  }
  assert.equal(policy.rules.find((rule) => rule.capability === 'mcp').effect, 'ask');
});

for (const command of commands) {
  test(`allow listed command: ${command}`, () => assert.equal(effectFor(command), 'allow'));
}

for (const command of [
  'npm publish', 'npm install synthetic-package', 'npm run start', 'npm run loop:auto',
  'npx synthetic-package', 'node -e synthetic', 'node scripts/unknown.mjs',
  'python -c synthetic', 'powershell -Command synthetic', 'bash -c synthetic',
  'cmd /c synthetic', 'ssh synthetic-host', 'cloudctl synthetic-operation',
  'curl https://example.invalid', 'npm test -- --config synthetic.config.ts',
  'npm test -- src/../synthetic.ts', 'npm test ; synthetic-command',
  'npm test && synthetic-command', 'npm test\nsynthetic-command',
  'npm test | synthetic-command', 'npm test > synthetic-file', 'npm test -- $(synthetic)',
  'node node_modules/vitest/vitest.mjs run synthetic.test.ts',
]) {
  test(`unlisted input asks even with inherited all-allow: ${JSON.stringify(command)}`, () => {
    assert.equal(effectFor(command, [{ capability: 'all', effect: 'allow' }]), 'ask');
  });
}

test('native/enterprise/session restrictions cannot be overridden by allow', () => {
  assert.equal(effectFor('npm test', [{ capability: 'shell', effect: 'ask' }]), 'ask');
  assert.equal(effectFor('npm test', [{ capability: 'shell', effect: 'deny' }]), 'deny');
});

test('file and web scopes do not silently permit arbitrary external writes/fetches', () => {
  const rules = (capability) => policy.rules.filter((rule) => rule.capability === capability);
  assert.deepEqual(rules('fs_write')[0].match, ['./src/**', './tests/**', './docs/**', './scripts/**', './.kiro/specs/**']);
  for (const capability of ['fs_read', 'fs_write', 'web_fetch']) {
    const [allow, ask] = rules(capability);
    assert.equal(allow.effect, 'allow');
    assert.equal(ask.effect, 'ask');
    assert.deepEqual(allow.match, ask.exclude);
  }
  const sensitive = rules('filesystem')[0];
  assert.equal(sensitive.effect, 'ask');
  for (const pattern of ['**/.env', '**/.env.*', '**/.secrets/**', '**/*.pem', '**/*.key', './data/**', './ops/**']) {
    assert.ok(sensitive.match.includes(pattern));
  }
});

test('unsafe, empty and duplicate inventory inputs fail closed', () => {
  for (const path of ['src/../x.test.ts', 'src/x.test.ts;echo', 'src/a b.test.ts',
    'src/$(x).test.ts', 'src/x\ny.test.ts', 'src/x*.test.ts', 'C:/src/x.test.ts',
    'src\\x.test.ts', 'src/x.ts', null, 1]) {
    assert.throws(() => commandInventory([path]), /UNSAFE_TEST_PATH/);
  }
  assert.throws(() => commandInventory([]), /EMPTY_TEST_INVENTORY/);
  assert.throws(() => commandInventory(['src/x.test.ts', 'src/x.test.ts']), /DUPLICATE_TEST_PATH/);
  for (const value of [[], ['*'], ['npm test', 'npm test'], ['npm test\nsynthetic-command'], [null]]) {
    assert.throws(() => permissionPolicy(value), /INVALID_COMMAND_INVENTORY/);
  }
});

test('discovery limits inventory to tests, rejects missing roots and directory junctions', () => {
  const tempRoot = join(homedir(), '.aki', 'tmp');
  mkdirSync(tempRoot, { recursive: true });
  const root = mkdtempSync(join(tempRoot, 'kiro-permission-tests-'));
  assert.throws(() => discoverTests(root), /ENOENT/);
  mkdirSync(join(root, 'src'));
  mkdirSync(join(root, 'src', 'unit'));
  writeFileSync(join(root, 'src', 'unit', 'x.test.ts'), '// synthetic fixture\n');
  writeFileSync(join(root, 'src', 'unit', 'ignored.ts'), '// not a test\n');
  assert.deepEqual(discoverTests(root), ['src/unit/x.test.ts']);
  symlinkSync(join(root, 'src', 'unit'), join(root, 'src', 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => discoverTests(root), /SYMLINK_ENTRY/);
});

// Phase 2 expands local development scope; existing negative coverage remains intact.
test('spec writing and delegation are allowed, host-based web matching is used', () => {
  const write = policy.rules.find((rule) => rule.capability === 'fs_write' && rule.effect === 'allow');
  assert.ok(write.match.includes('./.kiro/specs/**'));
  for (const capability of ['skill', 'subagent', 'context']) {
    assert.equal(policy.rules.find((rule) => rule.capability === capability).effect, 'allow');
  }
  const fetch = policy.rules.find((rule) => rule.capability === 'web_fetch' && rule.effect === 'allow');
  assert.ok(fetch.match.includes('kiro.dev'));
  assert.ok(fetch.match.every((host) => !host.includes('/')));
  assert.ok(!renderPolicy(commands).includes('&development_commands'));
});
