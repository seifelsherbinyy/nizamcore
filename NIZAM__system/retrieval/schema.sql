-- Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
-- NIZAM Knowledge Retrieval schema — PostgreSQL 18 + pgvector
-- Database: nizam_knowledge
-- Apply with: psql -U nk_owner -d nizam_knowledge -f schema.sql

BEGIN;

-- Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Roles (idempotent) ────────────────────────────────────────────────────────
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='nk_owner')  THEN CREATE ROLE nk_owner;  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='nk_writer') THEN CREATE ROLE nk_writer; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='nk_reader') THEN CREATE ROLE nk_reader; END IF;
END $$;

-- ── Sources ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
  source_id      TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  host_path      TEXT NOT NULL,              -- absolute VPS path (no secrets)
  classification TEXT NOT NULL               -- private_github | review_before_commit
                   CHECK (classification IN ('private_github','review_before_commit')),
  enabled        BOOLEAN NOT NULL DEFAULT true,
  last_scanned   TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Documents ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
  document_id    TEXT PRIMARY KEY,
  source_id      TEXT NOT NULL REFERENCES sources(source_id),
  canonical_key  TEXT NOT NULL,              -- source-relative path
  title          TEXT,
  doc_type       TEXT NOT NULL               -- markdown|json|jsonl|yaml|code|plaintext
                   CHECK (doc_type IN ('markdown','json','jsonl','yaml','code','plaintext')),
  language       TEXT NOT NULL DEFAULT 'en',
  module         TEXT,                       -- NIZAM__system | MARSAD | etc.
  classification TEXT NOT NULL
                   CHECK (classification IN ('private_github','review_before_commit')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_id, canonical_key)
);
CREATE INDEX IF NOT EXISTS idx_doc_module ON documents(module);
CREATE INDEX IF NOT EXISTS idx_doc_classification ON documents(classification);

-- ── Document versions ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_versions (
  version_id        TEXT PRIMARY KEY,
  document_id       TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  content_hash      TEXT NOT NULL,           -- sha256 of raw content
  source_updated_at TIMESTAMPTZ NOT NULL,
  indexed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_from        TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_to          TIMESTAMPTZ,
  is_current        BOOLEAN NOT NULL DEFAULT true,
  superseded_by     TEXT REFERENCES document_versions(version_id) ON DELETE SET NULL,
  classification    TEXT NOT NULL
                      CHECK (classification IN ('private_github','review_before_commit'))
);
CREATE INDEX IF NOT EXISTS idx_ver_doc       ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_ver_current   ON document_versions(document_id, is_current);
CREATE INDEX IF NOT EXISTS idx_ver_hash      ON document_versions(content_hash);
CREATE INDEX IF NOT EXISTS idx_ver_valid     ON document_versions(valid_from, valid_to);

-- ── Chunks ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id        TEXT PRIMARY KEY,
  version_id      TEXT NOT NULL REFERENCES document_versions(version_id) ON DELETE CASCADE,
  document_id     TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  parent_chunk_id TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
  prev_chunk_id   TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
  next_chunk_id   TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
  ordinal         INTEGER NOT NULL,
  heading_path    TEXT NOT NULL DEFAULT '',
  content         TEXT NOT NULL,
  content_hash    TEXT NOT NULL,
  source_path     TEXT NOT NULL,
  source_updated_at TIMESTAMPTZ NOT NULL,
  occurred_at     TIMESTAMPTZ,
  classification  TEXT NOT NULL
                    CHECK (classification IN ('private_github','review_before_commit')),
  token_count     INTEGER NOT NULL CHECK (token_count > 0),
  confidence      REAL NOT NULL DEFAULT 1.0,
  -- Full-text search vector (auto-maintained by trigger)
  fts_vector      TSVECTOR
);

CREATE INDEX IF NOT EXISTS idx_chunk_version  ON chunks(version_id);
CREATE INDEX IF NOT EXISTS idx_chunk_doc      ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_occurred ON chunks(occurred_at);
CREATE INDEX IF NOT EXISTS idx_chunk_fts      ON chunks USING GIN(fts_vector);

