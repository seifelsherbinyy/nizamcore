# Privacy Scan Report

Generated: 2026-06-14T13:33:37.6155935+03:00
Repo root: D:\NIZAM

## Overall status: **PASS**

## Blocked path presence (strict-local inventory)

| Pattern | Exists | Status |
|---------|--------|--------|
| .env | True | PRESENT_STRICT_LOCAL |
| oauth-token.json | False | ABSENT_OR_OK |
| oauth-client.json | False | ABSENT_OR_OK |
| NIZAM-secrets.json | True | PRESENT_STRICT_LOCAL |
| YAWMIYAT__journaling | True | PRESENT_STRICT_LOCAL |
| BADAN__body_health_system\daily_signals | True | PRESENT_STRICT_LOCAL |
| SUKOON__recovery_first | True | PRESENT_STRICT_LOCAL |
| NIZAM__system\ledgers\EVENT_LEDGER.jsonl | True | PRESENT_STRICT_LOCAL |
| TAFRIGH__brain_dumper\raw | True | PRESENT_STRICT_LOCAL |
| SOUL.md | True | PRESENT_STRICT_LOCAL |

## Failures

- None

## HIMAYAH rule

Research and graphify scans must scope to NIZAM__system/companion/ and Research_docs/vendor_research/ only.
Never include blocked paths in clone, graphify, or egress operations.
