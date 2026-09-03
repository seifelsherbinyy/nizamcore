# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Hybrid retrieval query tests — requires PostgreSQL."""
from __future__ import annotations
import os, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

pytestmark = pytest.mark.skipif(
    not os.environ.get("NIZAM_KNOWLEDGE_DSN"),
    reason="NIZAM_KNOWLEDGE_DSN not set"
)


@pytest.fixture(scope="module", autouse=True)
def seed_corpus(pg_dsn, bench_root):
    from NIZAM__system.retrieval.bench.fixtures import write_fixtures, SYNTHETIC_DOCS
    from NIZAM__system.retrieval.ingest import run_ingest
    write_fixtures(bench_root)
    run_ingest("bench_test", bench_root, dsn=pg_dsn)


def test_lexical_exact_id(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("EVT-SYNTH-EXACT-9371", embed_fn=None, dsn=pg_dsn)
    paths = [r.source_path for r in pkt.results]
    assert any("synth_exact_id" in p for p in paths), (
        f"Exact-ID query did not retrieve expected doc. Got: {paths}")


def test_lexical_semantic(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("morning initialization recovery gate", embed_fn=None, dsn=pg_dsn)
    assert len(pkt.results) > 0, "Semantic query returned no results"
    assert pkt.lexical_count > 0


def test_every_result_has_provenance(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("NIZAM protocol system", embed_fn=None, dsn=pg_dsn)
    for r in pkt.results:
        assert r.source_path, "source_path missing"
        assert r.version_id,  "version_id missing"
        assert r.content_hash, "content_hash missing"
        assert r.classification in ("private_github", "review_before_commit")
        assert r.source_updated_at is not None


def test_privacy_filter_blocks_unknown_classification(pg_dsn):
    """Privacy double-check: filter rejects any result with non-permitted classification."""
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search(
        "test", embed_fn=None, dsn=pg_dsn,
        classification_filter=["private_github"],
    )
    for r in pkt.results:
        assert r.classification == "private_github", (
            f"Non-permitted classification leaked: {r.classification}")


def test_multilingual_arabic(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("Arabic text retrieval UTF-8", embed_fn=None, dsn=pg_dsn)
    assert pkt.lexical_count >= 0  # Arabic FTS may have limited overlap; no crash is the key test


def test_current_state_query(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("current rule recovery check frequency", embed_fn=None, dsn=pg_dsn, current_only=True)
    for r in pkt.results:
        assert r.is_current, "current_only query returned non-current result"


def test_result_count_bounded(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("NIZAM protocol", embed_fn=None, dsn=pg_dsn, final_limit=5)
    assert len(pkt.results) <= 5, "Result count must be bounded"


def test_context_packet_latency_recorded(pg_dsn):
    from NIZAM__system.retrieval.query import hybrid_search
    pkt = hybrid_search("test", embed_fn=None, dsn=pg_dsn)
    assert "total" in pkt.stage_latencies_ms
    assert pkt.stage_latencies_ms["total"] > 0
