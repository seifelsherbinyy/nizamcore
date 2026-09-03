# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 2
"""Benchmark runner — Wave 2: lexical / dense / hybrid / hybrid+rerank.

Measures Recall@K, MRR, nDCG@10, p50/p95 latency, storage, CPU, peak RSS,
plus update and delete correctness, and grounding completeness.

METRIC NOTE (fixed in Wave 2): retrieved chunk paths are DEDUPLICATED before
scoring. Wave 1 counted each chunk of a matching document as a separate hit,
which produced recall > 1.0 and understated MRR. Metrics here are per-document.
"""
from __future__ import annotations

import json
import logging
import math
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("bench")
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parents[2]))

from NIZAM__system.retrieval.bench.fixtures import (
    SYNTHETIC_DOCS, BENCHMARK_QUERIES, write_fixtures,
)
from NIZAM__system.retrieval.ingest import run_ingest, ingest_file
from NIZAM__system.retrieval.query import hybrid_search

EMBED_MODEL = os.environ.get("BENCH_EMBED_MODEL", "intfloat/multilingual-e5-large")
RERANK_MODEL = os.environ.get("BENCH_RERANK_MODEL", "jinaai/jina-reranker-v2-base-multilingual")


# ── metrics (per-document, deduplicated) ─────────────────────────────────────
def _dedupe(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(paths))


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for r in retrieved[:k] if r in relevant)
    return min(hits / len(relevant), 1.0)


def mrr(retrieved: list[str], relevant: set[str]) -> float:
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    dcg = sum((1 if r in relevant else 0) / math.log2(i + 1)
              for i, r in enumerate(retrieved[:k], 1))
    idcg = sum(1.0 / math.log2(i + 1)
               for i in range(1, min(len(relevant), k) + 1))
    return dcg / idcg if idcg > 0 else 0.0


