# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Hybrid retrieval: lexical (FTS) + dense (pgvector) + RRF + rerank + expansion.

Connection string: NIZAM_KNOWLEDGE_DSN env var (read-only nk_reader credentials).
Embedding fn:      NIZAM_EMBED_FN env var → Python dotted path, or inject at call time.

No SQL is exposed to callers. Result counts and text volume are capped.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Callable, Optional

try:
    import psycopg2, psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False

from .model import SearchResult, ContextPacket

log = logging.getLogger(__name__)

_MAX_LEXICAL   = 20
_MAX_DENSE     = 20
_MAX_FINAL     = 10
_MAX_CONTENT_CHARS = 4000   # per chunk in context packet (prompt-injection limit)

_RRF_K = 60  # standard RRF constant


def _rrf(rank: int, k: int = _RRF_K) -> float:
    return 1.0 / (k + rank)


def _get_connection(dsn: Optional[str] = None):
    if not HAS_PG:
        raise RuntimeError("psycopg2 not installed.")
    dsn = dsn or os.environ["NIZAM_KNOWLEDGE_DSN"]
    return psycopg2.connect(dsn)


# ── Lexical leg ───────────────────────────────────────────────────────────────
def _lexical_search(
    cur, query: str, classification_filter: list[str], limit: int
) -> list[tuple[str, float]]:
    """Return [(chunk_id, ts_rank)] ordered by rank desc."""
    cur.execute("""
        SELECT c.chunk_id,
               ts_rank(c.fts_vector, websearch_to_tsquery('english', %s)) AS rank
        FROM chunks c
        JOIN document_versions dv ON c.version_id = dv.version_id
        WHERE c.fts_vector @@ websearch_to_tsquery('english', %s)
          AND dv.is_current = true
          AND c.classification = ANY(%s)
        ORDER BY rank DESC
        LIMIT %s
    """, (query, query, classification_filter, limit))
    return [(r[0], r[1]) for r in cur.fetchall()]


# ── Dense leg ─────────────────────────────────────────────────────────────────
def _dense_search(
    cur,
    embedding: list[float],
    model: str,
    model_version: str,
    classification_filter: list[str],
    limit: int,
) -> list[tuple[str, float]]:
    """Return [(chunk_id, cosine_similarity)] ordered desc."""
    cur.execute("""
        SELECT ce.chunk_id,
               1 - (ce.embedding <=> %s::vector) AS similarity
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        JOIN document_versions dv ON c.version_id = dv.version_id
        WHERE ce.model = %s AND ce.model_version = %s
          AND dv.is_current = true
          AND c.classification = ANY(%s)
        ORDER BY ce.embedding <=> %s::vector
        LIMIT %s
    """, (embedding, model, model_version, classification_filter, embedding, limit))
    return [(r[0], r[1]) for r in cur.fetchall()]


# ── RRF fusion ────────────────────────────────────────────────────────────────
def _fuse(
    lexical: list[tuple[str, float]],
    dense: list[tuple[str, float]],
) -> list[tuple[str, float, Optional[int], Optional[int]]]:
    """Return [(chunk_id, rrf_score, lexical_rank, dense_rank)] sorted by rrf desc."""
    scores: dict[str, float] = {}
    lex_rank: dict[str, int] = {}
    den_rank: dict[str, int] = {}
    for rank, (cid, _) in enumerate(lexical, 1):
        scores[cid] = scores.get(cid, 0.0) + _rrf(rank)
        lex_rank[cid] = rank
    for rank, (cid, _) in enumerate(dense, 1):
        scores[cid] = scores.get(cid, 0.0) + _rrf(rank)
        den_rank[cid] = rank
    return sorted(
        [(cid, sc, lex_rank.get(cid), den_rank.get(cid)) for cid, sc in scores.items()],
        key=lambda x: -x[1]
    )


# ── Fetch full chunk rows ─────────────────────────────────────────────────────
def _fetch_chunks(cur, chunk_ids: list[str]) -> dict[str, dict]:
    cur.execute("""
        SELECT c.chunk_id, c.document_id, c.source_path, c.heading_path,
               c.content, c.classification, c.source_updated_at, c.occurred_at,
               c.version_id, c.content_hash, dv.is_current
        FROM chunks c
        JOIN document_versions dv ON c.version_id = dv.version_id
        WHERE c.chunk_id = ANY(%s)
    """, (chunk_ids,))
    return {r[0]: {
        "chunk_id": r[0], "document_id": r[1], "source_path": r[2],
        "heading_path": r[3],
        "content": r[4][:_MAX_CONTENT_CHARS],  # cap content (prompt-injection limit)
        "classification": r[5], "source_updated_at": r[6], "occurred_at": r[7],
        "version_id": r[8], "content_hash": r[9], "is_current": r[10],
    } for r in cur.fetchall()}


