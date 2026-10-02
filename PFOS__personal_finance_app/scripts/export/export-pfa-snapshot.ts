#!/usr/bin/env node
/**
 * NIZAM / PFOS -> MAL/Zayd PFA snapshot export (read-only)
 * Added: 2026-10-02, ADR-ZAYD-001 (NIZAM__system/docs/ADR-ZAYD-001-pfos-engine-into-mal-zayd.md)
 *
 * Standalone CLI, NOT part of the governed src/server/** barrel and not imported by it. It opens
 * the finance store the same way src/server/process/financeAgent.ts does (via openFinanceStore,
 * the single factory contract 06 requires), reads three repositories, and prints one JSON object
 * on stdout shaped like NIZAM__system/schemas/pfa_canonical_state.schema.json (v2, milliunits).
 *
 * It calls NO write method on any repository. It is the "sync from PFOS" half of MAL/Zayd's v2
 * update routine (MAL__financial_engine/pfa/README.md); the Python half
 * (MAL__financial_engine/pfa/sync_from_pfos.py) invokes this script as a subprocess and consumes
 * its stdout.
 *
 * Every PFOS Money value is ALREADY an integer milliunit (contract 06's schema_meta records
 * money_base = 'milliunits') -- this script does no unit conversion anywhere. It only renames
 * fields to the *_milliunits convention pfa_canonical_state.schema.json v2 expects.
 *
 * Config is explicit CLI flags, never ambient process.env, matching this tier's own rule that
 * nothing reads the environment except the one bridge in src/server/config/environment.ts --
 * this script is outside that tier and does not use that bridge, so it takes its own explicit
 * input instead of inventing a second ambient-read path.
 *
 * Two shape fixes made against the real schema and repositories (not guessed):
 *   1. pfa_canonical_state.schema.json's debt_entry.id requires pattern ^[a-z0-9_]+$. PFOS's
 *      default id generator is randomUUID() (support.ts), which contains hyphens. toSchemaId()
 *      below maps hyphens to underscores so exported ids validate; the original PFOS id is kept
 *      verbatim in each entry's `source_id` for traceability back to the row it came from.
 *   2. The schema's income.stable_net_monthly_milliunits is a required non-nullable integer (no
 *      null in its type union). PFOS has no transactionsRepository-based income rollup wired up
 *      in this first cut, so the honest move is 0 plus a loud provenance.open_items entry, not a
 *      schema-breaking null and not an invented figure.
 *
 * Fails closed: a missing required flag, an unreachable data directory, or a store that refuses
 * to open all exit 1 with a message naming what was wrong. There is no fallback location and no
 * default -- the same rule src/server/db/paths.ts enforces for the real server process.
 */
import { openFinanceStore } from '../../src/server/db/store.ts';
import { createRepositoryContext } from '../../src/server/db/repositories/support.ts';
import { createAccountsRepository } from '../../src/server/db/repositories/accountsRepository.ts';
import { createObligationsRepository } from '../../src/server/db/repositories/obligationsRepository.ts';
import { createFxRatesRepository } from '../../src/server/db/repositories/fxRatesRepository.ts';
import { isCreditType, type AccountType } from '../../src/features/accounts/accounts.types.ts';

interface Cli {
  readonly dataDir: string;
  readonly fileName: string;
  readonly storeName: string;
  readonly asOf: string;
}

function parseArgs(argv: readonly string[]): Cli {
  const get = (flag: string): string | undefined => {
    const i = argv.indexOf(flag);
    return i >= 0 ? argv[i + 1] : undefined;
  };
  const dataDir = get('--data-dir');
  const fileName = get('--file-name');
  const storeName = get('--store-name') ?? 'finance-agent';
  const asOf = get('--as-of') ?? new Date().toISOString().slice(0, 10);
  const missing: string[] = [];
  if (!dataDir) missing.push('--data-dir');
  if (!fileName) missing.push('--file-name');
  if (missing.length > 0) {
    throw new Error(
      `export-pfa-snapshot: missing required flag(s): ${missing.join(', ')}. ` +
        'Usage: export-pfa-snapshot --data-dir <abs path> --file-name <finance.db> [--store-name <name>] [--as-of YYYY-MM-DD]',
    );
  }
  return { dataDir: dataDir!, fileName: fileName!, storeName, asOf };
}

/** debt_entry.id must match ^[a-z0-9_]+$. randomUUID() ids have hyphens; map them to underscores. */
function toSchemaId(rawId: string): string {
  return rawId.toLowerCase().replace(/[^a-z0-9_]/g, '_');
}

/** Best-effort PFOS Account -> MAL debt-type classification. Only credit-type accounts qualify. */
function debtTypeForAccount(type: AccountType): 'credit_card' {
  if (!isCreditType(type)) {
    throw new Error(`debtTypeForAccount called on a non-credit account type: ${type}`);
  }
  return 'credit_card';
}

/**
 * Best-effort PFOS Obligation.kind -> MAL debt-type classification. `kind` is free text at the
 * DB layer (obligationsRepository.ts: "kind: string", no enum), so this is a heuristic over
 * substrings, not a lookup table over a closed vocabulary. Anything unmatched falls to `other`
 * and is listed in provenance.open_items so it is visible, never silently guessed into a bucket.
 */
function debtTypeForObligationKind(kind: string): {
  type: 'bnpl_installment' | 'family_loan' | 'personal_loan' | 'other';
  matched: boolean;
} {
  const k = kind.toLowerCase();
  if (k.includes('bnpl') || k.includes('installment')) return { type: 'bnpl_installment', matched: true };
  if (k.includes('family')) return { type: 'family_loan', matched: true };
  if (k.includes('personal_loan') || k.includes('personal loan')) return { type: 'personal_loan', matched: true };
  return { type: 'other', matched: false };
}

