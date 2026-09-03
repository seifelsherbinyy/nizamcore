"""NIZAM adaptive cross-domain governor — deterministic gate layer.

Owning contract: NIZAM-CONTRACT-01 (Constitution and Governance) v1.0.0
Depends on:     NIZAM-CONTRACT-03, NIZAM-CONTRACT-04, NIZAM-CONTRACT-05
Phase:          R1_FIXTURES / P0_FIXTURES — deterministic, credential-free,
                zero-network, zero-external-mutation.

SCOPE BOUNDARY (deliberate, do not widen without an owner amendment):
  This package contains ONLY pure deterministic decision logic. It performs no
  I/O, opens no socket, reads no credential, touches no Drive/Calendar/GitHub,
  and schedules nothing. Actuators (R4-R7 of the rollout playbook) are NOT here
  and are NOT authorized by the presence of this package.
"""
CONTRACT_VERSIONS = {
    "NIZAM-CONTRACT-01": "1.0.0",
    "NIZAM-CONTRACT-02": "1.0.0",
    "NIZAM-CONTRACT-03": "1.0.0",
    "NIZAM-CONTRACT-04": "1.0.0",
    "NIZAM-CONTRACT-05": "1.0.0",
}
PHASE = "R1_FIXTURES"