# ── Reranker (cross-encoder stub — replaces with real model in production) ────
def _rerank_stub(
    query: str,
    candidates: list[tuple[str, float, Optional[int], Optional[int]]],
    chunk_rows: dict[str, dict],
) -> list[tuple[str, float, Optional[int], Optional[int], float]]:
    """Returns candidates with a stub rerank_score = rrf_score (identity).
    Replace this function with a real cross-encoder for production reranking.
    """
    return [(cid, rrf, lr, dr, rrf) for cid, rrf, lr, dr in candidates]


def _rerank_real(
    query: str,
    candidates: list[tuple[str, float, Optional[int], Optional[int]]],
    chunk_rows: dict[str, dict],
    rerank_fn,
) -> list[tuple[str, float, Optional[int], Optional[int], float]]:
    """Rescore candidates with an injected cross-encoder.

    rerank_fn(query, [passages]) -> [scores]. Candidates whose chunk text is
    unavailable keep their RRF score so they are never silently dropped.
    """
    scorable, passages = [], []
    for cid, rrf, lr, dr in candidates:
        row = chunk_rows.get(cid)
        if row is None:
            continue
        scorable.append((cid, rrf, lr, dr))
        passages.append(row["content"])

    if not scorable:
        return [(cid, rrf, lr, dr, rrf) for cid, rrf, lr, dr in candidates]

    scores = rerank_fn(query, passages)
    out = []
    for (cid, rrf, lr, dr), sc in zip(scorable, scores):
        out.append((cid, rrf, lr, dr, float(sc)))
    # candidates without fetched rows retain rrf as rerank score
    have = {c[0] for c in scorable}
    for cid, rrf, lr, dr in candidates:
        if cid not in have:
            out.append((cid, rrf, lr, dr, rrf))
    return out


# ── Context expansion ─────────────────────────────────────────────────────────
def _expand_neighbors(cur, chunk_id: str, already: set[str]) -> list[dict]:
    cur.execute("""
        SELECT c.chunk_id, c.document_id, c.source_path, c.heading_path,
               c.content, c.classification, c.source_updated_at, c.occurred_at,
               c.version_id, c.content_hash, dv.is_current
        FROM chunks c
        JOIN document_versions dv ON c.version_id = dv.version_id
        WHERE c.chunk_id IN (
          SELECT prev_chunk_id FROM chunks WHERE chunk_id = %s
          UNION
          SELECT next_chunk_id FROM chunks WHERE chunk_id = %s
        ) AND c.chunk_id != ALL(%s)
    """, (chunk_id, chunk_id, list(already)))
    return [{
        "chunk_id": r[0], "document_id": r[1], "source_path": r[2],
        "heading_path": r[3], "content": r[4][:_MAX_CONTENT_CHARS],
        "classification": r[5], "source_updated_at": r[6], "occurred_at": r[7],
        "version_id": r[8], "content_hash": r[9], "is_current": r[10],
    } for r in cur.fetchall()]