function obligationStatusToDebtStatus(
  status: string,
): 'active' | 'paid_off' | 'restructured' | 'deferred' {
  switch (status) {
    case 'paid':
      return 'paid_off';
    case 'skipped':
      return 'deferred';
    case 'scheduled':
    case 'overdue':
    default:
      return 'active';
  }
}

function main(): void {
  const cli = parseArgs(process.argv.slice(2));
  const opened = openFinanceStore({
    dataDir: cli.dataDir,
    fileName: cli.fileName,
    storeName: cli.storeName,
    busyTimeoutMs: 5_000,
  });
  const openItems: string[] = [];

  try {
    const ctx = createRepositoryContext({ handle: opened.handle, actor: 'zayd-pfa-sync-readonly' });
    const accounts = createAccountsRepository(ctx);
    const obligations = createObligationsRepository(ctx);
    const fxRates = createFxRatesRepository(ctx);

    const accountRows = accounts.list({ includeClosed: false });
    const obligationRows = obligations.list();
    const rate = fxRates.latest('EGP', 'USD', cli.asOf);

    const debts: unknown[] = [];

    for (const a of accountRows) {
      if (!isCreditType(a.type)) continue;
      debts.push({
        id: toSchemaId(a.id),
        source_id: a.id,
        name: a.name,
        type: debtTypeForAccount(a.type),
        recycling_eligible: false, // PFOS's Account row has no arrears/clean-period field yet (see open_items below) -- default to the conservative "not eligible" rather than guess.
        credit_limit_milliunits: a.creditLimit,
        current_balance_milliunits: a.balance,
        available_credit_milliunits:
          a.creditLimit !== null ? a.creditLimit - Math.max(a.balance, 0) : null,
        status: a.closed ? 'paid_off' : 'active',
        as_of_date: cli.asOf,
        source: 'PFOS_engine',
        pfos_updated_at: a.updatedAt, // stable per-row change timestamp from PFOS, used as the ts input to the ledger idempotency_key (sha256(ts+debt_id+event_type)) so a resync that finds no PFOS-side change recomputes the SAME key and appends nothing twice.
        notes:
          'recycling_eligible defaulted false: PFOS Account rows do not yet carry an arrears/clean-period field to confirm eligibility against the underlying "current, under limit, 30+ days clean" rule. Confirm manually.',
      });
      openItems.push(`account:${a.id} recycling_eligible defaulted false, needs manual confirmation`);
    }

    for (const o of obligationRows) {
      const classified = debtTypeForObligationKind(o.kind);
      if (!classified.matched) {
        openItems.push(`obligation:${o.id} kind="${o.kind}" did not match a known debt-type pattern, filed as "other"`);
      }
      debts.push({
        id: toSchemaId(o.id),
        source_id: o.id,
        name: o.name,
        type: classified.type,
        recycling_eligible: false,
        installment_monthly_milliunits: o.minimumAmount,
        original_amount_milliunits: o.amount,
        due_date: o.dueDate,
        status: obligationStatusToDebtStatus(o.status),
        arrears_status: o.status === 'overdue' ? 'OVERDUE' : null,
        as_of_date: cli.asOf,
        source: 'PFOS_engine',
        pfos_updated_at: o.updatedAt, // same idempotency rationale as the account branch above.
        notes: null,
      });
    }

    const totalOutstanding = debts.reduce((sum: number, d) => {
      const row = d as { current_balance_milliunits?: number | null; original_amount_milliunits?: number | null };
      return sum + (row.current_balance_milliunits ?? row.original_amount_milliunits ?? 0);
    }, 0);

    if (rate === null) {
      openItems.push('fx_rates: no EGP/USD rate on or before as_of -- exchange_rate fields left null');
    }

    openItems.push(
      'income.stable_net_monthly_milliunits set to 0 placeholder: not yet derivable from accounts/obligations alone, needs a transactionsRepository-based income rollup (out of scope for this first export, tracked, not estimated).',
    );

    const snapshot = {
      source_of_truth: {
        engine: 'PFOS',
        storeRef: `${cli.dataDir}/${cli.fileName}`,
        schemaVersion: '2.0.0',
        projectedAt: new Date().toISOString(),
        sourceAuditVersion: null,
      },
      snapshot_date: cli.asOf,
      currency: 'EGP_and_USD',
      exchange_rate:
        rate === null
          ? { egp_per_usd: null, rate_verified: false, rate_sources: [], rate_date: cli.asOf }
          : {
              egp_per_usd: rate.rateNum / rate.rateDen,
              rate_verified: true,
              rate_sources: [
                `PFOS fx_rates row ${rate.id} (integer pair ${rate.rateNum}/${rate.rateDen}, never a float applied to money -- contract 06 section 4.4)`,
              ],
              rate_date: cli.asOf,
            },
      income: {
        stable_net_monthly_milliunits: 0,
      },
      debt_architecture: {
        summary: {
          total_outstanding_milliunits: totalOutstanding,
          total_monthly_obligations_milliunits: null,
          recycling_eligible_limit_milliunits: 0,
          debt_to_income_ratio: null,
        },
        debts,
      },
      cash_flow: {
        monthly_income_milliunits: 0,
      },
      provenance: {
        last_updated: new Date().toISOString(),
        update_method: 'pfos_engine_sync',
        figures_source: 'PFOS_engine',
        open_items: openItems,
      },
      privacy_level: 'strict_local',
    };

    process.stdout.write(JSON.stringify(snapshot, null, 2) + '\n');
  } finally {
    opened.handle.close();
  }
}

main();
