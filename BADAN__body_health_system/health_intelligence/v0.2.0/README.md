# NIZAM Health Intelligence v0.2.0 — implementation record

Owning contract: **NIZAM-HEALTH-INTELLIGENCE v0.2.0**
Phase: cloud-first reconciliation
Status as of 2026-09-01: implemented and verified on the live VPS.

Governing docs are `00_*.md` … `09_*.md` in this directory. `README_PACKAGE_ORIGINAL.md`
is the delivered package's own readme, kept unmodified.

## Authority split

| Plane | Owns | Lives in |
|---|---|---|
| VPS | runtime databases, ingestion, deterministic analytics, caches, cron, secrets | `personal-health` stack |
| Drive | organized durable knowledge, journals, ledgers, reports, indexes, manifests | `47_NIZAM/06_HEALTH_FITNESS` |
| GitHub | code, schemas, migrations, tests | this directory |

Hermes owns no independent copy of truth. It resolves the three authorities
through `SYSTEM/RETRIEVAL_MANIFEST.json`.

## What is in this directory

```text
schemas/       6 JSON schemas (authoritative)
migrations/    002_health_intelligence_v020.sql — additive; applied to personal_health
sync/          deployment-independent engine code
tests/         the acceptance tests for that code
tools/         verify_cloud_build.py
```

### `sync/`

| Module | Role |
|---|---|
| `storage_policy.py` | storage-class allow/deny lists. Policy only, no identifiers. |
| `feature_engine.py` | pure statistics: windows, robust z, personal baselines, data quality. |
| `artifact_builder.py` | provenance envelopes, classification gate, secret scan, canonical JSON. |
| `compute_features.py` | cycle-aligned Cairo day joins; writes `daily_feature_vectors`. |

## What is deliberately NOT in this directory

These modules encode live deployment particulars (Drive folder IDs, absolute
paths, service identities). Tracking them would violate the NIZAM rule against
committing deployment particulars, so they live on the VPS only:

| VPS-only file | Why |
|---|---|
| `sync/drive_layout.py` | real Drive folder IDs |
| `sync/index_builder.py` | imports `drive_layout` |
| `sync/drive_sync.py` | imports `drive_layout`; holds runtime topology |
| `tests/test_index_builder.py` | imports `drive_layout` |
| `scripts/daily-ingest.sh` | absolute paths + a Drive folder ID |
| `scripts/reconcile.sh` | absolute paths |
| `.env`, `.env.mcp`, `data/tokens.json` | `vps_secret`, mode 600, never leave the VPS |

`storage_policy.py` is the seam that keeps `artifact_builder.py` free of identifiers.

## Non-negotiable rules this code enforces

1. **Deterministic engines are the only source of numbers.** No LLM computes,
   sources, dedupes or timestamps a health value. `artifact_builder` copies
   engine output; it never recomputes it.
2. **Missing stays missing.** A absent metric yields `null` and
   `status: "insufficient_data"`. Nothing is imputed, ever.
3. **Personal baselines, not population norms.** Every artifact carries
   `population_norms_used: false` and a trailing-median personal baseline.
   Deviation language means *unusual versus your own recent baseline*.
4. **Rest days are real zeros.** A cycle day with no workout has training load
   `0.0`, not `null`. Imputing it as missing would bias every window.
5. **`strict_local` means VPS-only** and is never silently broadened. The Drive
   allow-list is `{cloud_private, drive_knowledge}` only.
6. **Nothing is reported synced until it is read back.** Every Drive write is
   downloaded again and sha256-compared; `sync_receipts` has a DB-level CHECK
   (`sr_ok_requires_readback`) that makes `status='OK'` impossible without a
   matching readback hash.
7. **Secrets never reach Drive or Git.** Three independent gates: storage-class
   allow-list, credential-shaped key scan, credential-shaped value regex scan.
   A DB CHECK (`sr_no_secret_to_drive`) refuses a `vps_secret` receipt.
8. **Calendar writes are human-gated.** No code path here can create, update or
   approve a calendar event. Plans carry `write_status: "not_written"` and
   `approved_by_human: false`.
9. **Drive scope stays `drive.file`.**

## Scheduling

Target is 11:00 `Africa/Cairo`. The host's cron (Ubuntu `cron` 3.0pl1) has **no
`CRON_TZ` support**, so a single fixed UTC slot cannot hold 11:00 Cairo across
DST:

| Regime | 11:00 Cairo |
|---|---|
| EEST (+3, summer) | 08:00 UTC |
| EET (+2, winter) | 09:00 UTC |

Cron therefore fires at **both** 08:00 and 09:00 UTC and `daily-ingest.sh` gates
on the real Cairo hour from the tz database. `tests/test_schedule_gate.py` proves
that exactly one slot passes per day for 2026–2028, including every DST
transition day, and that no single UTC hour would have worked year-round.

## Failure isolation

Steps do not abort the chain. The previous `set -euo pipefail` script aborted at
step 2 when `daily_export.py` raised, which silently skipped the Drive upload and
stalled the Drive copy for roughly 2.5 months. Each step now records its own
status and the run exits non-zero only after every step has had its turn.
`tests/test_schedule_gate.py` asserts `errexit` cannot come back.

## Verify

```bash
python3 tools/verify_cloud_build.py                 # expect VERIFY_PASS
python3 tools/verify_cloud_build.py --tamper-test   # expect VERIFY_FAIL, exit 1
python3 -m pytest tests -q                          # deployment-independent tests
```

On the VPS, the full suite (including the VPS-only modules) runs with:

```bash
docker run --rm --network <DOCKER_NET> --env-file <STACK_ROOT>/.env \
  -v <STACK_ROOT>:/repo:ro -w /repo <SYNC_IMAGE> \
  sh -lc 'PYTHONPATH=/repo python3 -m pytest tests -q'
```

Placeholders above are deployment particulars deliberately not tracked in git:
`<STACK_ROOT>` is the sync stack root on the VPS, `<DOCKER_NET>` its container network,
`<SYNC_IMAGE>` the built sync image tag. Substitute from the live host, never from this file.
