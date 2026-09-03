# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 2
"""Backfill dense embeddings for chunks that lack them, per (model, model_version).

Idempotent: only embeds chunks missing a row for the target model/version.
Records timing and peak RSS so cost is measurable, not assumed.
"""
from __future__ import annotations

import argparse
import logging
import os
import resource
import sys
import time
import uuid

# Repository root, derived from this file. No hardcoded host path (R24).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from NIZAM__system.retrieval.embed import get_embedder, model_version_of

log = logging.getLogger("embed_backfill")


def _vec_literal(v: list[float]) -> str:
    """pgvector text input format."""
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def backfill(dsn: str, model_name: str, batch_size: int = 32, limit: int | None = None) -> dict:
    import psycopg2

    emb = get_embedder(model_name)
    mv = model_version_of(model_name)
    rss_after_load = _rss_mb()

    conn = psycopg2.connect(dsn)
    stats = {
        "model": model_name,
        "model_version": mv,
        "dimensions": emb.dim,
        "embedded": 0,
        "batches": 0,
        "embed_ms": 0.0,
        "db_ms": 0.0,
    }
    t_all = time.monotonic()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT c.chunk_id, c.content
                FROM chunks c
                LEFT JOIN chunk_embeddings ce
                  ON ce.chunk_id = c.chunk_id
                 AND ce.model = %s AND ce.model_version = %s
                WHERE ce.embedding_id IS NULL
                ORDER BY c.chunk_id
            """
            params = [model_name, mv]
            if limit:
                sql += " LIMIT %s"
                params.append(limit)
            cur.execute(sql, params)
            todo = cur.fetchall()

        log.info("chunks needing embeddings: %d", len(todo))

        for i in range(0, len(todo), batch_size):
            batch = todo[i:i + batch_size]
            ids = [r[0] for r in batch]
            texts = [r[1] for r in batch]

            t0 = time.monotonic()
            vecs = emb.embed_passages(texts)
            stats["embed_ms"] += (time.monotonic() - t0) * 1000

            t1 = time.monotonic()
            with conn.cursor() as cur:
                for cid, vec in zip(ids, vecs):
                    cur.execute(
                        """
                        INSERT INTO chunk_embeddings
                          (embedding_id, chunk_id, model, model_version, dimensions, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id, model, model_version) DO NOTHING
                        """,
                        (str(uuid.uuid4()), cid, model_name, mv, emb.dim, _vec_literal(vec)),
                    )
            conn.commit()
            stats["db_ms"] += (time.monotonic() - t1) * 1000
            stats["embedded"] += len(batch)
            stats["batches"] += 1
            log.info("batch %d: +%d (total %d)", stats["batches"], len(batch), stats["embedded"])
    finally:
        conn.close()

    stats["total_ms"] = (time.monotonic() - t_all) * 1000
    stats["rss_after_model_load_mb"] = round(rss_after_load, 1)
    stats["rss_peak_mb"] = round(_rss_mb(), 1)
    if stats["embedded"]:
        stats["ms_per_chunk"] = round(stats["embed_ms"] / stats["embedded"], 2)
        stats["chunks_per_sec"] = round(stats["embedded"] / (stats["embed_ms"] / 1000.0), 2)
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-large")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dsn", default=os.environ.get("NIZAM_KNOWLEDGE_DSN"))
    args = ap.parse_args()

    if not args.dsn:
        raise SystemExit("NIZAM_KNOWLEDGE_DSN not set and --dsn not provided")

    stats = backfill(args.dsn, args.model, args.batch_size, args.limit)
    import json
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
