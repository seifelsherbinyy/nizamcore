# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 2
"""Embedding port tests.

Model-dependent tests are skipped unless NIZAM_RUN_MODEL_TESTS=1, so the
default suite stays fast and offline. Pure logic is always tested.
"""
from __future__ import annotations
import math
import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from NIZAM__system.retrieval.embed import (
    _l2_normalize, _needs_e5_prefix, model_version_of,
)

MODEL_TESTS = os.environ.get("NIZAM_RUN_MODEL_TESTS") == "1"
E5 = "intfloat/multilingual-e5-large"


# ── pure logic (always runs) ──────────────────────────────────────────────────
def test_l2_normalize_unit_length():
    v = _l2_normalize([3.0, 4.0])
    assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0, rel_tol=1e-9)
    assert math.isclose(v[0], 0.6, rel_tol=1e-9)
    assert math.isclose(v[1], 0.8, rel_tol=1e-9)


def test_l2_normalize_zero_vector_is_safe():
    """Zero vector must not divide by zero."""
    assert _l2_normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


def test_l2_normalize_preserves_direction():
    v = _l2_normalize([1.0, 2.0, 2.0])
    assert v[1] == pytest.approx(v[2])
    assert v[0] > 0


def test_e5_family_detected():
    assert _needs_e5_prefix("intfloat/multilingual-e5-large")
    assert _needs_e5_prefix("intfloat/multilingual-e5-small")


def test_non_e5_family_not_prefixed():
    assert not _needs_e5_prefix("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    assert not _needs_e5_prefix("BAAI/bge-small-en-v1.5")


def test_model_version_is_stable_and_tagged():
    mv = model_version_of(E5)
    assert mv.startswith("fastembed")
    assert mv == model_version_of(E5)


# ── model-dependent (opt-in) ──────────────────────────────────────────────────
@pytest.mark.skipif(not MODEL_TESTS, reason="set NIZAM_RUN_MODEL_TESTS=1")
def test_embeddings_are_normalized_and_deterministic():
    from NIZAM__system.retrieval.embed import get_embedder
    e = get_embedder(E5)
    v1 = e.embed_query("recovery gate check")
    v2 = e.embed_query("recovery gate check")
    assert v1 == v2, "embeddings must be deterministic"
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, rel_tol=1e-6)
    assert len(v1) == e.dim


@pytest.mark.skipif(not MODEL_TESTS, reason="set NIZAM_RUN_MODEL_TESTS=1")
def test_e5_prefixes_actually_differ():
    """Guards the verified fastembed behaviour: it does NOT auto-prefix e5,
    so our port must produce different vectors for query vs passage."""
    from NIZAM__system.retrieval.embed import get_embedder
    e = get_embedder(E5)
    q = e.embed_query("recovery gate check")
    p = e.embed_passages(["recovery gate check"])[0]
    assert q != p, "query and passage prefixes must produce different vectors"


@pytest.mark.skipif(not MODEL_TESTS, reason="set NIZAM_RUN_MODEL_TESTS=1")
def test_relevant_scores_above_irrelevant():
    from NIZAM__system.retrieval.embed import get_embedder
    e = get_embedder(E5)
    q = e.embed_query("what happens during morning startup?")
    good = e.embed_passages(["The morning protocol runs a recovery gate check."])[0]
    bad = e.embed_passages(["Income is stored in integer milliunits."])[0]
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    assert dot(q, good) > dot(q, bad)


@pytest.mark.skipif(not MODEL_TESTS, reason="set NIZAM_RUN_MODEL_TESTS=1")
def test_empty_input_returns_empty():
    from NIZAM__system.retrieval.embed import get_embedder
    e = get_embedder(E5)
    assert e.embed_passages([]) == []
    assert e.embed_queries([]) == []
