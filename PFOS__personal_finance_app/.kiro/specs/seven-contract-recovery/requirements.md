# Seven-contract recovery requirements

Owner: contracts/programs/SEVEN_CONTRACT_RECOVERY.md. Phase: Recovery 1.
NIZAM-derived; subordinate to existing domain contracts and steering.

- R1: Record source identity, evidence class, authority/supersession and implementation references.
- R2: Treat missing remote access and absent local source separately; never infer absence from scoped search.
- R3: Inventory configured integrations without emitting credential values or deployment particulars.
- R4: Keep ledger facts, candidates, deterministic calculations, forecasts, explanations and signals separate.
- R5: The shared JSON money validator must reject every value rejected by the safe-integer money domain;
  valid signed integer endpoints and zero must survive validation and JSON round-trip unchanged.
- R6: Current-schema migration and fake Drive loading must reject unsafe monetary inputs without rewriting them.
- R7: Preserve user changes, all existing acceptance checks, original contracts and source bytes.
- R8: Record focused checks and `npm run verify:all -- --all` exactly as observed, including failures.
- R9: Publish seven-workstream status, architecture maps, readiness, limitations and next bounded loop.
