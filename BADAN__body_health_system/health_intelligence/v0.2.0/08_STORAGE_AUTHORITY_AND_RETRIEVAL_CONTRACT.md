# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Storage Authority & Hermes Retrieval Contract

## Purpose

This contract removes ambiguity around “local.” NIZAM is a cloud-first system whose operational and knowledge planes are primarily the OVH VPS and private Google Drive.

## Authority matrix

- **VPS operational authority:** current ingested records, deterministic features, job state, caches, embeddings, queues, runtime receipts.
- **Drive knowledge authority:** durable organized journals, health/workout ledgers, reports, reviews, research, indexes, canonical knowledge pointers.
- **GitHub software authority:** code, contracts, schemas, migrations and tests.
- **Hermes orchestration authority:** none; Hermes resolves and acts on the above authorities.

## Required metadata on durable records

Every canonical or synchronized artifact should expose, where applicable:
- stable artifact ID;
- schema/version;
- source system;
- created/updated timestamps;
- data effective period;
- storage class;
- canonical authority;
- canonical pointer;
- sensitivity/classification;
- upstream evidence refs;
- content/hash or revision marker when practical;
- sync/readback status.

## Retrieval order

1. `47_NIZAM` master index/bootstrap;
2. relevant domain index;
3. retrieval/source registry;
4. VPS fresh state for current facts;
5. Drive canonical long-form records;
6. connected APIs for freshness;
7. web research for external evidence;
8. synthesis.

## Retrieval quality rules

- Prefer canonical pointers, not duplicates.
- Prefer current operational evidence to old narrative summaries.
- Prefer higher-quality primary evidence to inferred summaries.
- Never silently merge contradictory records.
- Label facts, inferences, assumptions and missing evidence.
- Keep LLM context bounded; retrieve more only when needed.

## Sync rules

- VPS → Drive only after classification.
- Drive writes require destination readback before `OK`.
- Drive outage creates retry state, not data loss.
- Drive → VPS retrieval cache may be rebuilt; cache is never canonical.
- Secrets/tokens never enter Drive indexes, Docs, Sheets, logs or Git.

## Hermes bootstrap expectation

At startup or fresh cron execution, Hermes should read a compact machine-readable bootstrap manifest that gives the current domain indexes, source registries, approved repository location, storage authorities and retrieval precedence. This avoids broad searches and minimizes latency/token usage.
