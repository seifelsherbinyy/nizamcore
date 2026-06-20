# Outbound Message Privacy Guard

## Before any Khaldun Telegram send

1. Run `validate_khaldun_response()` on message body.
2. Run `apply_egress()` from pulsation HIMAYAH module.
3. Require `NIZAM_LIVE_CONNECTORS_APPROVED=1` AND `NIZAM_KHALDUN_OUTBOUND_APPROVED=1`.
4. Log to `khaldun-reminders-dryrun.jsonl` when outbound not approved.

## Content rules

- No raw journal bodies, open questions text, or therapy excerpts.
- Theme summaries and capacity bands only.
- Include missing-data honesty when sources absent.

## Default

Composition and validation run in dry-run mode until operator approves outbound.
