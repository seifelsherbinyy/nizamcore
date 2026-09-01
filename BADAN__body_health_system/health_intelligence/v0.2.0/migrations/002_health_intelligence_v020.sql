-- migrations/002_health_intelligence_v020.sql
-- Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (BADAN / Health Intelligence)
-- Phase: cloud-first reconciliation — VPS operational plane
--
-- ADDITIVE ONLY. Does not alter or drop any Phase-3 table, because the live
-- read-only MCP server (personal-health-mcp) queries whoop_* and daily_features.
--
-- Storage classes (v0.2 §2):
--   these tables are vps_private / strict_local == VPS-only. Never Drive-synced raw.
--   Only classified, derived knowledge artifacts may be copied to Drive.

BEGIN;

-- ── Deterministic windowed feature vectors ───────────────────────────────────
-- One row per Cairo planning date. `vector` holds the schema-0.2.0 payload with
-- windows {3,7,14,30,90}. Stored as JSONB so the metric set can evolve under a
-- methods_version without a migration per metric.
CREATE TABLE IF NOT EXISTS daily_feature_vectors (
  planning_date     DATE PRIMARY KEY,
  schema_version    TEXT        NOT NULL DEFAULT '0.2.0',
  timezone          TEXT        NOT NULL DEFAULT 'Africa/Cairo',
  methods_version   TEXT        NOT NULL,
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  vector            JSONB       NOT NULL,
  data_quality      JSONB       NOT NULL,
  source_refs       TEXT[]      NOT NULL DEFAULT '{}',
  privacy_level     TEXT        NOT NULL DEFAULT 'strict_local',
  CONSTRAINT dfv_privacy_vps_only CHECK (privacy_level = 'strict_local')
);
CREATE INDEX IF NOT EXISTS idx_dfv_computed ON daily_feature_vectors (computed_at DESC);

-- ── Journal feature records (human-authored signal) ──────────────────────────
-- Journals are human text. We store extracted deterministic features and an
-- explicit pointer to the source; we never store LLM-invented health values.
CREATE TABLE IF NOT EXISTS journal_feature_records (
  record_id         TEXT PRIMARY KEY,
  cairo_local_date  DATE        NOT NULL,
  source            TEXT        NOT NULL,
  source_ref        TEXT,
  observed_at       TIMESTAMPTZ,
  ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  features          JSONB       NOT NULL DEFAULT '{}',
  symptom_flags     TEXT[]      NOT NULL DEFAULT '{}',
  quality_flags     TEXT[]      NOT NULL DEFAULT '{}',
  privacy_level     TEXT        NOT NULL DEFAULT 'strict_local'
);
CREATE INDEX IF NOT EXISTS idx_jfr_date ON journal_feature_records (cairo_local_date DESC);

-- ── Hypothesis / counterevidence ledger ─────────────────────────────────────
-- Associations never auto-promote to causal. status is advanced only by an
-- explicit human decision or a designed experiment.
CREATE TABLE IF NOT EXISTS health_hypotheses (
  hypothesis_id     TEXT PRIMARY KEY,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  statement         TEXT        NOT NULL,
  candidate_x       TEXT,
  outcome_y         TEXT,
  lag_definition    TEXT,
  status            TEXT        NOT NULL DEFAULT 'proposed',
  evidence          JSONB       NOT NULL DEFAULT '[]',
  counterevidence   JSONB       NOT NULL DEFAULT '[]',
  confounders       JSONB       NOT NULL DEFAULT '[]',
  confidence        JSONB       NOT NULL DEFAULT '{}',
  privacy_level     TEXT        NOT NULL DEFAULT 'strict_local',
  CONSTRAINT hh_status_valid CHECK (
    status IN ('proposed','under_observation','supported','contradicted','retired')
  )
);

-- ── Behavior interventions + human-only adherence ───────────────────────────
-- completed_at is written ONLY from an explicit human record. Calendar
-- occurrence / device movement is NOT completion (metric spec, adherence).
CREATE TABLE IF NOT EXISTS behavior_interventions (
  intervention_id   TEXT PRIMARY KEY,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  title             TEXT        NOT NULL,
  rationale         TEXT,
  target_metric     TEXT,
  due_date          DATE,
  approved_by_human BOOLEAN     NOT NULL DEFAULT false,
  completed_at      TIMESTAMPTZ,
  completion_source TEXT,
  privacy_level     TEXT        NOT NULL DEFAULT 'strict_local',
  CONSTRAINT bi_completion_is_human CHECK (
    completed_at IS NULL OR completion_source = 'human_explicit'
  )
);
CREATE INDEX IF NOT EXISTS idx_bi_due ON behavior_interventions (due_date DESC);

-- ── Run receipts (deterministic run state) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS run_receipts (
  run_id            TEXT PRIMARY KEY,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at       TIMESTAMPTZ,
  planning_date     DATE,
  status            TEXT        NOT NULL DEFAULT 'RUNNING',
  steps             JSONB       NOT NULL DEFAULT '[]',
  error             TEXT,
  CONSTRAINT rr_status_valid CHECK (
    status IN ('RUNNING','OK','SYNC_PENDING','FAILED_SYNC','FAILED')
  )
);
CREATE INDEX IF NOT EXISTS idx_rr_started ON run_receipts (started_at DESC);

-- ── Sync receipts (Drive write + mandatory readback) ────────────────────────
-- A Drive write is only OK after the destination is read back and verified.
CREATE TABLE IF NOT EXISTS sync_receipts (
  sync_id           TEXT PRIMARY KEY,
  run_id            TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  artifact_kind     TEXT        NOT NULL,
  local_path        TEXT,
  storage_class     TEXT        NOT NULL,
  destination       TEXT,
  drive_file_id     TEXT,
  content_sha256    TEXT,
  readback_ok       BOOLEAN     NOT NULL DEFAULT false,
  readback_sha256   TEXT,
  status            TEXT        NOT NULL DEFAULT 'PENDING',
  attempts          INT         NOT NULL DEFAULT 0,
  error             TEXT,
  CONSTRAINT sr_status_valid CHECK (
    status IN ('PENDING','OK','RETRY','FAILED')
  ),
  -- Cannot claim OK without a verified readback. Fail closed.
  CONSTRAINT sr_ok_requires_readback CHECK (
    status <> 'OK' OR (readback_ok = true AND content_sha256 = readback_sha256)
  ),
  -- Secrets must never be synced to Drive.
  CONSTRAINT sr_no_secret_to_drive CHECK (storage_class <> 'vps_secret')
);
CREATE INDEX IF NOT EXISTS idx_sr_status ON sync_receipts (status, created_at DESC);

-- ── Role grants for the new tables ──────────────────────────────────────────
-- whoop_reader backs the read-only MCP server exposed to Hermes.
-- whoop_writer backs the ingestion/compute workers.
GRANT SELECT ON ALL TABLES    IN SCHEMA public TO whoop_reader;
GRANT ALL    ON ALL TABLES    IN SCHEMA public TO whoop_writer;
GRANT ALL    ON ALL SEQUENCES IN SCHEMA public TO whoop_writer;

COMMIT;
