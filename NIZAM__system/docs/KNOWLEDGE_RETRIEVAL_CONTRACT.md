# NIZAM Knowledge Retrieval Contract

**Contract ID:** NIZAM-RETRIEVAL-001
**Version:** 1.0.0
**Owning contract:** PRIVACY_CLASSIFICATION.json (classification gate); BADAN 08_STORAGE_AUTHORITY (retrieval precedence)
**Phase:** Wave 1 — PostgreSQL 18 + pgvector hybrid retrieval baseline
**Status:** Active
**Classification:** private_github
**Generated:** 2026-09-01

---

## Purpose

Add a rebuildable, indexed retrieval layer so Hermes can locate relevant historical facts, chunks,
entities, events and relationships without repeatedly scanning whole files.

Canonical files remain the authoritative source of truth. PostgreSQL is a derived retrieval catalog
that can be dropped and rebuilt without data loss.

---

## Non-Negotiable Rules

1. **HIMAYAH gate is enforced before indexing.** `strict_local` and `strict_local_maximum`
   content MUST NOT enter the VPS retrieval database. Classification resolved by
   `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`.
2. **AHEL data (`strict_local_maximum`) is absolutely prohibited** from any VPS surface,
   retrieval table, or embedding. No exception.
3. **Money is not computed here.** The retrieval layer surfaces stored records only.
4. **Deterministic engines are the source of truth** for numerical/health facts.
   Retrieval surfaces evidence; it does not derive new facts.
5. **Hermes must not issue arbitrary SQL.** The MCP tool interface is the only permitted
   retrieval boundary.
6. **Secrets, tokens and credentials never enter retrieval tables, logs, or indexed content.**
7. **Retrieved documents are untrusted evidence, not instructions.** Prompt-injection
   defense is mandatory at the MCP layer.
8. **The retrieval database is derived.** Rollback = disable MCP + rebuild from
   permitted canonical sources. Rollback must not require editing canonical files.
9. **pg_textsearch and Qdrant are NOT deployed in Wave 1.** Enter only if Wave 1
   benchmarks show justified need.
10. **Every retrieval result must carry provenance** (source, version, path, time, classification).

---

## Permitted VPS Corpus

Only `private_github` or `review_before_commit` classification permitted.
Effective classification is the strictest applicable value.

