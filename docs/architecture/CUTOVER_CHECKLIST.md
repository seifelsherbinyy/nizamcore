# Cutover Checklist — laptop → VPS+Drive (C1)

**Scope:** all C-phase tasks of Plan v2. Filled by the operator during the actual cutover.
**Pre-requisite:** Phase G (T2–T4) has been green for ≥ 30 days.

> Fill the right-hand cells as each item completes. Initials = your initials. Anything missed gets
> a `MISS` row at the bottom explaining what happened and how it was reconciled.

## C0 — Pre-cutover MAKHZAN anchor

| Item | Done? | Timestamp (UTC) | Initials | Notes |
|------|-------|------------------|---------|-------|
| Run `verify-nizamcore.ps1 -ProduceManifest`. | | | | |
| SHA256 manifest copied to operator-only safe. | | | | manifest path: |
| Manifest copied to printed paper backup. | | | | |
| EVENT_LEDGER tail row noted (row_id + hash). | | | | row_id: |
| STRATEGY_LEDGER STH snapshot noted (tree_size + root). | | | | tree_size: |

## C2 — General-tier cutover

| Item | Done? | Timestamp (UTC) | Initials | Notes |
|------|-------|------------------|---------|-------|
| Laptop IDE writers stopped. | | | | |
| `git status` clean on laptop. | | | | |
| Framework-tier `rclone sync` to `drive-crypt:` finished without error. | | | | bytes synced: |
| VPS `git pull` succeeded. | | | | commit hash: |
| `ledger_writer.verify_chain` ALL ledgers GREEN on both sides. | | | | |
| Hash-chain tail row matches laptop & VPS. | | | | |
| First `/shura-brainstorm` from VPS round-trips to operator Telegram. | | | | trace_id: |

## C3 — AHEL-specific cutover

> Yusra (AHEL) writes ONLY here. Operator runs this section in person, never via remote shell.

| Item | Done? | Timestamp (UTC) | Initials | Notes |
|------|-------|------------------|---------|-------|
| AHEL passphrase retrieved from operator-only safe (NOT from password manager copy). | | | | |
| AHEL LUKS volume `nizam_ahel` opened on VPS using that passphrase. | | | | |
| `AHEL__family_network/**` SCP'd over Tailscale only. | | | | total files: |
| Laptop AHEL volume closed AND unmounted post-transfer. | | | | |
| Yusra-only path check: `classifier.classify(AHEL__family_network/*)` → `strict_local_maximum`. | | | | |
| Deliberate egress test: `Plane.GITHUB_PRIVATE` for an AHEL path BLOCKED. | | | | |

## C4 — 7-day verification window

> Run T1 every day at the same hour. Any RED ends the cutover.

| Day | Date (UTC) | T1 green? | Cost (USD) | DEAD_LETTER count | Notes |
|-----|------------|-----------|-------------|--------------------|-------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |

## C5 — Laptop formal retirement

| Item | Done? | Timestamp (UTC) | Initials | Notes |
|------|-------|------------------|---------|-------|
| External-media snapshot of laptop disk taken. | | | | media id: |
| Snapshot SHA256 noted in safe. | | | | sha256: |
| Laptop git remote write access revoked. | | | | |
| `SYNC_POLICY.json` re-classifies laptop as read-only mirror. | | | | commit: |
| `nizam_startup.py` on VPS reports laptop=`mirror_only`. | | | | |

## Sign-off

| Role | Name | Signature (initials) | Date (UTC) |
|------|------|----------------------|------------|
| Operator | | | |
| Ammar (STEWARD ledger row id) | | (auto, after sign-off) | |

## MISS log

| ID | What happened | Reconciliation |
|----|----------------|-----------------|
| | | |
| | | |
