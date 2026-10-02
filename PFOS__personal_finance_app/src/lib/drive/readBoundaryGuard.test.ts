/**
 * Preventive read-side guard for the Drive database boundary.
 * Owning authority: repository build Contract 2 / Phase 2.7, under Contract 6 §5 I5.2 (APPROVED).
 * Rider: NIZAM-INC5-TAIL-008 item 3, executed by NIZAM-FINAL-009 work item B.
 *
 * PREVENTIVE, NOT A LIVE DEFECT FIX. Every production consumer of `downloadText` was enumerated before
 * this assertion was written. Only driveDb.ts constructs a NizamDb from downloaded text today, and it
 * already rehydrates before migration/validation. ImportWizard.tsx downloads a Picker-selected ledger
 * CSV and hands it to loadCsv; it never constructs a NizamDb and is legitimately exempt. Two further
 * call sites are tests: sync.test.ts parses remote bytes for an assertion, and moneyBoundary.test.ts
 * compares rejected bytes verbatim. Test-only reads cannot become a production database arrival path.
 *
 * Why source analysis is honest here. The write boundary is unforgeable through DriveBoundPayload's
 * private brand. The read boundary cannot brand raw external text, so the equivalent property is that
 * every production `downloadText` consumer which parses JSON into the database vocabulary must visibly
 * pass through `rehydrateFromDrive` before `migrate`/`validateDb`. This assertion fails closed on a new
 * database-shaped consumer and carries a negative fixture proving the failure mode.
 *
 * ALL FIXTURES BELOW ARE SYNTHETIC SOURCE STRINGS. They contain no real data, identifiers, hostnames,
 * Drive ids or deployment particulars.
 */
import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

type SourceFile = { readonly path: string; readonly source: string };

const ROOT = join('src');

function walk(path: string): string[] {
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) => {
    const child = join(path, entry.name);
    return entry.isDirectory() ? walk(child) : [child];
  });
}

function repoPath(path: string): string {
  return relative('.', path).split(sep).join('/');
}

function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1');
}

/**
 * Find production call sites where downloaded text participates in database construction without the
 * mandatory rehydration. This is intentionally narrower than "every download": CSV is not NizamDb and
 * a raw-byte assertion is not construction.
 */