-- Trigger: maintain fts_vector automatically
CREATE OR REPLACE FUNCTION chunks_fts_update() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.fts_vector :=
    setweight(to_tsvector('english', coalesce(NEW.heading_path, '')), 'A') ||
    setweight(to_tsvector('english', NEW.content), 'B');
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chunks_fts ON chunks;
CREATE TRIGGER trg_chunks_fts
  BEFORE INSERT OR UPDATE OF heading_path, content ON chunks
  FOR EACH ROW EXECUTE FUNCTION chunks_fts_update();

-- ── Chunk embeddings ──────────────────────────────────────────────────────────
-- dimensions column records the actual vector size; HNSW built after data exists
CREATE TABLE IF NOT EXISTS chunk_embeddings (
  embedding_id  TEXT PRIMARY KEY,
  chunk_id      TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  model         TEXT NOT NULL,               -- e.g. "Qwen3-Embedding-0.6B"
  model_version TEXT NOT NULL,
  dimensions    INTEGER NOT NULL,
  embedding     vector(1024),               -- sized for Qwen3-0.6B/BGE-M3; ALTER if needed
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chunk_id, model, model_version)
);
-- HNSW index created AFTER representative data loaded (see ingest.py build_hnsw)
-- CREATE INDEX idx_emb_hnsw ON chunk_embeddings USING hnsw (embedding vector_cosine_ops);

-- ── Entities ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS entities (
  entity_id   TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,                 -- person|project|event|document|concept
  name        TEXT NOT NULL,
  aliases     TEXT[] NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_entity_kind ON entities(kind);
CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name);

CREATE TABLE IF NOT EXISTS entity_mentions (
  mention_id  TEXT PRIMARY KEY,
  entity_id   TEXT NOT NULL REFERENCES entities(entity_id),
  chunk_id    TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  span_start  INTEGER,
  span_end    INTEGER,
  confidence  REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_mention_entity ON entity_mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_mention_chunk  ON entity_mentions(chunk_id);

CREATE TABLE IF NOT EXISTS relations (
  relation_id  TEXT PRIMARY KEY,
  subject_id   TEXT NOT NULL REFERENCES entities(entity_id),
  predicate    TEXT NOT NULL,
  object_id    TEXT NOT NULL REFERENCES entities(entity_id),
  chunk_id     TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
  confidence   REAL NOT NULL DEFAULT 1.0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Ingestion jobs ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_jobs (
  job_id       TEXT PRIMARY KEY,
  source_id    TEXT NOT NULL REFERENCES sources(source_id),
  started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at  TIMESTAMPTZ,
  status       TEXT NOT NULL DEFAULT 'running'
                 CHECK (status IN ('running','ok','error','partial')),
  cursor       TEXT,                        -- last processed key for resumable scans
  changed_ct   INTEGER NOT NULL DEFAULT 0,
  inserted_ct  INTEGER NOT NULL DEFAULT 0,
  updated_ct   INTEGER NOT NULL DEFAULT 0,
  deleted_ct   INTEGER NOT NULL DEFAULT 0,
  error_ct     INTEGER NOT NULL DEFAULT 0,
  errors       JSONB NOT NULL DEFAULT '[]',
  notes        TEXT
);

-- ── Retrieval benchmark ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS retrieval_benchmark (
  run_id        TEXT PRIMARY KEY,
  run_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  system        TEXT NOT NULL,               -- A|B|C|D
  ablation      TEXT NOT NULL,               -- lexical|dense|hybrid|hybrid+rerank|...
  corpus_size   INTEGER NOT NULL,
  query_family  TEXT NOT NULL,
  query_text    TEXT NOT NULL,               -- synthetic/redacted
  relevant_ids  TEXT[] NOT NULL,             -- expected chunk_ids
  retrieved_ids TEXT[] NOT NULL,             -- returned chunk_ids
  recall_5      REAL, recall_10 REAL, recall_20 REAL,
  mrr           REAL, ndcg_10   REAL,
  p50_ms        REAL, p95_ms    REAL,
  storage_bytes BIGINT,
  cpu_pct       REAL, ram_bytes BIGINT,
  notes         TEXT
);

-- ── Grants ───────────────────────────────────────────────────────────────────
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nk_reader;
GRANT SELECT, INSERT, UPDATE, DELETE ON
  sources, documents, document_versions, chunks, chunk_embeddings,
  entities, entity_mentions, relations, ingestion_jobs, retrieval_benchmark
TO nk_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO nk_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nk_writer;

COMMIT;
