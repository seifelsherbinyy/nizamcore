/**
 * NIZAM · S5 account and currency resolution — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S5)
 * Depends on: ./pipeline.types.ts, ../../lib/money/currency.ts. Pure, no I/O, no registry.
 *
 * ## Two resolutions that must never learn about each other
 *
 * CURRENCY IS NEVER INFERRED FROM THE ACCOUNT. That is the single most important property in this file,
 * and it is enforced STRUCTURALLY rather than by a comment: `resolveCurrency` does not take an account,
 * an accountId, or the resolution context's alias list. It cannot consult them because it is not given
 * them. An EGP account can receive a USD charge, and a store that assumes otherwise silently misstates
 * both the amount and the exposure.
 *
 * ## Why the alias list is an ARRAY and not a Map
 *
 * A `Map` cannot represent a duplicated alias — the second write wins and the ambiguity disappears
 * before anyone can refuse it. An array preserves the duplicate, so "matches two accounts" is
 * observable. Both failures then collapse into ONE refusal:
 *
 *   zero matches   -> ACCOUNT_ALIAS_UNRESOLVED
 *   many matches   -> ACCOUNT_ALIAS_UNRESOLVED
 *
 * They are the same refusal because neither identifies an account, and the remedy for both is the same
 * question to the owner. There is no "the usual account", no most-recently-used fallback, and nothing
 * carried over from a previous line or a previous day.
 *
 * ## Case folding is not inference
 *
 * `egp` -> `EGP` cannot produce a DIFFERENT currency, so folding is safe. Substituting a missing code
 * with the base currency WOULD produce a different one, so it is refused instead.
 */
import { CURRENCY_CODE_PATTERN, type CurrencyCode } from '../../lib/money/currency.ts';
import {
  type NormalizedRow,
  type ResolvedRow,
  type StageResult,
  err,
  ok,
  refuse,
} from './pipeline.types.ts';

/** One alias the caller resolved from the sources that actually declare it. Not a stored registry. */
export interface AccountAlias {
  readonly alias: string;
  readonly accountId: string;
}

/**
 * Resolution input. Supplied per call by the caller, per Contract 15 §10.3 — deliberately NOT a module
 * level singleton, so two callers cannot disagree about what is resolvable.
 */
export interface ResolutionContext {
  /** An array, so a duplicated alias survives to be refused. */
  readonly accountAliases: readonly AccountAlias[];
  /** Currencies the store knows. A code outside this set is refused, never coerced. */
  readonly knownCurrencies: readonly CurrencyCode[];
}

/**
 * Resolve an alias to exactly one account id, or nothing.
 *
 * Returns `null` for both zero and many, because the caller must treat them identically and giving it
 * the count would invite it to "pick the first one".
 */
export function resolveAccountId(
  aliasRaw: string,
  aliases: readonly AccountAlias[],
): string | null {
  const wanted = aliasRaw.trim().toLowerCase();
  if (wanted === '') return null;
  const matches = aliases.filter((entry) => entry.alias.trim().toLowerCase() === wanted);
  return matches.length === 1 ? matches[0]!.accountId : null;
}

/**
 * Resolve a currency token against the set the store knows.
 *
 * Takes NO account parameter. That absence is the guarantee.
 */
export function resolveCurrency(
  currencyRaw: string,
  knownCurrencies: readonly CurrencyCode[],
): { readonly kind: 'missing' } | { readonly kind: 'unknown' } | { readonly kind: 'ok'; readonly currency: CurrencyCode } {
  const token = currencyRaw.trim();
  if (token === '' || !/^[A-Za-z]{3}$/u.test(token)) return { kind: 'missing' };
  const folded = token.toUpperCase();
  if (!CURRENCY_CODE_PATTERN.test(folded) || !knownCurrencies.includes(folded)) {
    return { kind: 'unknown' };
  }
  return { kind: 'ok', currency: folded };
}

/** S5. Bind the row to a store account and a store currency, or refuse it. */
export function resolveRow(row: NormalizedRow, ctx: ResolutionContext): StageResult<ResolvedRow> {
  const at = row.rowRef;

  const accountId = resolveAccountId(row.accountAliasRaw, ctx.accountAliases);
  if (accountId === null) return err(refuse('ACCOUNT_ALIAS_UNRESOLVED', at));

  const currency = resolveCurrency(row.currencyRaw, ctx.knownCurrencies);
  if (currency.kind === 'missing') return err(refuse('CURRENCY_MISSING', at));
  if (currency.kind === 'unknown') return err(refuse('CURRENCY_UNKNOWN', at));

  return ok(Object.freeze({ ...row, accountId, currency: currency.currency }));
}
