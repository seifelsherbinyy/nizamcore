# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Chunking correctness and provenance round-trip tests."""
from __future__ import annotations
import sys, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from NIZAM__system.retrieval.chunking import chunk_document
from NIZAM__system.retrieval.model import Chunk

NOW = datetime.now(timezone.utc)
V   = str(uuid.uuid4())
D   = str(uuid.uuid4())


def _chunks(text, path, **kw):
    return chunk_document(text, path, V, D, "private_github", NOW, **kw)


def test_markdown_heading_aware():
    md = "# Title\n\nIntro paragraph.\n\n## Section A\n\nSection A body.\n\n## Section B\n\nSection B body.\n"
    chunks = _chunks(md, "test.md")
    assert len(chunks) >= 2
    headings = [c.heading_path for c in chunks]
    assert any("Section A" in h for h in headings)
    assert any("Section B" in h for h in headings)


def test_markdown_inherited_heading():
    md = "# Top\n\n## Sub\n\n### DeepSub\n\nContent here.\n"
    chunks = _chunks(md, "test.md")
    deep = [c for c in chunks if "DeepSub" in c.heading_path]
    assert deep, "DeepSub heading should appear in at least one chunk"
    assert "Top" in deep[0].heading_path or "Sub" in deep[0].heading_path


def test_provenance_round_trip():
    md = "# Check\n\nSome content.\n"
    chunks = _chunks(md, "prov/test.md")
    for c in chunks:
        assert c.version_id == V
        assert c.document_id == D
        assert c.source_path == "prov/test.md"
        assert c.classification == "private_github"
        assert c.source_updated_at == NOW
        assert c.content_hash  # sha256 present
        assert c.token_count > 0


def test_neighbor_links():
    md = "\n\n".join([f"Paragraph {i}: " + "word " * 50 for i in range(6)])
    chunks = _chunks(md, "test.md")
    if len(chunks) > 1:
        for i, c in enumerate(chunks):
            if i > 0:
                assert c.prev_chunk_id == chunks[i - 1].chunk_id
            if i < len(chunks) - 1:
                assert c.next_chunk_id == chunks[i + 1].chunk_id


def test_jsonl_one_chunk_per_record():
    import json
    lines = [json.dumps({"event_id": f"E{i:03d}", "val": i}) for i in range(5)]
    chunks = _chunks("\n".join(lines), "test.jsonl")
    assert len(chunks) == 5


def test_json_object_chunk():
    import json
    obj = json.dumps({"name": "test", "value": 42})
    chunks = _chunks(obj, "test.json")
    assert len(chunks) >= 1
    assert any("42" in c.content or "test" in c.content for c in chunks)


def test_content_hash_stable():
    text = "# Stable\n\nThis content.\n"
    c1 = _chunks(text, "t.md")
    c2 = _chunks(text, "t.md")
    assert c1[0].content_hash == c2[0].content_hash


def test_no_empty_chunks():
    md = "# H\n\n" + "\n\n".join(["paragraph " * 30 for _ in range(10)])
    for c in _chunks(md, "big.md"):
        assert c.content.strip(), "Empty chunk detected"
        assert c.token_count > 0


def test_date_extraction():
    text = "On 2026-08-15, the system was initialized.\n"
    chunks = _chunks(text, "dated.md")
    dated = [c for c in chunks if c.occurred_at is not None]
    assert dated, "Expected at least one chunk with occurred_at extracted from date in content"
    assert dated[0].occurred_at.year == 2026
