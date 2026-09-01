# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Cloud Architecture & Implementation Specification

## 1. Architecture

```text
WHOOP / Calendar / Journals / Workouts / Research
                     │
                     ▼
              HERMES ORCHESTRATOR
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   OVH VPS       GOOGLE DRIVE     GITHUB
 operational     47_NIZAM memory  code/contracts
 runtime         & retrieval      tests/schemas
       │             │
       └────── Retrieval Fabric ───┘
                     │
               bounded LLM context
```

**INFERENCE:** BADAN remains the health normalization owner. The correction is storage topology, not a parallel health subsystem.

## 2. Explicit storage classes

Do not use the word `local` as a physical-location description.

| Class | Location | Examples | Drive allowed |
|---|---|---|---|
| `vps_secret` | encrypted VPS secret store | OAuth client secret, refresh token, API key | No |
| `vps_private` | VPS DB/files | raw provider payload cache, temporary joins, embeddings containing sensitive text | No by default |
| `cloud_private` | VPS + private Drive where classification permits | journals, health ledgers, longitudinal records, daily plans | Yes |
| `drive_knowledge` | private `47_NIZAM` | indexes, reports, curated journals, research, summaries, manifests | Yes |
| `github_versioned` | private GitHub repo | code, schemas, contracts, tests | Not as data store |

Legacy `strict_local` should be interpreted as **VPS-only** until the governing schemas are migrated. Do not silently broaden that legacy classification.

## 3. Canonical authority rules

1. Runtime state is authoritative on VPS databases/files.
2. Durable knowledge is authoritative under `47_NIZAM` in Drive.
3. Code/contracts are authoritative in GitHub.
4. Hermes owns no independent copy of truth; it resolves authorities through manifests.
5. When copies disagree, compare provenance/version/source timestamps; do not prefer “most recently modified” blindly.
6. Drive indexes point to canonical records rather than duplicating them unnecessarily.

## 4. VPS operational plane

The live VPS should host, after inspection of the actual environment:
- Hermes Agent runtime and skills;
- WHOOP polling adapter and OAuth token handling;
- scheduler/cron execution;
- deterministic feature engine;
- SQLite for MVP or PostgreSQL if concurrency requires it;
- retrieval catalog/vector index/cache;
- Drive sync/readback worker;
- structured run receipts and failure queue;
- encrypted secrets outside repositories and Drive.

**MISSING:** exact filesystem paths and service names. The implementing agent must discover them before edits.

## 5. Drive knowledge plane

`47_NIZAM` is the retrieval root. For health, prefer:

```text
47_NIZAM/06_HEALTH_FITNESS/
  INDEX
  WHOOP/
    INDEX
    Daily_Snapshots/
    Weekly_Reviews/
    Longitudinal/
  WORKOUTS/
    INDEX
    Ledger/
  JOURNALS_REFERENCES/
    INDEX
  DAILY_INTELLIGENCE/
    INDEX
    Plans/
    Reviews/
  RESEARCH/
    INDEX
  SYSTEM/
    SOURCE_REGISTRY
    RETRIEVAL_MANIFEST
    SCHEMA_POINTERS
```

Use existing canonical folders when equivalent; do not create duplicates blindly.

## 6. Retrieval fabric

Hermes lookup order:
1. boot/system manifest;
2. domain index;
3. VPS current-state store for fresh operational data;
4. canonical Drive artifact(s);
5. external connected source/API if freshness is required;
6. web research when needed;
7. synthesis with provenance tags.

Hermes should never load entire folders into context. Retrieve compact indexes first, then top relevant artifacts, then compute a bounded context packet.

## 7. WHOOP ingestion

- serialize OAuth refresh because refresh tokens rotate;
- poll incrementally with bounded overlap;
- paginate to completion;
- upsert by provider identifier + update timestamp;
- preserve UTC timestamp, provider offset, Cairo-rendered timestamp and WHOOP cycle ID;
- checkpoint only after the transaction commits;
- back off on rate limits;
- store credentials only in `vps_secret`.

## 8. Persistence and Drive sync

After each successful daily run:
1. commit operational records on VPS;
2. classify artifacts;
3. write permitted durable knowledge to Drive;
4. read the destination back;
5. update domain index/manifest if canonical pointers changed;
6. store sync receipt on VPS.

A Drive failure must not erase VPS operational truth. Queue retry and mark the run `SYNC_PENDING` or `FAILED_SYNC`; never falsely report full success.

## 9. LLM boundary

The LLM may synthesize, explain patterns, generate hypotheses and draft an agenda. It must not be the arithmetic engine, timestamp engine, deduplication engine, persistence authority or completion authority.

## 10. Calendar boundary

Calendar is a planning/action surface, not the health store. Human approval remains required before writes where the governing NIZAM contract requires `Calendar Approved`. Idempotency keys must be deterministic and secrets stay VPS-only.
