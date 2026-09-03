# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Pytest fixtures shared across the retrieval test suite.

Uses an in-memory SQLite-like approach for unit tests that don't need PG:
  - HIMAYAH and chunking tests need no DB at all
  - Ingest and query tests use a real PostgreSQL via NIZAM_KNOWLEDGE_DSN
    (set in environment; skipped if absent)
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure the nizamcore root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


@pytest.fixture(scope="session")
def pg_dsn():
    dsn = os.environ.get("NIZAM_KNOWLEDGE_DSN")
    if not dsn:
        pytest.skip("NIZAM_KNOWLEDGE_DSN not set — skipping PostgreSQL tests")
    return dsn


@pytest.fixture(scope="session")
def bench_root(tmp_path_factory):
    return str(tmp_path_factory.mktemp("bench_corpus"))
