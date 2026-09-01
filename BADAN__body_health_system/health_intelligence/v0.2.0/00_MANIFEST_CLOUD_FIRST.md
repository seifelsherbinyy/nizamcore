# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Cloud-First Build Manifest

**Module:** BINA_BUILD → BADAN / Health Intelligence  
**Lane:** Health  
**Status:** refined cloud architecture + developer handoff; runtime deployment is not claimed  
**Primary deployment model:** OVH VPS + private Google Drive + GitHub + Hermes  

## Governing correction

- **FACT:** NIZAM is primarily cloud-resident. The OVH VPS is the continuously available operational/runtime plane.
- **FACT:** `47_NIZAM` in private Google Drive is the canonical human/agent knowledge and retrieval root.
- **FACT:** GitHub is the versioned source for software, schemas, contracts and tests.
- **FACT:** Hermes is the orchestrator and retrieval layer across VPS, Drive, APIs, Calendar and approved web research.
- **FACT:** Secrets, credentials, refresh tokens and deliberately restricted artifacts never belong in Google Drive.
- **INFERENCE:** The old phrase “local-first” is ambiguous and should be deprecated in implementation documentation. Use explicit storage classes instead.
- **MISSING:** The actual NIZAM/Hermes root path on the live OVH VPS has not been inspected in this environment and must not be invented.

## Storage authority

| Plane | Purpose | Canonical for |
|---|---|---|
| OVH VPS | runtime, ingestion, databases, jobs, caches, embeddings, private working data | operational truth |
| Google Drive `47_NIZAM` | organized durable memory, journals, ledgers, reports, indexes, retrieval manifests | knowledge/retrieval truth |
| GitHub | source code, schemas, tests, contracts, migration history | versioned software truth |
| Hermes | routing, synthesis, retrieval, scheduling, execution receipts | orchestration only |
| External APIs/Web | source evidence | never canonical personal truth |

## Package contents

1. `00_MANIFEST_CLOUD_FIRST.md`
2. `01_RESEARCH_REPORT_AND_BIBLIOGRAPHY.md`
3. `02_CLOUD_ARCHITECTURE_AND_IMPLEMENTATION_SPEC.md`
4. `03_METRIC_DICTIONARY_AND_CALCULATION_SPEC.md`
5. `04_BEHAVIOR_JOURNAL_STRESS_METHOD.md`
6. `05_DAILY_1100_HERMES_AND_CALENDAR_WORKFLOW.md`
7. `06_VALIDATION_RISKS_AND_ROADMAP.md`
8. `07_PROPOSED_SCHEMA_PACKAGE.md`
9. `08_STORAGE_AUTHORITY_AND_RETRIEVAL_CONTRACT.md`
10. `09_HERMES_EXECUTION_PROMPT_100_WORDS.md`
11. `schemas/*.schema.json`
12. `tools/verify_cloud_build.py`

## Security boundary

The architecture is **cloud-first, not Drive-everything**. VPS-only classes remain for secrets and deliberately restricted data. Private Drive stores durable user knowledge when permitted by classification. Every synced artifact carries provenance, source authority, sensitivity and canonical-location metadata.

## Runtime boundary

No credential was minted or rotated. No WHOOP consent was completed. No webhook was registered. No DNS/host mutation occurred. No Git commit/push occurred. No calendar event was written. No live VPS path or tool output was invented.