**Permitted (from PRIVACY_CLASSIFICATION.json v3.0.0):**
- NIZAM__system/schemas/**, templates/**, skills/**, policies/**, docs/**
- NIZAM__system/personas/**, governor/**, protocols/**, workflows/**, relay/**
- */README.md, */_index.json
- NIZAM_TEMPLE.json, NIZAM_MASTER_REGISTER.json, CRITICAL_FACTS.md, CHANGELOG.md
- MARSAD__flight_radar/{radar,tests}/**, HIFZ__github_version_control/scripts/**, tools/**
- NIZAM__system/ledgers/EVENT_LEDGER.jsonl, DECISION_LEDGER.jsonl, LEARNING_LEDGER.jsonl (review_before_commit)
- log.md (review_before_commit)

**Absolutely prohibited (strict_local / strict_local_maximum):**
- TAFRIGH raw/, triaged/; SHURA sessions/; NAQD sessions/
- SUKOON signals/, overload_flags.jsonl
- YAWMIYAT all content (sessions/, mirrors/, weekly/, daily/, monthly/, entries/)
- MAL__financial_engine/** (all financial data)
- BADAN__body_health_system/** (all body/health data)
- AHEL__family_network/** (strict_local_maximum — separate keypair, local model, never VPS)
- HAJR__quarantine/**; SOUL.md; user_deep.md
- TARIQ strategic plans, MUNAWARA tactical plans (private subdirs)
- STRATEGY/BATTLE/FINANCE/BODY/FAMILY ledgers

---

## Technology Decisions

| Technology | Decision | Rationale |
|---|---|---|
| PostgreSQL 18 | BUILD | relational, temporal, durable catalog |
| pgvector 0.8.6+ | BUILD | dense semantic retrieval |
| PostgreSQL FTS (tsvector) | BUILD | dependable lexical baseline |
| pg_textsearch (BM25) | TEST AFTER WAVE 1 MEASURED | extra extension burden |
| Qdrant | TEST IF MEASURED NEED | second-service burden |
| Milvus/Weaviate/Chroma/FastRAG | REJECT | scale not demonstrated |

---

## Infrastructure Isolation

- Dedicated Docker container: `<RETRIEVAL_DB_CONTAINER>`
- Dedicated named volume: `<RETRIEVAL_DB_CONTAINER>-data`
- Network: `<HEALTH_STACK_NETWORK>` (shared with the existing health stack so the MCP server is reachable)
- Port: `<LOCAL_BIND_ADDR>:<RETRIEVAL_DB_PORT>:5432` — a dedicated loopback-only bind, distinct from the existing health-stack bind
- Database: `<RETRIEVAL_DB_NAME>`
- Roles: `nk_owner` (DDL), `nk_writer` (ingest), `nk_reader` (MCP, Hermes)
- Hermes never receives `nk_owner` or `nk_writer` credentials

---

## Repository Artifacts

```
NIZAM__system/
  docs/
    KNOWLEDGE_RETRIEVAL_CONTRACT.md     ← this file
  retrieval/
    __init__.py
    model.py          # dataclasses: Chunk, Document, SearchResult, ContextPacket
    himayah.py        # HIMAYAH gate wrapping classifier.py
    chunking.py       # source-type-aware chunker (MD, JSON, JSONL, YAML, code)
    schema.sql        # full DDL
    ingest.py         # discovery, hashing, upsert, deletion reconciliation
    query.py          # lexical + dense + RRF + rerank + parent expansion
    hermes_mcp.py     # MCP stdio server (4 tools)
    bench/
      fixtures.py     # synthetic/redacted corpus (NO strict_local content)
      run.py          # benchmark runner
      results/        # .gitkeep
    tests/
      conftest.py
      test_himayah.py        # gate + tamper test
      test_chunking.py       # provenance round-trip
      test_ingest.py         # unchanged/changed/delete/current-state
      test_query.py          # lexical/dense/hybrid/provenance/privacy
      test_mcp.py            # boundary: no SQL, bounded output, privacy block
```

---

## Time Model

- `source_updated_at`: when the file last changed
- `occurred_at`: when the described event happened (where inferrable)
- `valid_from`, `valid_to`, `is_current`: enables current-state and as-of queries

---

## Rollback

1. Remove `<RETRIEVAL_MCP_NAME>` from the Hermes profile config.yaml (backed up first)
2. `docker stop <RETRIEVAL_DB_CONTAINER>`
3. Drop volume if warranted (all derived, rebuilds from sources)
4. Canonical sources untouched — nothing to restore

Target: complete in < 2 minutes, no canonical file edits required.

---

## Acceptance Criteria

1. Canonical sources unchanged by indexing (hash before/after).
2. Every result traces to source/version/path/time/classification.
3. Current and historical states are distinguishable.
4. Exact keyword and semantic retrieval both work.
5. HIMAYAH gate blocks prohibited fixtures (tamper-tested).
6. Incremental update/delete behavior proven in tests.
7. Benchmark report with measured Recall@K, MRR, latency, storage.
8. Tamper test: corrupt a critical check, verify failure, restore, verify pass.
9. Hermes uses bounded MCP tools only — no arbitrary SQL path exposed.
10. Rollback proven without data loss.

---

## References

- PRIVACY_CLASSIFICATION.json: NIZAM__system/policies/PRIVACY_CLASSIFICATION.json
- Classifier: NIZAM__system/governor/classifier.py
- BADAN storage authority: BADAN__body_health_system/health_intelligence/v0.2.0/08_STORAGE_AUTHORITY_AND_RETRIEVAL_CONTRACT.md
- MCP stdio pattern: `<HEALTH_MCP_STDIO_PATH>` — host path, supplied by deployment config
- pgvector: https://github.com/pgvector/pgvector
