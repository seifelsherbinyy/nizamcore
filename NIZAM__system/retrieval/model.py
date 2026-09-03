# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Pure dataclasses — no I/O, no DB imports.

All monetary values would be integer milliunits if this layer ever stored
money; it does not (retrieval is read-only surfaces of upstream records).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DocumentVersion:
    version_id: str
    document_id: str
    source_path: str
    content_hash: str           # sha256
    source_updated_at: datetime
    indexed_at: datetime
    valid_from: datetime
    valid_to: Optional[datetime]
    is_current: bool
    classification: str         # private_github | review_before_commit
    superseded_by: Optional[str] = None


@dataclass
class Chunk:
    chunk_id: str
    version_id: str
    document_id: str
    ordinal: int
    heading_path: str           # e.g. "## Section > ### Subsection"
    content: str
    content_hash: str
    token_count: int
    source_path: str
    source_updated_at: datetime
    occurred_at: Optional[datetime]
    classification: str
    parent_chunk_id: Optional[str] = None
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    confidence: float = 1.0


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    source_path: str
    heading_path: str
    content: str
    classification: str
    is_current: bool
    source_updated_at: datetime
    occurred_at: Optional[datetime]
    lexical_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    rrf_score: float = 0.0
    rerank_score: Optional[float] = None
    # provenance
    version_id: str = ""
    content_hash: str = ""


@dataclass
class ContextPacket:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    query_class: str = "semantic"
    lexical_count: int = 0
    dense_count: int = 0
    overlap: int = 0
    fused_count: int = 0
    reranked_count: int = 0
    privacy_filtered_count: int = 0
    stage_latencies_ms: dict[str, float] = field(default_factory=dict)
    empty_result_reason: Optional[str] = None


@dataclass
class IngestReceipt:
    source: str
    path: str
    content_hash: str
    version_id: str
    chunk_count: int
    embed_count: int
    skipped: bool
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
