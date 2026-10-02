/** Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 2 (KWP). */
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { load } from 'js-yaml';
import { semanticInventory } from './develop.mjs';

/** Inspected Kiro 1.1.28 Gpd/Hpd/Vpd subset, not its full filesystem/shell parser. */
export function compileRules(rules) {
  const quote = (value) => JSON.stringify(value.replace(/\*\*/g, '*'));
  const statements = [];
  for (const rule of rules) {
    const capabilities = rule.capability === 'filesystem' ? ['fs_read', 'fs_write'] : [rule.capability];
    const conditions = (rule.exclude ?? []).map((pattern) => `!(resource.path like ${quote(pattern)})`);
    if (rule.effect === 'ask') conditions.push('!(context has "asked" && context.asked)');
    const matches = !rule.match?.length || (rule.match.length === 1 && rule.match[0] === '*')
      ? [null] : rule.match.flatMap((pattern) => {
        const result = [`resource.path like ${quote(pattern)}`];
        if (pattern.endsWith(' *') && !/[*?]/.test(pattern.slice(0, -2))) {
          result.push(`resource.path == ${quote(pattern.slice(0, -2))}`);
        }
        return result;
      });
    for (const capability of capabilities) for (const match of matches) {
      const predicates = [...(match ? [match] : []), ...conditions];
      statements.push(`${rule.effect === 'allow' ? 'permit' : 'forbid'}(principal, action == Action::${JSON.stringify(capability)}, resource)`
        + (predicates.length ? ` when { ${predicates.join(' && ')} }` : '') + ';');
    }
  }
  return statements.join('\n');
}

// Operator supplies the already installed module. No install, process, network or policy write.
const [modulePath, ...policyPaths] = process.argv.slice(2);
if (!modulePath || !policyPaths.length) throw new Error('EXPECTED_INSTALLED_CEDAR_AND_POLICY_PATHS');
const cedar = createRequire(import.meta.url)(modulePath);
const rules = policyPaths.flatMap((path) => load(readFileSync(path, 'utf8')).rules);
const policies = { staticPolicies: compileRules(rules), templates: {}, templateLinks: [] };
const capabilities = ['shell', 'fs_read', 'fs_write', 'web_fetch', 'web_search', 'mcp', 'context', 'skill', 'subagent', 'diagnostics'];
for (const capability of capabilities) {
  const result = cedar.isAuthorizedPartial({ principal: { type: 'Agent', id: 'synthetic' },
    action: { type: 'Action', id: capability }, resource: null, context: {}, policies, entities: [] });
  if (result.type !== 'residuals' || result.response.errored.length) throw new Error('CEDAR_PARTIAL_FAILED_' + capability);
}
const probes = [
  ...semanticInventory().map(({ command }) => ['shell', command, 'allow']),
  ...['git commit -m synthetic', 'git push', 'git reset --hard',
    'docker run synthetic', 'npm install synthetic-package', 'gh pr create',
    'powershell -Command synthetic', 'curl.exe https://example.invalid',
    'node scripts/unknown.mjs'].map((command) => ['shell', command, 'deny']),
  ['shell', 'npm run typecheck', 'allow'],
  ['shell', 'npm test -- src/synthetic/new.test.ts', 'allow'],
  ['shell', 'node -e synthetic', 'deny'],
  ['shell', 'npm publish', 'deny'],
  ['shell', 'ssh synthetic-host', 'deny'],
  ['web_fetch', 'kiro.dev', 'allow'],
  ['web_fetch', 'example.invalid', 'deny'],
  ['subagent', 'synthetic-design', 'allow'],
  ['skill', 'synthetic-skill', 'allow'],
  ['mcp', 'synthetic-server/synthetic-tool', 'deny'],
];
for (const [capability, path, expected] of probes) {
  const resource = { type: 'Resource', id: 'synthetic' };
  const result = cedar.isAuthorized({ principal: { type: 'Agent', id: 'synthetic' },
    action: { type: 'Action', id: capability }, resource, context: {}, policies,
    entities: [{ uid: resource, attrs: { path }, parents: [] }] });
  if (result.type !== 'success' || result.response.diagnostics.errors.length
    || result.response.decision.toLowerCase() !== expected) throw new Error('CEDAR_DECISION_FAILED_' + capability);
}
console.log(JSON.stringify({ cedarPartialEvaluation: 'PASS', capabilities: capabilities.length,
  syntheticDecisions: probes.length, rules: rules.length,
  maxExclude: Math.max(0, ...rules.map((rule) => rule.exclude?.length ?? 0)),
  ideActivation: 'UNVERIFIED' }));
