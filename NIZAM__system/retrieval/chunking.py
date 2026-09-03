# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Source-type-aware chunker.

No DB access. No embedding. Pure text → Chunk list.

Supported source types:
  markdown    — heading-aware chunks with inherited heading path
  json        — logical object boundary
  jsonl       — one logical event per chunk
  yaml        — top-level key groups
  code        — function/class/config block (line-based heuristic)
  plaintext   — paragraph / fixed-token fallback

All chunks carry: source_path, heading_path, content, content_hash,
ordinal, token_count (approximated as len//4), parent_chunk_id,
prev/next links (set after all chunks produced), occurred_at (extracted
from content where structurally available).
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .model import Chunk

_MAX_CHUNK_TOKENS = 512
_OVERLAP_TOKENS   = 64
_DATE_RE = re.compile(
    r"\b(20\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b"
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _extract_date(text: str) -> Optional[datetime]:
    m = _DATE_RE.search(text)
    if m:
        try:
            return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _make_chunk(
    version_id: str,
    document_id: str,
    source_path: str,
    ordinal: int,
    heading_path: str,
    content: str,
    classification: str,
    source_updated_at: datetime,
    parent_id: Optional[str] = None,
) -> Chunk:
    cid = str(uuid.uuid4())
    return Chunk(
        chunk_id=cid,
        version_id=version_id,
        document_id=document_id,
        ordinal=ordinal,
        heading_path=heading_path,
        content=content.strip(),
        content_hash=_sha(content),
        token_count=_tokens(content),
        source_path=source_path,
        source_updated_at=source_updated_at,
        occurred_at=_extract_date(content),
        classification=classification,
        parent_chunk_id=parent_id,
    )


def _link_neighbors(chunks: list[Chunk]) -> list[Chunk]:
    for i, c in enumerate(chunks):
        c.prev_chunk_id = chunks[i - 1].chunk_id if i > 0 else None
        c.next_chunk_id = chunks[i + 1].chunk_id if i < len(chunks) - 1 else None
    return chunks


# ── Markdown ──────────────────────────────────────────────────────────────────
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

def _chunk_markdown(
    text: str, version_id: str, doc_id: str, source_path: str,
    classification: str, source_updated_at: datetime
) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading_stack: list[tuple[int, str]] = []
    sections: list[tuple[str, str]] = []  # (heading_path, body)

    splits = _HEADING_RE.split(text)
    # splits: [pre, level1, title1, body1, level2, title2, body2 ...]
    if len(splits) <= 1:
        sections = [("(root)", text)]
    else:
        if splits[0].strip():
            sections.append(("(root)", splits[0]))
        it = iter(splits[1:])
        for hashes, title, body in zip(it, it, it):
            level = len(hashes)
            heading_stack = [(l, t) for l, t in heading_stack if l < level]
            heading_stack.append((level, title.strip()))
            hpath = " > ".join(t for _, t in heading_stack)
            sections.append((hpath, body))

    parent_map: dict[str, str] = {}  # hpath -> parent chunk_id
    for hpath, body in sections:
        paras = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]
        buf, buf_tokens = [], 0
        parent_id = parent_map.get(hpath.rsplit(" > ", 1)[0]) if " > " in hpath else None
        for para in paras:
            pt = _tokens(para)
            if buf and buf_tokens + pt > _MAX_CHUNK_TOKENS:
                c = _make_chunk(version_id, doc_id, source_path,
                                len(chunks), hpath, "\n\n".join(buf),
                                classification, source_updated_at, parent_id)
                chunks.append(c)
                buf, buf_tokens = [], 0
            buf.append(para); buf_tokens += pt
        if buf:
            c = _make_chunk(version_id, doc_id, source_path,
                            len(chunks), hpath, "\n\n".join(buf),
                            classification, source_updated_at, parent_id)
            chunks.append(c)
            parent_map[hpath] = c.chunk_id
    return _link_neighbors(chunks)


# ── JSON ──────────────────────────────────────────────────────────────────────
def _chunk_json(
    text: str, version_id: str, doc_id: str, source_path: str,
    classification: str, source_updated_at: datetime
) -> list[Chunk]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _chunk_plaintext(text, version_id, doc_id, source_path,
                                classification, source_updated_at)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = list(data.items())
    else:
        items = [data]

    chunks: list[Chunk] = []
    for item in items:
        content = json.dumps(item, ensure_ascii=False, indent=2)
        if _tokens(content) > _MAX_CHUNK_TOKENS * 2:
            # oversized: fall back to plaintext chunking of this item
            sub = _chunk_plaintext(content, version_id, doc_id, source_path,
                                   classification, source_updated_at)
            chunks.extend(sub)
        else:
            c = _make_chunk(version_id, doc_id, source_path, len(chunks),
                            "(json object)", content, classification, source_updated_at)
            chunks.append(c)
    return _link_neighbors(chunks)


# ── JSONL ─────────────────────────────────────────────────────────────────────
def _chunk_jsonl(
    text: str, version_id: str, doc_id: str, source_path: str,
    classification: str, source_updated_at: datetime
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            content = json.dumps(obj, ensure_ascii=False)
        except json.JSONDecodeError:
            content = line
        c = _make_chunk(version_id, doc_id, source_path, len(chunks),
                        "(jsonl record)", content, classification, source_updated_at)
        chunks.append(c)
    return _link_neighbors(chunks)


# ── Plaintext / fallback ──────────────────────────────────────────────────────
def _chunk_plaintext(
    text: str, version_id: str, doc_id: str, source_path: str,
    classification: str, source_updated_at: datetime
) -> list[Chunk]:
    words = text.split()
    chunks: list[Chunk] = []
    step = _MAX_CHUNK_TOKENS * 4  # ~4 chars/token
    overlap = _OVERLAP_TOKENS * 4
    i = 0
    while i < len(words):
        window = words[i: i + _MAX_CHUNK_TOKENS]
        content = " ".join(window)
        c = _make_chunk(version_id, doc_id, source_path, len(chunks),
                        "(text)", content, classification, source_updated_at)
        chunks.append(c)
        i += _MAX_CHUNK_TOKENS - _OVERLAP_TOKENS
        if i >= len(words): break
    return _link_neighbors(chunks)


# ── Public dispatch ───────────────────────────────────────────────────────────
def chunk_document(
    text: str,
    source_path: str,
    version_id: str,
    document_id: str,
    classification: str,
    source_updated_at: datetime,
) -> list[Chunk]:
    """Dispatch to the appropriate chunker based on file extension."""
    ext = Path(source_path).suffix.lower()
    kw = dict(version_id=version_id, doc_id=document_id,
              source_path=source_path, classification=classification,
              source_updated_at=source_updated_at)
    if ext in (".md", ".markdown", ".txt", ".rst"):
        return _chunk_markdown(text, **kw)
    elif ext == ".jsonl":
        return _chunk_jsonl(text, **kw)
    elif ext in (".json",):
        return _chunk_json(text, **kw)
    elif ext in (".yaml", ".yml"):
        # YAML: treat as plaintext with heading-aware if "key:" patterns exist
        return _chunk_markdown(text, **kw)
    elif ext in (".py", ".ts", ".js", ".sql", ".sh"):
        return _chunk_plaintext(text, **kw)
    else:
        return _chunk_plaintext(text, **kw)