def _pct(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(int(len(s) * q), len(s) - 1)
    return s[idx]


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _cpu_s() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


# ── storage ───────────────────────────────────────────────────────────────────
def storage_footprint(dsn: str) -> dict:
    import psycopg2
    out = {}
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT relname, pg_total_relation_size(c.oid)
                FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                ORDER BY 2 DESC
            """)
            tables = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute("""
                SELECT indexrelname, pg_relation_size(indexrelid)
                FROM pg_stat_user_indexes WHERE schemaname='public'
                ORDER BY 2 DESC
            """)
            indexes = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute("SELECT pg_database_size(current_database())")
            db_total = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM chunks")
            n_chunks = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM chunk_embeddings")
            n_emb = cur.fetchone()[0]
    finally:
        conn.close()
    out["db_total_bytes"] = db_total
    out["db_total_mb"] = round(db_total / 1048576, 2)
    out["tables_bytes"] = tables
    out["indexes_bytes"] = indexes
    out["chunks"] = n_chunks
    out["embeddings"] = n_emb
    if n_chunks:
        out["bytes_per_chunk"] = round(db_total / n_chunks, 1)
    return out


# ── update / delete correctness ───────────────────────────────────────────────
def update_delete_checks(dsn: str, corpus_root: str) -> dict:
    import psycopg2
    res = {"update": {}, "delete": {}}
    src = "bench_mutation_v1"
    rel = "NIZAM__system/docs/bench/mutating_doc.md"
    abs_p = Path(corpus_root) / rel
    abs_p.parent.mkdir(parents=True, exist_ok=True)

    conn = psycopg2.connect(dsn)
    try:
        # --- UPDATE: v1 then v2, old must be superseded, new must be current
        abs_p.write_text("# Mutation Test\n\nAlpha state before change.\n", encoding="utf-8")
        r1 = ingest_file(conn, src, rel, str(abs_p))
        abs_p.write_text("# Mutation Test\n\nBravo state after change.\n", encoding="utf-8")
        r2 = ingest_file(conn, src, rel, str(abs_p))

        with conn.cursor() as cur:
            cur.execute("""
                SELECT version_id, is_current FROM document_versions dv
                JOIN documents d ON d.document_id = dv.document_id
                WHERE d.source_id=%s AND d.canonical_key=%s
                ORDER BY dv.is_current DESC
            """, (src, rel))
            rows = cur.fetchall()
            current = [r[0] for r in rows if r[1]]
            superseded = [r[0] for r in rows if not r[1]]

            cur.execute("""
                SELECT count(*) FROM chunks c
                WHERE c.version_id = %s AND c.content LIKE %s
            """, (r2.version_id, "%Bravo%"))
            new_content_present = cur.fetchone()[0] > 0

            cur.execute("""
                SELECT count(*) FROM chunks c
                WHERE c.version_id = %s AND c.content LIKE %s
            """, (r1.version_id, "%Alpha%"))
            old_content_retained = cur.fetchone()[0] > 0

        res["update"] = {
            "v1_version": r1.version_id,
            "v2_version": r2.version_id,
            "distinct_versions": r1.version_id != r2.version_id,
            "exactly_one_current": len(current) == 1,
            "current_is_v2": current == [r2.version_id],
            "superseded_count": len(superseded),
            "new_content_indexed": new_content_present,
            "old_version_retained_for_history": old_content_retained,
        }
        res["update"]["PASS"] = all([
            res["update"]["distinct_versions"],
            res["update"]["exactly_one_current"],
            res["update"]["current_is_v2"],
            res["update"]["new_content_indexed"],
        ])

        # --- DELETE: removing the document must cascade chunks + embeddings
        with conn.cursor() as cur:
            cur.execute("""
                SELECT document_id FROM documents WHERE source_id=%s AND canonical_key=%s
            """, (src, rel))
            doc_id = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM chunks WHERE document_id=%s", (doc_id,))
            chunks_before = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) FROM chunk_embeddings ce
                JOIN chunks c ON c.chunk_id = ce.chunk_id WHERE c.document_id=%s
            """, (doc_id,))
            emb_before = cur.fetchone()[0]

            cur.execute("DELETE FROM documents WHERE document_id=%s", (doc_id,))
            conn.commit()

            cur.execute("SELECT count(*) FROM chunks WHERE document_id=%s", (doc_id,))
            chunks_after = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) FROM chunk_embeddings ce
                JOIN chunks c ON c.chunk_id = ce.chunk_id WHERE c.document_id=%s
            """, (doc_id,))
            emb_after = cur.fetchone()[0]

        res["delete"] = {
            "chunks_before": chunks_before,
            "chunks_after": chunks_after,
            "embeddings_before": emb_before,
            "embeddings_after": emb_after,
            "chunks_cascaded": chunks_after == 0,
            "embeddings_cascaded": emb_after == 0,
        }
        res["delete"]["PASS"] = chunks_after == 0 and emb_after == 0
    finally:
        conn.close()
    return res


# ── main ──────────────────────────────────────────────────────────────────────
def run(dsn: str, corpus_root: str, ablations: list[str]) -> dict:
    written = write_fixtures(corpus_root)
    log.info("wrote %d fixture files", len(written))

    run_id = f"bench_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    source_id = "bench_synthetic_v1"

    t0 = time.monotonic()
    ingest_result = run_ingest(source_id=source_id, source_root=corpus_root, dsn=dsn)
    ingest_ms = (time.monotonic() - t0) * 1000

    # ensure embeddings exist for the dense-capable ablations
    from NIZAM__system.retrieval.embed import get_embedder, model_version_of
    from NIZAM__system.retrieval.embed_backfill import backfill

    need_dense = any(a in ("dense", "hybrid", "hybrid_rerank") for a in ablations)
    embedder = None
    mv = None
    backfill_stats = None
    rss_after_embed = None
    if need_dense:
        bf_t = time.monotonic()
        backfill_stats = backfill(dsn, EMBED_MODEL)
        backfill_stats["wall_ms"] = round((time.monotonic() - bf_t) * 1000, 1)
        embedder = get_embedder(EMBED_MODEL)
        mv = model_version_of(EMBED_MODEL)
        rss_after_embed = round(_rss_mb(), 1)

    reranker = None
    rss_after_rerank = None
    if "hybrid_rerank" in ablations:
        from NIZAM__system.retrieval.embed import get_reranker
        reranker = get_reranker(RERANK_MODEL)
        # warm it
        reranker.score("warmup", ["warmup passage"])
        rss_after_rerank = round(_rss_mb(), 1)

    results = []
    for ab in ablations:
        use_dense = ab in ("dense", "hybrid", "hybrid_rerank")
        use_lex = ab in ("lexical", "hybrid", "hybrid_rerank")
        use_rr = ab == "hybrid_rerank"

        latencies, per_query = [], []
        cpu0 = _cpu_s()
        grounding_ok = True
        grounding_violations = []

        for q in BENCHMARK_QUERIES:
            # lexical-suppressed ablation: dense-only needs an unmatched FTS query
            kwargs = dict(
                dsn=dsn, final_limit=20, current_only=False,
                embed_fn=(embedder.embed_query if use_dense else None),
                rerank_fn=(reranker if use_rr else None),
            )
            if use_dense:
                kwargs["model"] = EMBED_MODEL
                kwargs["model_version"] = mv
            if not use_lex:
                kwargs["lexical_limit"] = 0

            t = time.monotonic()
            pkt = hybrid_search(query=q["text"], **kwargs)
            lat = (time.monotonic() - t) * 1000
            latencies.append(lat)

            got = _dedupe([r.source_path for r in pkt.results])
            rel = set(q["relevant_paths"])

            for r in pkt.results:
                if not (r.source_path and r.version_id and r.content_hash
                        and r.classification in ("private_github", "review_before_commit")):
                    grounding_ok = False
                    grounding_violations.append(r.chunk_id)

            per_query.append({
                "qid": q["qid"], "family": q["family"], "query": q["text"],
                "latency_ms": round(lat, 2),
                "results": len(pkt.results),
                "unique_docs": len(got),
                "lexical_count": pkt.lexical_count,
                "dense_count": pkt.dense_count,
                "hit": bool(set(got) & rel),
                "recall_5": round(recall_at_k(got, rel, 5), 4),
                "recall_10": round(recall_at_k(got, rel, 10), 4),
                "mrr": round(mrr(got, rel), 4),
                "ndcg_10": round(ndcg_at_k(got, rel, 10), 4),
                "top_doc": got[0] if got else None,
                "relevant": sorted(rel),
            })

        n = len(per_query)
        results.append({
            "run_id": f"{run_id}_{ab}",
            "ablation": ab,
            "embed_model": EMBED_MODEL if use_dense else None,
            "rerank_model": RERANK_MODEL if use_rr else None,
            "p50_ms": round(_pct(latencies, 0.50), 2),
            "p95_ms": round(_pct(latencies, 0.95), 2),
            "cpu_s": round(_cpu_s() - cpu0, 3),
            "queries_with_hit": sum(1 for q in per_query if q["hit"]),
            "hit_rate": round(sum(1 for q in per_query if q["hit"]) / n, 4),
            "avg_recall_5": round(sum(q["recall_5"] for q in per_query) / n, 4),
            "avg_recall_10": round(sum(q["recall_10"] for q in per_query) / n, 4),
            "avg_mrr": round(sum(q["mrr"] for q in per_query) / n, 4),
            "avg_ndcg_10": round(sum(q["ndcg_10"] for q in per_query) / n, 4),
            "grounding_complete": grounding_ok,
            "grounding_violations": grounding_violations,
            "per_query": per_query,
        })
        log.info("%-14s hit_rate=%.2f mrr=%.3f p50=%.1fms",
                 ab, results[-1]["hit_rate"], results[-1]["avg_mrr"], results[-1]["p50_ms"])

    mut = update_delete_checks(dsn, corpus_root)
    store = storage_footprint(dsn)

    report = {
        "schema": "nizam.retrieval_benchmark/v2",
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "corpus_docs": len(SYNTHETIC_DOCS),
        "corpus_queries": len(BENCHMARK_QUERIES),
        "ingest_ms": round(ingest_ms, 2),
        "ingest_summary": {k: v for k, v in ingest_result.items() if k != "receipts"},
        "embedding_backfill": backfill_stats,
        "ablations": results,
        "mutation_checks": mut,
        "storage": store,
        "resources": {
            "peak_rss_mb": round(_rss_mb(), 1),
            "rss_after_embed_model_mb": rss_after_embed,
            "rss_after_rerank_model_mb": rss_after_rerank,
            "total_cpu_s": round(_cpu_s(), 2),
        },
        "metric_note": "Recall/MRR/nDCG computed over DEDUPLICATED document paths.",
    }

    out_dir = _HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{run_id}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log.info("report -> %s", out)
    return report


if __name__ == "__main__":
    dsn = os.environ.get("NIZAM_KNOWLEDGE_DSN")
    if not dsn:
        sys.exit("NIZAM_KNOWLEDGE_DSN not set")
    corpus = os.environ.get("BENCH_CORPUS_ROOT", "/tmp/nizam_bench_corpus")
    abl = os.environ.get("BENCH_ABLATIONS", "lexical,dense,hybrid,hybrid_rerank").split(",")
    rep = run(dsn, corpus, [a.strip() for a in abl if a.strip()])

    print("\n=== SUMMARY ===")
    hdr = f"{'ablation':<15}{'hit':>5}{'R@5':>7}{'MRR':>7}{'nDCG':>7}{'p50ms':>8}{'p95ms':>8}"
    print(hdr); print("-" * len(hdr))
    for a in rep["ablations"]:
        print(f"{a['ablation']:<15}{a['queries_with_hit']:>3}/{rep['corpus_queries']:<2}"
              f"{a['avg_recall_5']:>7.3f}{a['avg_mrr']:>7.3f}{a['avg_ndcg_10']:>7.3f}"
              f"{a['p50_ms']:>8.1f}{a['p95_ms']:>8.1f}")
    print(f"\nupdate PASS={rep['mutation_checks']['update'].get('PASS')}  "
          f"delete PASS={rep['mutation_checks']['delete'].get('PASS')}")
    print(f"storage: {rep['storage']['db_total_mb']} MB total, "
          f"{rep['storage']['chunks']} chunks, {rep['storage']['embeddings']} embeddings")
    print(f"peak RSS: {rep['resources']['peak_rss_mb']} MB")