# ── Public API ────────────────────────────────────────────────────────────────
def hybrid_search(
    query: str,
    embed_fn: Optional[Callable[[str], list[float]]] = None,
    model: str = "Qwen3-Embedding-0.6B",
    model_version: str = "v1",
    classification_filter: Optional[list[str]] = None,
    current_only: bool = True,
    expand_neighbors: bool = False,
    rerank_fn: Optional[Callable[[str, list[str]], list[float]]] = None,
    dsn: Optional[str] = None,
    lexical_limit: int = _MAX_LEXICAL,
    dense_limit: int = _MAX_DENSE,
    final_limit: int = _MAX_FINAL,
) -> ContextPacket:
    """Run lexical + dense + RRF + rerank retrieval.

    embed_fn: callable(query_str) -> list[float].  If None, dense leg is skipped.
    classification_filter: defaults to ['private_github','review_before_commit'].
    Returns ContextPacket with provenance-rich SearchResults.
    """
    if classification_filter is None:
        classification_filter = ["private_github", "review_before_commit"]

    pkt = ContextPacket(query=query)
    t0 = time.monotonic()

    conn = _get_connection(dsn)
    try:
        with conn.cursor() as cur:
            # Lexical leg
            t_lex = time.monotonic()
            lex = _lexical_search(cur, query, classification_filter, lexical_limit)
            pkt.lexical_count = len(lex)
            pkt.stage_latencies_ms["lexical"] = (time.monotonic() - t_lex) * 1000

            # Dense leg
            dense: list[tuple[str, float]] = []
            if embed_fn is not None:
                t_emb = time.monotonic()
                vec = embed_fn(query)
                pkt.stage_latencies_ms["embed"] = (time.monotonic() - t_emb) * 1000
                t_den = time.monotonic()
                dense = _dense_search(cur, vec, model, model_version,
                                      classification_filter, dense_limit)
                pkt.dense_count = len(dense)
                pkt.stage_latencies_ms["dense"] = (time.monotonic() - t_den) * 1000

            # Overlap
            lex_ids  = {c for c, _ in lex}
            den_ids  = {c for c, _ in dense}
            pkt.overlap = len(lex_ids & den_ids)

            # RRF fusion
            t_fuse = time.monotonic()
            fused = _fuse(lex, dense)
            pkt.fused_count = len(fused)
            pkt.stage_latencies_ms["fuse"] = (time.monotonic() - t_fuse) * 1000

            # Fetch chunk rows for top candidates
            top_ids = [cid for cid, _, _, _ in fused[:final_limit * 2]]
            rows = _fetch_chunks(cur, top_ids)

            # Privacy double-check (fail closed)
            before = len(fused)
            fused = [f for f in fused if f[0] in rows
                     and rows[f[0]]["classification"] in classification_filter]
            pkt.privacy_filtered_count = before - len(fused)
            if pkt.privacy_filtered_count:
                log.warning("privacy_filtered=%d candidates removed post-fetch",
                            pkt.privacy_filtered_count)

            # Rerank
            t_rerank = time.monotonic()
            cands = fused[:final_limit * 2]
            if rerank_fn is not None:
                reranked = _rerank_real(query, cands, rows, rerank_fn)
            else:
                reranked = _rerank_stub(query, cands, rows)
            reranked.sort(key=lambda x: -x[4])
            pkt.reranked_count = len(reranked)
            pkt.stage_latencies_ms["rerank"] = (time.monotonic() - t_rerank) * 1000

            # Build results
            seen: set[str] = set()
            for cid, rrf_score, lex_rank, den_rank, rerank_score in reranked[:final_limit]:
                if cid not in rows:
                    continue
                r = rows[cid]
                pkt.results.append(SearchResult(
                    chunk_id=cid, document_id=r["document_id"],
                    source_path=r["source_path"], heading_path=r["heading_path"],
                    content=r["content"], classification=r["classification"],
                    is_current=r["is_current"],
                    source_updated_at=r["source_updated_at"],
                    occurred_at=r["occurred_at"],
                    lexical_rank=lex_rank, dense_rank=den_rank,
                    rrf_score=rrf_score, rerank_score=rerank_score,
                    version_id=r["version_id"], content_hash=r["content_hash"],
                ))
                seen.add(cid)

            # Optional neighbor expansion
            if expand_neighbors:
                t_exp = time.monotonic()
                for sr in list(pkt.results):
                    for nb in _expand_neighbors(cur, sr.chunk_id, seen):
                        seen.add(nb["chunk_id"])
                        pkt.results.append(SearchResult(
                            chunk_id=nb["chunk_id"], document_id=nb["document_id"],
                            source_path=nb["source_path"], heading_path=nb["heading_path"],
                            content=nb["content"], classification=nb["classification"],
                            is_current=nb["is_current"],
                            source_updated_at=nb["source_updated_at"],
                            occurred_at=nb["occurred_at"],
                            version_id=nb["version_id"], content_hash=nb["content_hash"],
                        ))
                pkt.stage_latencies_ms["expand"] = (time.monotonic() - t_exp) * 1000

    finally:
        conn.close()

    pkt.stage_latencies_ms["total"] = (time.monotonic() - t0) * 1000
    if not pkt.results:
        pkt.empty_result_reason = "no matches after fusion+filter"
    return pkt
