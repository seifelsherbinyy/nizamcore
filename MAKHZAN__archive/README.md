# MAKHZAN — Archive

Arabic: مخزن — "warehouse / storehouse."

## Purpose
Immutable timestamped snapshots. Whenever POP rewrites or reconciles a file, the prior state is mirrored here first so we never lose work silently.

## Snapshot triggers
- Phase boundary completion (Phase 1, Phase 2, Phase 3).
- NAQD reconciliation (rewrite of contradicted notes).
- Schema migrations or registry version bumps.
- User-requested checkpoint.

## Layout
- `YYYY-MM-DDTHH-MM-SSZ/` — one folder per snapshot.
- Inside each: mirrored file structure + `MANIFEST.json` listing every snapshotted file with SHA256 hash, size, and source path.

## Rules
- **Append-only.** Never delete a snapshot.
- **Never edit** past snapshots.
- Snapshot contents inherit privacy of their original location — strict-local sources stay strict-local inside the snapshot. (See `.gitignore` MAKHZAN-specific rules.)

## Privacy
The folder itself is committable, but snapshots may contain strict-local mirrors — `.gitignore` excludes `MAKHZAN__archive/**/raw/`, `**/triaged/`, `**/sessions/`, `**/signals/`.
