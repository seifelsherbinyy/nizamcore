/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE03). */
import { lstatSync, readFileSync, readdirSync, realpathSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
export const AUTHORITY = 'contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md';
const ID = /^nizam-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const nonempty = (value, max = 1024) => typeof value === 'string' && value.trim().length > 0 && value.length <= max;
const shape = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join('|') === [...keys].sort().join('|');

/** Restrict reads to simple repository-relative paths, with no symlink components. */
export function localFile(root, relative) {
  if (typeof relative !== 'string' || !/^[a-zA-Z0-9_./-]+$/.test(relative)
    || relative.split('/').some((part) => !part || part === '.' || part === '..')) throw new Error('INVALID_PATH');
  let path = realpathSync(root);
  for (const part of relative.split('/')) {
    path = join(path, part);
    if (lstatSync(path).isSymbolicLink()) throw new Error('SYMLINK_PATH');
  }
  if (!lstatSync(path).isFile()) throw new Error('NOT_FILE');
  return path;
}

/** Our single-line scalar subset, not a general YAML parser. */
export function skillMetadata(text) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(text);
  if (!match) throw new Error('FRONTMATTER');
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = /^(name|description|compatibility): (.+)$/.exec(line);
    if (!field || Object.hasOwn(fields, field[1])) throw new Error('METADATA_FIELD');
    fields[field[1]] = field[2].startsWith('"') ? JSON.parse(field[2]) : field[2];
  }
  if (!shape(fields, ['name', 'description', 'compatibility']) || !ID.test(fields.name)
    || fields.name.length > 64 || !nonempty(fields.description) || !nonempty(fields.compatibility)) throw new Error('METADATA_VALUE');
  if (text.split('\n').length > 150 || !text.includes('## Workflow')) throw new Error('SKILL_BODY');
  return fields;
}

export function validateRegistry(registry, readLocal) {
  const findings = [];
  if (!shape(registry, ['schemaVersion', 'authority', 'phase', 'capabilities'])
    || registry.schemaVersion !== 1 || registry.authority !== AUTHORITY || registry.phase !== 'KDE1'
    || !Array.isArray(registry.capabilities) || !registry.capabilities.length || registry.capabilities.length > 50) return ['REGISTRY_SCHEMA'];
  try { if (!readLocal(AUTHORITY).trim()) findings.push('AUTHORITY_EMPTY'); } catch { findings.push('AUTHORITY_MISSING'); }
  const ids = new Set();
  const descriptions = new Set();
  for (const row of registry.capabilities) {
    if (!shape(row, ['id', 'kind', 'path', 'references', 'status', 'activation', 'positive', 'negative'])
      || typeof row.id !== 'string' || !ID.test(row.id) || row.id.length > 64 || row.kind !== 'skill'
      || row.path !== `.kiro/skills/${row.id}/SKILL.md` || row.status !== 'CONFIGURED'
      || row.activation !== 'UNVERIFIED' || !nonempty(row.positive) || !nonempty(row.negative)
      || row.positive === row.negative || !Array.isArray(row.references) || !row.references.length
      || row.references.length > 10 || new Set(row.references).size !== row.references.length) {
      findings.push('CAPABILITY_SCHEMA'); continue;
    }
    if (ids.has(row.id)) findings.push('DUPLICATE_ID');
    ids.add(row.id);
    try {
      const text = readLocal(row.path);
      const meta = skillMetadata(text);
      if (meta.name !== row.id) findings.push('SKILL_NAME');
      if (descriptions.has(meta.description)) findings.push('DUPLICATE_DESCRIPTION');
      descriptions.add(meta.description);
      if (!text.includes(AUTHORITY) || !text.includes('Phase 1')) findings.push('SKILL_OWNERSHIP');
      if (!text.includes(row.positive) || !text.includes(row.negative)) findings.push('TRIAL_PROMPTS');
      for (const ref of row.references) {
        if (typeof ref !== 'string' || !/^docs\/kiro\/references\/[a-z-]+\.md$/.test(ref)) {
          findings.push('REFERENCE_PATH'); continue;
        }
        if (!text.includes(ref) || !readLocal(ref).trim()) findings.push('REFERENCE_CONTENT');
      }
    } catch { findings.push('SKILL_OR_REFERENCE_INVALID'); }
  }
  return findings;
}

export function validateWorkspace(root = ROOT) {
  try {
    const read = (path) => {
      const file = localFile(root, path);
      if (lstatSync(file).size > 100_000) throw new Error('FILE_TOO_LARGE');
      return readFileSync(file, 'utf8');
    };
    const registry = JSON.parse(read('docs/kiro/capability-registry.json'));
    const findings = validateRegistry(registry, read);
    if (findings.length) return findings;
    const folders = readdirSync(join(root, '.kiro/skills')).sort();
    if (folders.join('|') !== registry.capabilities.map((row) => row.id).sort().join('|')) findings.push('SKILL_INVENTORY');
    return findings;
  } catch { return ['WORKSPACE_INPUT_INVALID']; }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const findings = process.argv.length === 2 ? validateWorkspace() : ['UNSUPPORTED_ARGUMENTS'];
  console.log(JSON.stringify({ structuralValidation: findings.length ? 'FAIL' : 'PASS', findings, kiroActivation: 'UNVERIFIED' }));
  process.exitCode = findings.length ? 1 : 0;
}
