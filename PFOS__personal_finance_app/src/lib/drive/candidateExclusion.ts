/**
 * NIZAM · The single serialisation-time Drive projection — D-5 part 2 = (c)
 * Implemented by: repository build Contract 2 (Drive data layer) / Phase 2.7, under PFOS Contract 06
 *                 and Contract 6 §5 I5.2 (APPROVED). Owner decision D-5, recorded 2026-09-21.
 * Depends on: ../db/schema.ts (types only). Pure. No I/O, no key, no network.
 *
 * ## Why this file exists, in one sentence
 *
 * Contract 6 §5 **I5.2**: a candidate *"is not financial truth and MUST NOT be counted in any balance,
 * budget, forecast or report"* — and a candidate that has been mirrored to Drive has escaped the staging
 * boundary that clause creates.
 *
 * ## Why (c) and not (d), argued from the defect rather than from taste
 *
 * The owner chose **(c) a single serialisation-time projection** over **(d) per-call-site exclusion**. The
 * decisive evidence is what (d) had already produced in this very repository. At `sync.ts` the comment
 * read *"Candidates are device-local (they are unreviewed, not synced to Drive)"* — and **two lines
 * below it** sat `transactionCandidates: local.transactionCandidates`, inside the object that gets
 * serialised to Drive. The comment was true about MERGE semantics and false about EGRESS. It did not
 * merely fail to enforce the property; it actively misled a reader about code directly beneath it.
 *
 * That is what per-call-site convention decays into. So the exclusion here is not a step a caller
 * performs — it is a property of the TYPE that reaches Drive.
 *
 * ## How the type makes it unforgettable
 *
 * `DriveBoundPayload` carries a private brand that only `projectForDrive` can attach. `driveDb`'s
 * serialisation helper accepts that type and nothing else, so a caller CANNOT construct a Drive-bound
 * payload without going through the projection. A new upload path added by someone who never read this
 * file still cannot leak a candidate, because the alternative does not typecheck.
 *
 * ## What this module is NOT
 *
 * It is not encryption. D-5 part 1 = (a) WebCrypto is a separate module and a separate concern, and the
 * owner's binding condition 2 sequences them: this one needs no key and no gate, so it lands first and
 * completely. Encryption alone would not have fixed egress anyway — an encrypted payload still CONTAINS
 * the candidates, the owner's key decrypts them, and a future readable mirror would expose them.
 */
import type { NizamDb } from '../db/schema.ts';

declare const DRIVE_BOUND: unique symbol;

/**
 * The only shape that may be serialised to Drive.
 *
 * Structurally `NizamDb` minus staging, plus a brand that cannot be forged from outside this module.
 * The brand is the enforcement: a plain object literal, however carefully assembled, is not assignable
 * to this type, so `serialiseForDrive` cannot be called with an unprojected database.
 */
export type DriveBoundPayload = Omit<NizamDb, 'transactionCandidates'> & {
  readonly [DRIVE_BOUND]: true;
};

/** The staging key this projection exists to drop. Named once, so a rename cannot silently widen egress. */
export const EXCLUDED_STAGING_KEY = 'transactionCandidates' as const;

/**
 * Build the Drive-bound payload: everything except staging.
 *
 * Implemented as an explicit destructuring omission rather than a key allowlist, deliberately. An
 * allowlist would silently DROP any collection added to `NizamDb` later — which fails in the dangerous
 * direction, because a new canonical collection would stop being backed up and nothing would say so. An
 * omission fails in the safe direction: a new collection is carried to Drive, and only the one named key
 * is removed.
 */
export function projectForDrive(db: NizamDb): DriveBoundPayload {
  const { [EXCLUDED_STAGING_KEY]: _staging, ...rest } = db;
  return rest as DriveBoundPayload;
}

/**
 * Serialise a Drive-bound payload. The ONLY sanctioned path from a database to Drive-bound text.
 *
 * Takes `DriveBoundPayload`, so the projection has provably already happened. The indentation matches
 * what `driveDb` used before this module existed, so the on-Drive artifact shape is unchanged.
 */
export function serialiseForDrive(payload: DriveBoundPayload): string {
  return JSON.stringify(payload, null, 2);
}

/** Convenience for the common case: project, then serialise. */
export function serialiseDbForDrive(db: NizamDb): string {
  return serialiseForDrive(projectForDrive(db));
}

/**
 * The READ counterpart of `projectForDrive`, and the reason both live in this one file.
 *
 * ## The defect this exists to close
 *
 * `projectForDrive` removes `transactionCandidates`, but `zNizamDb` declares it REQUIRED with no
 * `.default()`, and the only code that ever filled it is the v5→v6 migration step. A projected artifact
 * is stamped `schemaVersion: 9`, so no migration step runs, and `validateDb` therefore threw on every
 * read of an artifact this module had written. Writing a field out without putting it back is an
 * asymmetric boundary, and an asymmetric boundary is a bug with two halves.
 *
 * Symmetry is the invariant:
 *
 *     project   : NizamDb -> DriveBoundPayload   (staging removed)
 *     rehydrate : raw     -> raw + staging: []   (staging restored as empty)
 *
 * ## Why `[]` is the honest value rather than a placeholder
 *
 * Staging is DEVICE-LOCAL. A remote artifact does not have "unknown" candidates whose value we are
 * guessing at — it genuinely has none, because candidates never travel. So `[]` is the true value on
 * read, not a default standing in for missing information.
 *
 * ## Why absence and presence are treated differently
 *
 * An ABSENT key is injected. A PRESENT key is left exactly as found, **even if it is malformed**, so that
 * `validateDb` still rejects a corrupt artifact. Coercing a present-but-invalid value would convert a
 * real corruption signal into silence, which is the failure mode this repository consistently refuses.
 */
export function rehydrateFromDrive(raw: unknown): unknown {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    // Not an object at all. Hand it on untouched so `migrate` and `validateDb` produce their own
    // diagnostics rather than one invented here.
    return raw;
  }
  const record = raw as Record<string, unknown>;
  // Present — including present-and-wrong — is left for validation to judge.
  if (EXCLUDED_STAGING_KEY in record) return raw;
  return { ...record, [EXCLUDED_STAGING_KEY]: [] };
}
