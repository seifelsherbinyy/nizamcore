/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 2 (KDE03/05/08). */
import { lstatSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { AUTHORITY, ROOT, localFile } from './validate.mjs';

export const RESEARCH_PATH = 'docs/kiro/operational-excellence/phase-2-evidence.json';
const DOMAINS = 'ABCDEFGHIJKLMNOPQ'.split('');
const REPOSITORY = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const text = (v, max = 2000) => typeof v === 'string' && v.trim().length > 0 && v.length <= max;
const shape = (v, keys) => v !== null && typeof v === 'object' && !Array.isArray(v)
  && Object.keys(v).sort().join('|') === [...keys].sort().join('|');
const list = (v, max) => Array.isArray(v) && v.length > 0 && v.length <= max;
const unique = (v) => new Set(v).size === v.length;
const repo = (v) => typeof v === 'string' && REPOSITORY.test(v) && v.length <= 200
  && !v.split('/').some((part) => part === '.' || part === '..');

function sourceUrl(value, repository) {
  if (!text(value, 1000)) return false;
  try {
    const url = new URL(value);
    const prefix = url.hostname === 'api.github.com' ? `/repos/${repository}/` : `/${repository}/`;
    return url.protocol === 'https:' && ['github.com', 'raw.githubusercontent.com', 'api.github.com'].includes(url.hostname)
      && !url.username && !url.password && !url.port && !url.search && !url.hash
      && (url.pathname + '/').startsWith(prefix) && url.href === value;
  } catch { return false; }
}

function validSource(row) {
  return shape(row, ['id', 'repository', 'kind', 'url', 'retrievedAt', 'sha256', 'excerpt', 'locator'])
    && typeof row.id === 'string' && /^S\d{3}$/.test(row.id) && repo(row.repository)
    && ['readme', 'source', 'package', 'license', 'security', 'issue', 'advisory', 'release', 'metadata', 'ci', 'docs'].includes(row.kind)
    && sourceUrl(row.url, row.repository)
    && typeof row.retrievedAt === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(row.retrievedAt)
    && Number.isFinite(Date.parse(row.retrievedAt)) && new Date(row.retrievedAt).toISOString() === row.retrievedAt
    && typeof row.sha256 === 'string' && /^[a-f0-9]{64}$/.test(row.sha256)
    && text(row.excerpt, 1200) && text(row.locator, 200);
}

function validCandidate(row) {
  return shape(row, ['repository', 'domains', 'depth', 'disposition', 'sources', 'nativeAlternative', 'reason', 'nextAction', 'execution', 'kiroActivation'])
    && repo(row.repository) && list(row.domains, 17) && unique(row.domains) && row.domains.every((id) => DOMAINS.includes(id))
    && ['SCREENED', 'ASSESSED', 'UNRESOLVED'].includes(row.depth)
    && ['REUSE_EXISTING', 'CONDITIONAL_TRIAL', 'PATTERN_ONLY', 'DEFER', 'REJECT_FOR_NOW', 'UNRESOLVED'].includes(row.disposition)
    && Array.isArray(row.sources) && row.sources.length <= 50 && unique(row.sources)
    && row.sources.every((id) => typeof id === 'string' && /^S\d{3}$/.test(id))
    && (row.depth === 'UNRESOLVED' ? row.disposition === 'UNRESOLVED' && row.sources.length === 0
      : row.disposition !== 'UNRESOLVED' && row.sources.length > 0)
    && text(row.nativeAlternative) && text(row.reason) && text(row.nextAction)
    && row.execution === 'NOT_RUN' && row.kiroActivation === 'NOT_TESTED';
}

/** Structural consistency only. This never establishes source truth or operational readiness. */
export function validateResearch(value) {
  if (!shape(value, ['schemaVersion', 'authority', 'phase', 'sources', 'candidates'])
    || value.schemaVersion !== 1 || value.authority !== AUTHORITY || value.phase !== 'RESEARCH2'
    || !list(value.sources, 500) || !list(value.candidates, 150)) return ['RESEARCH_SCHEMA'];
  const findings = [];
  const sources = new Map();
  for (const row of value.sources) {
    if (!validSource(row)) { findings.push('SOURCE_SCHEMA'); continue; }
    if (sources.has(row.id)) findings.push('DUPLICATE_SOURCE');
    sources.set(row.id, row.repository.toLowerCase());
  }
  const repositories = new Set();
  const covered = new Set();
  const cited = new Set();
  for (const row of value.candidates) {
    if (!validCandidate(row)) { findings.push('CANDIDATE_SCHEMA'); continue; }
    const identity = row.repository.toLowerCase();
    if (repositories.has(identity)) findings.push('DUPLICATE_CANDIDATE');
    repositories.add(identity);
    let evidenceValid = row.sources.length > 0;
    for (const id of row.sources) {
      cited.add(id);
      if (sources.get(id) !== identity) { findings.push('CITATION_INVALID'); evidenceValid = false; }
    }
    if (evidenceValid) row.domains.forEach((id) => covered.add(id));
  }
  if (DOMAINS.some((id) => !covered.has(id))) findings.push('DOMAIN_COVERAGE');
  if ([...sources.keys()].some((id) => !cited.has(id))) findings.push('ORPHAN_SOURCE');
  return [...new Set(findings)];
}

export function validateResearchWorkspace(root = ROOT) {
  try {
    const file = localFile(root, RESEARCH_PATH);
    if (lstatSync(file).size > 2_000_000) return ['RESEARCH_TOO_LARGE'];
    return validateResearch(JSON.parse(readFileSync(file, 'utf8')));
  } catch { return ['RESEARCH_INPUT_INVALID']; }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const findings = process.argv.length === 2 ? validateResearchWorkspace() : ['UNSUPPORTED_ARGUMENTS'];
  console.log(JSON.stringify({ structuralValidation: findings.length ? 'FAIL' : 'PASS', findings,
    externalExecution: 'NOT_RUN', kiroActivation: 'NOT_TESTED' }));
  process.exitCode = findings.length ? 1 : 0;
}
