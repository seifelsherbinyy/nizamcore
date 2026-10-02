/**
 * Bidirectional isolation for right-to-left companion text.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1), task NIZAM-SLACK-FINANCE-007 track_t.
 *
 * Why this exists. Right-to-left text commonly embeds Latin-script or numeric runs, and both flow
 * left-to-right inside the overall right-to-left flow, so the display order of an un-isolated mixed
 * string is resolved from surrounding context rather than from the author's intent. The remedy named by
 * the standards guidance is an isolating construct: U+2066 LEFT-TO-RIGHT ISOLATE and U+2069 POP
 * DIRECTIONAL ISOLATE around the embedded run.
 *
 * Evidence: docs/kiro/operational-excellence/slack-finance-evidence.json, claims C019-C022 and C051.
 * The isolate code points U+2066 and U+2069 are ASSESSED at S040 (W3C "bidi Unicode controls"), and the
 * numerals-in-RTL hazard at S039 (W3C "inline bidi markup"). Source ids are positional and shift when
 * the artifact is reassembled, which is why each is named as well as numbered.
 *
 * This inserts ONLY Unicode bidi control characters. It never inserts content, so it is not an
 * interpolation of money, an identifier or native text into a closed string. The closed question set
 * in dailyMessages.ts is not mutated: this returns a new display string.
 */

/** U+2066 LEFT-TO-RIGHT ISOLATE. */
export const LRI = '\u2066';
/** U+2067 RIGHT-TO-LEFT ISOLATE. */
export const RLI = '\u2067';
/** U+2068 FIRST STRONG ISOLATE. */
export const FSI = '\u2068';
/** U+2069 POP DIRECTIONAL ISOLATE. */
export const PDI = '\u2069';

/** Any isolate initiator. Presence means the string is already isolated and must be left alone. */
const ALREADY_ISOLATED = /[\u2066\u2067\u2068]/;

/**
 * A maximal left-to-right run: Latin letters and ASCII digits, allowing an internal separator only
 * between two alphanumerics so a trailing period at the end of an Arabic sentence is not swallowed
 * into the isolate.
 */
const LTR_RUN_SOURCE = '[A-Za-z0-9]+(?:[._\\-/][A-Za-z0-9]+)*';
const LTR_RUN = new RegExp(LTR_RUN_SOURCE, 'g');
/**
 * A separate NON-global instance for predicate use. `RegExp.prototype.test` on a global regex advances
 * lastIndex, so reusing LTR_RUN for a predicate would make repeated calls on the same input alternate
 * between true and false.
 */
const LTR_RUN_PROBE = new RegExp(LTR_RUN_SOURCE);

/**
 * Wrap every left-to-right run in a right-to-left string with LRI ... PDI.
 *
 * Idempotent by refusal rather than by re-parsing: if the input already carries any isolate
 * initiator it is returned unchanged, because double-wrapping changes resolved display order and a
 * silent second pass is a rendering defect that no assertion on visible characters would catch.
 */
export function isolateLtrRuns(text: string): string {
  if (ALREADY_ISOLATED.test(text)) return text;
  return text.replace(LTR_RUN, (run) => `${LRI}${run}${PDI}`);
}

/**
 * Apply isolation only where the base direction makes it necessary. English text needs none: its
 * base direction already matches its Latin runs, and adding controls there would be noise that
 * every downstream length check would then have to account for.
 */
export function forLocale(text: string, locale: 'en' | 'ar'): string {
  return locale === 'ar' ? isolateLtrRuns(text) : text;
}

/** Strip every isolate control. For assertions and for length budgeting against a transport limit. */
export function stripIsolates(text: string): string {
  return text.replace(/[\u2066\u2067\u2068\u2069]/g, '');
}

/**
 * True when a right-to-left string carries a left-to-right run that is not isolated. This is the
 * defect detector: the Arabic MAL_PFOS question in dailyMessages.ts embeds the Latin run "PFOS" and
 * is reported by this predicate today.
 */
export function hasUnisolatedLtrRun(text: string): boolean {
  if (ALREADY_ISOLATED.test(text)) return false;
  return LTR_RUN_PROBE.test(stripIsolates(text));
}
