# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Ingest pipeline tests — requires PostgreSQL (NIZAM_KNOWLEDGE_DSN)."""
from __future__ import annotations
import sys, os, uuid, json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

pytestmark = pytest.mark.skipif(
    not os.environ.get("NIZAM_KNOWLEDGE_DSN"),
    reason="NIZAM_KNOWLEDGE_DSN not set"
)


@pytest.fixture(scope="function")
def conn(pg_dsn):
    import psycopg2
    c = psycopg2.connect(pg_dsn)
    yield c
    try:
        c.rollback()
    except Exception:
        pass
    c.close()


def _write_file(tmp_path, name, content):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_unchanged_creates_no_duplicate(conn, tmp_path):
    from NIZAM__system.retrieval.ingest import ingest_file
    src = "test_sources/ingest_tests"
    content = "# Stable\n\nThis content does not change.\n"
    path = _write_file(tmp_path, "NIZAM__system/docs/stable.md", content)
    rel  = "NIZAM__system/docs/stable.md"

    r1 = ingest_file(conn, src, rel, path)
    r2 = ingest_file(conn, src, rel, path)
    assert r1.version_id == r2.version_id, "Second ingest of unchanged file must reuse version"
    assert r2.skipped, "Second ingest must be skipped"
    assert r2.chunk_count == 0


def test_changed_creates_new_version(conn, tmp_path):
    from NIZAM__system.retrieval.ingest import ingest_file
    import psycopg2.extras
    src = "test_sources/ingest_tests"
    path = _write_file(tmp_path, "NIZAM__system/docs/changing.md", "# V1\n\nOriginal content.\n")
    rel  = "NIZAM__system/docs/changing.md"

    r1 = ingest_file(conn, src, rel, path)
    assert not r1.skipped

    # Modify content
    Path(path).write_text("# V2\n\nChanged content.\n", encoding="utf-8")
    r2 = ingest_file(conn, src, rel, path)
    assert not r2.skipped
    assert r2.version_id != r1.version_id, "Changed file must produce a new version_id"

    # Previous version must no longer be current
    with conn.cursor() as cur:
        cur.execute("SELECT is_current FROM document_versions WHERE version_id=%s", (r1.version_id,))
        row = cur.fetchone()
        assert row and not row[0], "Old version must be non-current after update"


def test_current_state_excludes_superseded(conn, tmp_path):
    from NIZAM__system.retrieval.ingest import ingest_file
    src = "test_sources/ingest_tests"
    rel = "NIZAM__system/docs/temporal.md"
    _write_file(tmp_path, rel, "# V1\n\nOld state.\n")
    path = str(tmp_path / rel)
    r1 = ingest_file(conn, src, rel, path)

    Path(path).write_text("# V2\n\nNew state supersedes old.\n", encoding="utf-8")
    r2 = ingest_file(conn, src, rel, path)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM document_versions dv
            JOIN chunks c ON c.version_id = dv.version_id
            WHERE c.source_path = %s AND dv.is_current = true
        """, (rel,))
        current_ct = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM document_versions dv
            JOIN chunks c ON c.version_id = dv.version_id
            WHERE c.source_path = %s AND dv.is_current = false
        """, (rel,))
        old_ct = cur.fetchone()[0]
    assert current_ct > 0, "Must have current chunks"
    assert old_ct > 0, "Old version chunks must still exist (historical)"


def test_prohibited_fixture_blocked(conn, tmp_path):
    from NIZAM__system.retrieval.ingest import ingest_file
    from NIZAM__system.retrieval.himayah import HimayahViolation
    src = "test_sources/ingest_tests"
    path = _write_file(tmp_path, "AHEL__family_network/person.json", '{"name": "Test"}')
    with pytest.raises(HimayahViolation):
        ingest_file(conn, src, "AHEL__family_network/person.json", path)


def test_provenance_round_trips(conn, tmp_path):
    from NIZAM__system.retrieval.ingest import ingest_file
    src = "test_sources/ingest_tests"
    content = "# Provenance Check\n\nThis tests that provenance survives to the DB.\n"
    path = _write_file(tmp_path, "NIZAM__system/docs/prov_test.md", content)
    rel  = "NIZAM__system/docs/prov_test.md"
    r = ingest_file(conn, src, rel, path)
    assert r.version_id
    with conn.cursor() as cur:
        cur.execute("SELECT source_path, classification FROM chunks WHERE version_id = %s LIMIT 1", (r.version_id,))
        row = cur.fetchone()
    assert row, "Chunks must be stored for ingested document"
    assert row[0] == rel
    assert row[1] == "private_github"
