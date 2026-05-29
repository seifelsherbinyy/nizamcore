# NIZAM Ledgers

Append-only JSONL ledgers. Sole writer: **Ammar** (governor).
Other code calls `governor/ledger_writer.py`; never opens `.jsonl` files directly.

## Ledger map

| Ledger | Privacy | Phase | Cryptographic integrity |
|---|---|---|---|
| `EVENT_LEDGER.jsonl` | review_before_commit | 1 | hash-chained `prev_hash` |
| `LEARNING_LEDGER.jsonl` | review_before_commit | 1 | hash-chained `prev_hash` |
| `DEAD_LETTER.jsonl` | review_before_commit | 1 | hash-chained `prev_hash` |
| `STRATEGY_LEDGER.jsonl` | strict_local | 2 | RFC 6962 Merkle tree + Ed25519 Signed Tree Head |
| `BATTLE_LEDGER.jsonl` | strict_local | 2 | hash-chained `prev_hash` |
| `FINANCE_LEDGER.jsonl` | strict_local | 2 | hash-chained `prev_hash` |
| `BODY_LEDGER.jsonl` | strict_local | 2 | hash-chained `prev_hash` |
| `FAMILY_LEDGER.jsonl` | strict_local_maximum | 3 | separate keypair; AHEL-only |
| `DECISION_LEDGER.jsonl` | review_before_commit | 1 | hash-chained `prev_hash` |

## Row schema (common)

```json
{
  "ts": "2026-05-28T20:18:00Z",
  "ledger": "EVENT_LEDGER",
  "row_id": "uuid4",
  "trace_id": "uuid4-end-to-end-chain-id",
  "actor": "Salman|Hazim|Ammar|...|operator",
  "action": "string",
  "module": "SHURA|NAQD|...",
  "privacy_class": "review_before_commit|strict_local|strict_local_maximum",
  "prev_hash": "sha256-of-prior-row",
  "row_hash": "sha256-of-this-row-excluding-row_hash",
  "payload": {}
}
```

## STRATEGY_LEDGER hardening (G13.5 + E4.3)

Default Python library: **`arc-protocol`** (pip install arc-protocol).
Provides RFC 6962-style Merkle tree + Ed25519 Signed Tree Heads.
Alternative: `merkletools` + manual `cryptography.hazmat.primitives.asymmetric.ed25519`.
Operator gate: G13.5 (USER selects). If `arc-protocol` is unavailable on the VPS
at install time, `merkletools` is the documented fallback.

Pre-Phase-2 bootstrap uses stdlib hashlib only (no cryptographic STH); STH wiring
arrives at E4.3 once Tariq is live.
