# ADR-0001: Local-First Egress and Replay Policy

- Status: Accepted for local remediation
- Date: 2026-06-13
- Activation scope: local code and tests only

## Decision

1. `strict_local_maximum` data never leaves the local machine and never enters a third-party model.
2. `strict_local` data may remain on local disk. Any encrypted backup, VPS, Telegram, or zero-data-retention inference activation requires separate operator approval.
3. Drive, Notion, Gmail, Telegram, GitHub writes, model inference, deployment, and remote telemetry are disabled by default.
4. External writes require a HIMAYAH decision, explicit operator approval, and an audit event containing hashes and bounded metadata rather than payload text.
5. Connector operations use at most three attempts with backoff `[1, 4, 16]`.
6. Final failures enter `NIZAM__system/ledgers/DEAD_LETTER.jsonl`, classified `strict_local`.
7. Dead-letter replay is manual, approval-gated, and idempotent. Automatic replay is prohibited.
8. Credentials are never stored in policy files, logs, receipts, or committed artifacts.

## Deferred Decisions

- Production model provider and model
- Approved pilot connectors
- VPS and backup topology
- Remote telemetry destination
- Credential rotation and activation

These decisions require an operator approval receipt before implementation or activation.

## Rollback

Revert this ADR and its matching machine-readable policy changes. Revoked credentials must never be restored.
