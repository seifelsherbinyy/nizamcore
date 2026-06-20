from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .contracts import KnowledgeClaim
from .knowledge import KnowledgeStore


DEFAULT_BENCHMARK = Path(__file__).resolve().parent / "knowledge_benchmark.yaml"


def load_benchmark(path: Path = DEFAULT_BENCHMARK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(
    benchmark: dict[str, Any] | None = None,
    *,
    store_path: Path | None = None,
) -> dict[str, Any]:
    benchmark = benchmark or load_benchmark()
    top_k = int(benchmark.get("top_k", 5))
    minimum_mrr = float(benchmark.get("minimum_mrr", 0.6))
    owns_store = store_path is None
    if store_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        store_path = Path(tmp.name)
        tmp.close()
    store = KnowledgeStore(store_path)
    try:
        for row in benchmark.get("fixtures", []):
            store.add(KnowledgeClaim(**row))
        hits = 0
        reciprocal_total = 0.0
        results: list[dict[str, Any]] = []
        for case in benchmark.get("benchmarks", []):
            ranked = store.search(str(case["query"]), limit=top_k)
            ranked_ids = [str(row["claim_id"]) for row in ranked]
            expected = [str(item) for item in case["expected_claim_ids"]]
            rank = next(
                (index + 1 for index, claim_id in enumerate(ranked_ids) if claim_id in expected),
                None,
            )
            hit = rank is not None
            hits += int(hit)
            reciprocal_total += 0.0 if rank is None else 1.0 / rank
            results.append(
                {
                    "id": case["id"],
                    "hit": hit,
                    "rank": rank,
                    "expected_claim_ids": expected,
                    "ranked_claim_ids": ranked_ids,
                }
            )
        cases = len(results)
        hit_rate = hits / cases if cases else 0.0
        mrr = reciprocal_total / cases if cases else 0.0
        return {
            "top_k": top_k,
            "cases": cases,
            "hit_rate": hit_rate,
            "mrr": round(mrr, 4),
            "passed": hit_rate == 1.0 and mrr >= minimum_mrr,
            "results": results,
        }
    finally:
        store.close()
        if owns_store:
            store_path.unlink(missing_ok=True)
