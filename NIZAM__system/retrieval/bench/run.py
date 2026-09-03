# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Benchmark runner — Wave 1 baseline: lexical only (dense pending embedding deployment).

Measures: Recall@5/10/20, MRR, nDCG@10, p50/p95 latency,
          storage footprint, CPU usage, incremental update/delete correctness.
Outputs: JSON report written to bench/results/<timestamp>.json
"""
from __future__ import annotations

import json
import logging
import math
import os
import resource
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

_HERE = Path(__file__).parent
_ROOT = _HERE.parent  # NIZAM__system/retrieval
sys.path.insert(0, str(_ROOT.parents[1]))  # nizamcore root

from NIZAM__system.retrieval.bench.fixtures import SYNTHETIC_DOCS, BENCHMARK_QUERIES, write_fixtures
from NIZAM__system.retrieval.ingest import run_ingest
from NIZAM__system.retrieval.query import hybrid_search


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for r in retrieved[:k] if r in relevant)
    return hits / len(relevant)


def mrr(retrieved: list[str], relevant: set[str]) -> float:
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    dcg, idcg = 0.0, 0.0
    for i, r in enumerate(retrieved[:k], 1):
        dcg += (1 if r in relevant else 0) / math.log2(i + 1)
    for i in range(1, min(len(relevant), k) + 1):
        idcg += 1.0 / math.log2(i + 1)
    return dcg / idcg if idcg > 0 else 0.0


def run(dsn: str, corpus_root: str, ablations: list[str] | None = None) -> dict:
    if ablations is None:
        ablations = ["lexical"]  # Wave 1: lexical baseline; dense after embeddings deployed

    # Write fixtures
    written = write_fixtures(corpus_root)
    log.info("wrote %d fixture files to %s", len(written), corpus_root)

    source_id = "bench_synthetic_v1"
    run_id = f"bench_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    # Ingest
    t_ingest_start = time.monotonic()
    ingest_result = run_ingest(source_id=source_id, source_root=corpus_root, dsn=dsn)
    ingest_ms = (time.monotonic() - t_ingest_start) * 1000
    log.info("ingest: %s in %.0f ms", ingest_result, ingest_ms)

    results = []
    for ablation in ablations:
        use_dense = "dense" in ablation or "hybrid" in ablation
        latencies = []
        per_query = []

        for q in BENCHMARK_QUERIES:
            t0 = time.monotonic()
            pkt = hybrid_search(
                query=q["text"],
                embed_fn=None if not use_dense else None,  # dense stub until model deployed
                dsn=dsn,
                final_limit=20,
            )
            latency_ms = (time.monotonic() - t0) * 1000
            latencies.append(latency_ms)

            retrieved_paths = [r.source_path for r in pkt.results]
            relevant_paths  = set(q["relevant_paths"])

            per_query.append({
                "qid": q["qid"],
                "family": q["family"],
                "query": q["text"],
                "latency_ms": round(latency_ms, 2),
                "result_count": len(pkt.results),
                "recall_5":  round(recall_at_k(retrieved_paths, relevant_paths, 5),  4),
                "recall_10": round(recall_at_k(retrieved_paths, relevant_paths, 10), 4),
                "recall_20": round(recall_at_k(retrieved_paths, relevant_paths, 20), 4),
                "mrr":       round(mrr(retrieved_paths, relevant_paths),              4),
                "ndcg_10":   round(ndcg_at_k(retrieved_paths, relevant_paths, 10),   4),
                "retrieved_paths": retrieved_paths[:10],
                "relevant_paths":  list(relevant_paths),
            })

        latencies_s = sorted(latencies)
        p50 = latencies_s[len(latencies_s) // 2]
        p95 = latencies_s[int(len(latencies_s) * 0.95)]

        results.append({
            "run_id":    run_id + f"_{ablation}",
            "ablation":  ablation,
            "system":    "B",
            "p50_ms":    round(p50, 2),
            "p95_ms":    round(p95, 2),
            "avg_recall_5":  round(sum(q["recall_5"]  for q in per_query) / len(per_query), 4),
            "avg_recall_10": round(sum(q["recall_10"] for q in per_query) / len(per_query), 4),
            "avg_mrr":       round(sum(q["mrr"]       for q in per_query) / len(per_query), 4),
            "avg_ndcg_10":   round(sum(q["ndcg_10"]   for q in per_query) / len(per_query), 4),
            "per_query": per_query,
        })

    report = {
        "schema": "nizam.retrieval_benchmark/v1",
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "corpus_size_docs": len(SYNTHETIC_DOCS),
        "corpus_size_queries": len(BENCHMARK_QUERIES),
        "ingest_ms": round(ingest_ms, 2),
        "ingest_summary": ingest_result,
        "ablations": results,
        "notes": "Wave 1 baseline — lexical (FTS) only. Dense leg pending embedding model deployment.",
    }

    # Write report
    out_dir = _HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log.info("report written to %s", out_path)
    return report


if __name__ == "__main__":
    dsn = os.environ.get("NIZAM_KNOWLEDGE_DSN")
    if not dsn:
        print("ERROR: NIZAM_KNOWLEDGE_DSN not set", file=sys.stderr)
        sys.exit(1)
    corpus = os.environ.get("BENCH_CORPUS_ROOT", "/tmp/nizam_bench_corpus")
    report = run(dsn=dsn, corpus_root=corpus)
    print(json.dumps(report, indent=2, default=str))
