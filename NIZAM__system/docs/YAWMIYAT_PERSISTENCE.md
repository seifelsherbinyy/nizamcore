# YAWMIYAT — Persistence & Recovery Architecture

> Owner contract: NIZAM-YAWMIYAT-PERSISTENCE v1 (this doc) + NIZAM_CONVERSATIONAL_LAYER.md.
> Lineage, strictly preserved on every artifact:

```
raw transcript ─► canonical session ─► human journal ─► biometrics/enrichment
      ─► assessment ─► evaluation ─► analysis ─► longitudinal indexes
```

Every artifact shares ONE immutable **session_id** (`YWM-YYYYMMDD-HHMMSS-type-XXXX`)
and cross-references its sources. The raw verbatim transcript is NEVER rewritten.

## Directory layout (all under `YAWMIYAT__journaling/`)

| Path | Kind | HIMAYAH class | Drive mirror |
|---|---|---|---|
| `transcripts/{sid}.txt` | raw verbatim human transcript | `strict_local_drive` | yes (read-back verified) |
| `transcripts/{sid}.utterances.json` | raw machine capture (timestamped utterances, literal) | `strict_local_drive` | no (VPS only) |
| `sessions/{sid}.json` | canonical machine record (committed on human confirm) | `strict_local` | no |
| `mirrors/{sid}.md` | human journal | `strict_local_drive` | yes (read-back verified) |
| `analysis/{sid}.v{n}.json` | versioned enrichment + evaluation + analysis | `strict_local` | no |
| `_retrieval/MANIFEST.json` | per-artifact sha256 (tamper detection) | `strict_local_drive` | yes |
| `_retrieval/INDEX.json` | inverted index (date/topic/person/entity/pattern) | `strict_local_drive` | yes |
| `_recovery/journal.mirror_queue.jsonl` | pending Drive mirrors (outage recovery) | `strict_local` | no |
| `_recovery/archive_legacy/` | pre-migration originals (audit) | `strict_local` | no |

## Single-authority rules

- **Assessment** is canonical ONLY inside `sessions/{sid}.json#assessment`. The
  analysis artifact references it by `assessment_ref` and never holds a copy.
- **Raw transcript** is captured first and immutable. Nothing rewrites or
  summarizes it in place.
- **Missing data stays missing.** Enrichment reads the WHOOP daily snapshot
  for THAT session's captured date; absent fields are `null`, never
  trend-estimated or invented. Transcripts never captured are `MISSING`.

## Versioning of derived outputs (amendment 3)

`analysis/{sid}.v{n}.json` is append-only. Each version records:
`analysis_version`, `generated_at`, `source.transcript_sha256`,
`engine_provenance`, `assessment_ref`, `supersedes` (previous version),
and `current` linkage. Reprocessing writes a NEW version; old versions stay
recoverable. `_glob_versions()` + `current_analysis_path()` resolve the chain.

## Enrichment & schedule (amendment 7)

- `tools/journal_enrich.py` — idempotent; per-session captured-date routing.
  Options: `--date YYYY-MM-DD`, `--since YYYY-MM-DD`, `--all`, `--dry-run`.
  Re-running with the same evidence is a **noop** (no new version).
- `tools/journal_daily.sh` — cron wrapper: enriches previous Cairo day, then
  reconciles Drive. Cadence is a configurable crontab slot
  (block `NIZAM-YAWMIYAT-JOURNAL`, UTC-scheduler dual-slot for Cairo DST).
- A failed run is safe to retry: versions are immutable and enrichment is
  deterministic, so no duplicates are produced.

## Drive reconcile & outage recovery (amendment 8)

- VPS is always authoritative. Drive is a one-way read-back-verified mirror.
- `tools/yawmiyat_index.py::reconcile_drive()`:
  1. resolves the private NIZAM Drive target (`06_HEALTH_FITNESS/JOURNALS_REFERENCES`);
  2. uploads `strict_local_drive` artifacts (transcripts `.txt`, mirrors `.md`);
  3. **reads the destination back** and compares sha256 to the local copy;
  4. on any Drive failure: the artifact is queued to `_recovery/journal.mirror_queue.jsonl`
     and retried next run; the VPS copy is NEVER deleted.
- Recipes are reported per run in the reconcile report.

## Tamper detection (requirement)

`build_manifest()` records sha256 for every committed content artifact
(transcripts, sessions, mirrors, analysis) — `_retrieval` is excluded as
self-referential. `verify_manifest()` recomputes current hashes; any mismatch is
reported as `TAMPERED` and identifies the exact artifact. Proven in
`tests/test_journal_persistence.py::test_tamper_detection` and on the live store.

## Recovery procedure

1. **Detect**: run `verify_manifest()`; address each `TAMPERED`/`missing` artifact
   from its canonical source (regenerate `mirrors/` from `sessions/`; analysis
   from `_glob_versions` history; transcripts are immutable and must be restored
   from Drive if lost — they are never regenerated from memory).
2. **Restore**: `git` is excluded for journal content; restore from `_recovery/archive_legacy`
   (pre-migration) or the verified Drive mirror (transcripts/mirrors) or the
   versioned `analysis/` history.
3. **Outage**: if Drive is down, artifacts queue and retry. No action deletes
   VPS data. On Drive return, re-run `reconcile_drive()`.
4. **Re-verify**: after any restore, rebuild `MANIFEST.json` + `INDEX.json`
   (`build_manifest(force=True)`, `build_index()`) and confirm `verify_manifest() == []`.

## Tools

| Script | Purpose |
|---|---|
| `tools/yawmiyat.py` | core: capture, commit, mirror, dedupe, THABAT, analysis versioning |
| `tools/yawmiyat_derived.py` | WHOOP/BADAN enrichment + deterministic evaluation |
| `tools/yawmiyat_index.py` | manifest, inverted index, tamper detect, Drive reconcile |
| `tools/journal_enrich.py` | scheduled idempotent enrichment + derive + index |
| `tools/backfill_migrate.py` | safe legacy migration (assigns IDs, marks transcripts MISSING) |
| `tools/journal_daily.sh` | cron wrapper (enrich + reconcile) |

## Privacy (HIMAYAH) — amendment 1

The blocker was: `PRIVACY_CLASSIFICATION.json` marked `YAWMIYAT/.../sessions`
and `mirrors` as `strict_local` ("on-disk only") and `SYNC_POLICY.json` would
"refuse strict_local paths automatically." The **smallest explicit amendment**
introduces `strict_local_drive` (see `DATA_MODEL.md`), applying to
`transcripts/**`, `mirrors/**`, `_retrieval/**`: on-disk only + MAY mirror
one-way to the private designated NIZAM Drive location, read-back verified,
never deleted from VPS. `sessions/**` and `analysis/**` remain `strict_local`
(VPS only). GitHub / Obsidian / Notion / any_external still refuse all journal
content.

## Note on regression gate

`MARSAD__flight_radar/tests/test_forecast.py` fails 22 tests under the current
environment (numpy version semantics); it is an unrelated pre-existing failure
not touched by this work. Everything else passes (841 + this suite's 6).