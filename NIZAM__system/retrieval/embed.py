# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 2
"""Embedding port — deterministic CPU-only dense vectors via fastembed/ONNX.

Design notes (verified empirically 2026-09-01, fastembed 0.8.0):
  - fastembed does NOT apply e5 "query: "/"passage: " prefixes. query_embed()
    and embed() return identical vectors. We therefore apply prefixes here.
  - fastembed does NOT L2-normalize output (observed norm ~28.8). We normalize
    so cosine and inner-product distances are interchangeable.

No monetary values pass through this module. Embeddings are derived only from
already-HIMAYAH-cleared chunk text.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Iterable, Optional, Sequence

log = logging.getLogger(__name__)

# Deployment-specific. Supplied by the environment, never hardcoded (R24).
DEFAULT_CACHE = os.environ.get("NIZAM_RETRIEVAL_MODEL_CACHE") or None

# Model families that require asymmetric query/passage prefixes.
_E5_PREFIX_FAMILIES = ("e5",)


def _needs_e5_prefix(model_name: str) -> bool:
    low = model_name.lower()
    return any(f in low for f in _E5_PREFIX_FAMILIES)


def _l2_normalize(vec: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return list(vec)
    return [v / norm for v in vec]


class Embedder:
    """Wraps a fastembed TextEmbedding with correct prefixing and normalization."""

    def __init__(
        self,
        model_name: str,
        cache_dir: str = DEFAULT_CACHE,
        normalize: bool = True,
    ) -> None:
        from fastembed import TextEmbedding  # imported lazily: heavy

        os.makedirs(cache_dir, exist_ok=True)
        self.model_name = model_name
        self.normalize = normalize
        self._e5 = _needs_e5_prefix(model_name)
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        # Probe dimension once, deterministically.
        probe = list(self._model.embed(["dimension probe"]))[0]
        self.dim = len(probe)
        log.info(
            "Embedder ready model=%s dim=%d e5_prefix=%s normalize=%s",
            model_name, self.dim, self._e5, normalize,
        )

    # -- internal ---------------------------------------------------------
    def _post(self, vecs: Iterable[Sequence[float]]) -> list[list[float]]:
        out = []
        for v in vecs:
            v = [float(x) for x in v]
            out.append(_l2_normalize(v) if self.normalize else v)
        return out

    # -- public -----------------------------------------------------------
    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed documents/chunks for storage."""
        if not texts:
            return []
        payload = [f"passage: {t}" for t in texts] if self._e5 else list(texts)
        return self._post(self._model.embed(payload))

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        payload = f"query: {text}" if self._e5 else text
        return self._post(self._model.embed([payload]))[0]

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = [f"query: {t}" for t in texts] if self._e5 else list(texts)
        return self._post(self._model.embed(payload))


_CACHE: dict[tuple[str, str, bool], Embedder] = {}


def get_embedder(
    model_name: str,
    cache_dir: str = DEFAULT_CACHE,
    normalize: bool = True,
) -> Embedder:
    """Process-level singleton so the model is loaded at most once per config."""
    key = (model_name, cache_dir, normalize)
    if key not in _CACHE:
        _CACHE[key] = Embedder(model_name, cache_dir, normalize)
    return _CACHE[key]


def model_version_of(model_name: str) -> str:
    """Stable version tag recorded alongside stored vectors."""
    try:
        import fastembed
        fe = fastembed.__version__
    except Exception:
        fe = "unknown"
    return f"fastembed{fe}"

# ── Cross-encoder reranker ────────────────────────────────────────────────────
class Reranker:
    """Cross-encoder reranker. Scores (query, passage) pairs jointly.

    Higher score = more relevant. Scores are model-specific logits, not
    probabilities, and are only meaningful for ordering within one query.
    """

    def __init__(self, model_name: str, cache_dir: str = DEFAULT_CACHE) -> None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        os.makedirs(cache_dir, exist_ok=True)
        self.model_name = model_name
        self._model = TextCrossEncoder(model_name=model_name, cache_dir=cache_dir)
        log.info("Reranker ready model=%s", model_name)

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        return [float(s) for s in self._model.rerank(query, list(passages))]

    def __call__(self, query: str, passages: Sequence[str]) -> list[float]:
        return self.score(query, passages)


_RERANK_CACHE: dict[tuple[str, str], "Reranker"] = {}


def get_reranker(model_name: str, cache_dir: str = DEFAULT_CACHE) -> "Reranker":
    key = (model_name, cache_dir)
    if key not in _RERANK_CACHE:
        _RERANK_CACHE[key] = Reranker(model_name, cache_dir)
    return _RERANK_CACHE[key]
