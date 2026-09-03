# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Ingestion pipeline: discover → HIMAYAH gate → hash → compare → chunk → upsert.

Uses psycopg2 for PostgreSQL access. Connection string is read from the
environment variable NIZAM_KNOWLEDGE_DSN. Never hard-coded.

Never commits to or mutates canonical source files.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False

from .chunking import chunk_document
from .himayah import classify_for_ingest, HimayahViolation
from .model import IngestReceipt

log = logging.getLogger(__name__)

_PERMITTED_EXTENSIONS = {".md", ".json", ".jsonl", ".yaml", ".yml", ".py", ".ts", ".sql", ".txt"}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _doc_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".md": "markdown", ".markdown": "markdown",
        ".json": "json", ".jsonl": "jsonl",
        ".yaml": "yaml", ".yml": "yaml",
        ".py": "code", ".ts": "code", ".js": "code", ".sql": "code",
    }.get(ext, "plaintext")


def _get_connection(dsn: Optional[str] = None):
    if not HAS_PG:
        raise RuntimeError("psycopg2 not installed; cannot connect to PostgreSQL.")
    dsn = dsn or os.environ["NIZAM_KNOWLEDGE_DSN"]
    return psycopg2.connect(dsn)


def ingest_file(
    conn,
    source_id: str,
    rel_path: str,
    abs_path: str,
    dry_run: bool = False,
) -> IngestReceipt:
    """Ingest a single file: HIMAYAH gate → read → hash → version compare → chunk → upsert."""
    t0 = time.monotonic()
    errors: list[str] = []

    # 1. HIMAYAH gate (raises on violation — caller catches for reconciliation)
    classification = classify_for_ingest(rel_path)

    # 2. Read file
    try:
        text = Path(abs_path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return IngestReceipt(
            source=source_id, path=rel_path, content_hash="",
            version_id="", chunk_count=0, embed_count=0, skipped=True,
            errors=[f"read error: {e}"],
        )

    content_hash = _sha256(text)
    source_updated_at = datetime.fromtimestamp(
        Path(abs_path).stat().st_mtime, tz=timezone.utc
    )

    # Derive source root from abs_path and rel_path
    _parts = len(Path(rel_path).parts)
    _source_root = str(Path(abs_path).parents[_parts - 1])

    with conn.cursor() as cur:
        # 2b. Ensure source row exists (idempotent)
        cur.execute("""
            INSERT INTO sources (source_id, name, host_path, classification)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id) DO UPDATE SET last_scanned = now()
        """, (source_id, source_id, _source_root, classification))

        # 3. Upsert document record
        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{rel_path}"))
        doc_type = _doc_type(rel_path)
        module = rel_path.split("/")[0] if "/" in rel_path else rel_path

        cur.execute("""
            INSERT INTO documents (document_id, source_id, canonical_key, title, doc_type,
                                   module, classification)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, canonical_key) DO NOTHING
        """, (document_id, source_id, rel_path, Path(rel_path).stem, doc_type,
              module, classification))

        # 4. Check if content changed
        cur.execute("""
            SELECT version_id FROM document_versions
            WHERE document_id = %s AND content_hash = %s AND is_current = true
        """, (document_id, content_hash))
        existing = cur.fetchone()

        if existing:
            conn.commit()
            return IngestReceipt(
                source=source_id, path=rel_path, content_hash=content_hash,
                version_id=existing[0], chunk_count=0, embed_count=0,
                skipped=True, duration_ms=(time.monotonic() - t0) * 1000
            )

        if dry_run:
            conn.rollback()
            return IngestReceipt(
                source=source_id, path=rel_path, content_hash=content_hash,
                version_id="(dry_run)", chunk_count=-1, embed_count=0, skipped=False
            )

        # 5. Mark previous versions non-current
        version_id = str(uuid.uuid4())
        cur.execute("""
            UPDATE document_versions SET is_current = false, valid_to = now()
            WHERE document_id = %s AND is_current = true
        """, (document_id,))

        # 6. Insert new version
        cur.execute("""
            INSERT INTO document_versions
              (version_id, document_id, content_hash, source_updated_at, classification)
            VALUES (%s, %s, %s, %s, %s)
        """, (version_id, document_id, content_hash, source_updated_at, classification))

        # 7. Produce chunks
        chunks = chunk_document(
            text=text,
            source_path=rel_path,
            version_id=version_id,
            document_id=document_id,
            classification=classification,
            source_updated_at=source_updated_at,
        )

        # 8. Insert chunks: two-pass to avoid self-referential FK on next_chunk_id
        for ck in chunks:
            cur.execute("""
                INSERT INTO chunks
                  (chunk_id, version_id, document_id, parent_chunk_id,
                   prev_chunk_id, next_chunk_id, ordinal, heading_path,
                   content, content_hash, source_path, source_updated_at,
                   occurred_at, classification, token_count, confidence)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                ck.chunk_id, ck.version_id, ck.document_id, ck.parent_chunk_id,
                ck.prev_chunk_id, None,
                ck.ordinal, ck.heading_path,
                ck.content, ck.content_hash, ck.source_path, ck.source_updated_at,
                ck.occurred_at, ck.classification, ck.token_count, ck.confidence,
            ))
        # Second pass: now all chunk rows exist; set next_chunk_id
        for ck in chunks:
            if ck.next_chunk_id:
                cur.execute(
                    "UPDATE chunks SET next_chunk_id=%s WHERE chunk_id=%s",
                    (ck.next_chunk_id, ck.chunk_id)
                )

        conn.commit()
        log.info("ingested %s -> version=%s chunks=%d", rel_path, version_id, len(chunks))
        return IngestReceipt(
            source=source_id, path=rel_path, content_hash=content_hash,
            version_id=version_id, chunk_count=len(chunks), embed_count=0,
            skipped=False, duration_ms=(time.monotonic() - t0) * 1000,
        )


def run_ingest(
    source_id: str,
    source_root: str,
    dsn: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Discover all permitted files under source_root and ingest each."""
    root = Path(source_root)
    conn = _get_connection(dsn)
    results: list[IngestReceipt] = []
    blocked: list[tuple[str, str]] = []

    try:
        for fpath in sorted(root.rglob("*")):
            if not fpath.is_file():
                continue
            if fpath.suffix.lower() not in _PERMITTED_EXTENSIONS:
                continue
            rel = str(fpath.relative_to(root)).replace("\\", "/")
            try:
                receipt = ingest_file(conn, source_id, rel, str(fpath), dry_run)
                results.append(receipt)
            except HimayahViolation as e:
                blocked.append((rel, str(e)))
            except Exception as e:
                log.error("ingest error %s: %s", rel, e)
                results.append(IngestReceipt(
                    source=source_id, path=rel, content_hash="",
                    version_id="", chunk_count=0, embed_count=0, skipped=True,
                    errors=[str(e)]
                ))
    finally:
        conn.close()

    return {
        "total": len(results) + len(blocked),
        "ingested": sum(1 for r in results if not r.skipped and not r.errors),
        "skipped": sum(1 for r in results if r.skipped),
        "blocked": len(blocked),
        "errors": sum(1 for r in results if r.errors),
        "receipts": [r.__dict__ for r in results],
        "blocked_paths": blocked,
    }


def build_hnsw(conn, model: str, model_version: str) -> None:
    """Build HNSW index on chunk_embeddings after data is loaded.

    Safe to call when index already exists (IF NOT EXISTS).
    """
    idx = f"idx_emb_hnsw_{model.replace('-','_').replace('/','_')}_{model_version}"
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx}
            ON chunk_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m=16, ef_construction=64)
            WHERE model=%s AND model_version=%s
        """, (model, model_version))
    conn.commit()
    log.info("HNSW index %s built", idx)