export function databaseDownloadBypasses(files: readonly SourceFile[]): string[] {
  const findings: string[] = [];
  for (const file of files) {
    if (/\.test\.tsx?$/.test(file.path)) continue;
    const code = stripComments(file.source);
    if (!/\.downloadText\s*\(/.test(code)) continue;

    const parsesJson = /JSON\.parse\s*\(/.test(code);
    const namesDatabase = /\b(?:NizamDb|validateDb|migrate|rehydrateFromDrive|loadDb)\b/.test(code);
    const constructsDatabase = parsesJson && namesDatabase;
    if (!constructsDatabase) continue;

    // Construction is allowed only when the source text makes the data flow visible. The production
    // path uses nested calls — `migrate(rehydrateFromDrive(raw))` — where execution order is inside-out,
    // so lexical positions alone would invert the real order. Accept either that exact nesting or an
    // explicitly assigned rehydrated value which is then validated.
    const afterParse = code.slice(code.indexOf('JSON.parse'));
    const nestedGuard = /(?:migrate|validateDb)\s*\(\s*rehydrateFromDrive\s*\(/.test(afterParse);
    const assignedGuard = /(?:const|let)\s+\w+\s*=\s*rehydrateFromDrive\s*\([^;]+;[\s\S]*?(?:migrate|validateDb)\s*\(\s*\w+\s*\)/.test(afterParse);
    if (!nestedGuard && !assignedGuard) {
      findings.push(`${file.path}: database download is parsed without parse -> rehydrate -> validate ordering`);
    }
  }
  return findings;
}

function actualSources(): SourceFile[] {
  return walk(ROOT)
    .filter((path) => /\.tsx?$/.test(path))
    .map((path) => ({ path: repoPath(path), source: readFileSync(path, 'utf8') }));
}

function callSites(files: readonly SourceFile[]): string[] {
  return files
    // This test contains synthetic `.downloadText(...)` snippets as DATA for the negative fixtures. It
    // does not call the method. Exclude the fixture container rather than pretending those strings are
    // runtime call sites.
    .filter((file) => file.path !== 'src/lib/drive/readBoundaryGuard.test.ts')
    .filter((file) => /\.downloadText\s*\(/.test(stripComments(file.source)))
    .map((file) => file.path)
    .sort();
}

describe('preventive Drive database read-boundary guard', () => {
  it('the current production tree has no database download bypass', () => {
    expect(databaseDownloadBypasses(actualSources())).toEqual([]);
  });

  it('fails a new caller that downloads the database and parses it without rehydration', () => {
    const bypass = {
      path: 'src/lib/drive/syntheticBypass.ts',
      source: `
        import { migrate } from '../db/migrations.ts';
        import type { NizamDb } from '../db/schema.ts';
        export async function bypass(client: { downloadText(id: string): Promise<string> }): Promise<NizamDb> {
          const text = await client.downloadText('synthetic-id');
          return migrate(JSON.parse(text));
        }
      `,
    };
    expect(databaseDownloadBypasses([bypass])).toEqual([
      'src/lib/drive/syntheticBypass.ts: database download is parsed without parse -> rehydrate -> validate ordering',
    ]);
  });

  it('fails a caller that imports rehydration but validates before using it', () => {
    const wrongOrder = {
      path: 'src/lib/drive/syntheticWrongOrder.ts',
      source: `
        import { rehydrateFromDrive } from './candidateExclusion.ts';
        import { validateDb, type NizamDb } from '../db/schema.ts';
        export async function wrong(client: { downloadText(id: string): Promise<string> }): Promise<NizamDb> {
          const text = await client.downloadText('synthetic-id');
          const db = validateDb(JSON.parse(text));
          rehydrateFromDrive(db);
          return db;
        }
      `,
    };
    expect(databaseDownloadBypasses([wrongOrder])).toHaveLength(1);
  });

  it('accepts the required parse -> rehydrate -> migrate ordering', () => {
    const guarded = {
      path: 'src/lib/drive/syntheticGuarded.ts',
      source: `
        import { rehydrateFromDrive } from './candidateExclusion.ts';
        import { migrate } from '../db/migrations.ts';
        import type { NizamDb } from '../db/schema.ts';
        export async function load(client: { downloadText(id: string): Promise<string> }): Promise<NizamDb> {
          const text = await client.downloadText('synthetic-id');
          const raw: unknown = JSON.parse(text);
          return migrate(rehydrateFromDrive(raw));
        }
      `,
    };
    expect(databaseDownloadBypasses([guarded])).toEqual([]);
  });

  it('keeps ImportWizard legitimately exempt: it loads CSV and never constructs NizamDb', () => {
    const source = readFileSync(join('src', 'features', 'import', 'ImportWizard.tsx'), 'utf8');
    expect(source).toContain('downloadText(picked.id)');
    expect(source).toContain('loadCsv(picked.name, text)');
    expect(stripComments(source)).not.toMatch(/\b(?:NizamDb|validateDb|migrate|rehydrateFromDrive)\b/);
    expect(databaseDownloadBypasses([{ path: 'src/features/import/ImportWizard.tsx', source }])).toEqual([]);
  });

  it('enumerates every current src call site, including the two test-only reads', () => {
    const sites = callSites(actualSources());
    expect(sites).toEqual([
      'src/features/import/ImportWizard.tsx',
      'src/lib/db/moneyBoundary.test.ts',
      'src/lib/drive/driveDb.ts',
      'src/lib/drive/sync.test.ts',
    ]);
  });

  it('does not mistake a compile-time `as NizamDb` test assertion for runtime construction', () => {
    const source = readFileSync(join('src', 'lib', 'drive', 'sync.test.ts'), 'utf8');
    expect(source).toContain('as NizamDb');
    // Test files are explicitly out of the production arrival-path analysis.
    expect(databaseDownloadBypasses([{ path: 'src/lib/drive/sync.test.ts', source }])).toEqual([]);
  });

  it('keeps the rejected-evidence byte-comparison test exempt', () => {
    const source = readFileSync(join('src', 'lib', 'db', 'moneyBoundary.test.ts'), 'utf8');
    expect(source).toContain('downloadText(file.id)).toBe(text)');
    expect(databaseDownloadBypasses([{ path: 'src/lib/db/moneyBoundary.test.ts', source }])).toEqual([]);
  });
});
