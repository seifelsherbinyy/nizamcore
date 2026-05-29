"""Generic intelligence source base (E4.2).

The original `base.BaseFlightSource` is specific to flight offers. MARSAD's
strategic-command role (per Plan v2) needs to ingest signals from web,
news, and scholarly feeds. This module gives those adapters a shared
shape **without touching the existing flight code path**.

Adapters land later as siblings; this file is the contract.

Shared shape:
  * Signal — a single intelligence observation
  * SourceBundle — a batch returned by one fetch
  * BaseIntelSource — abstract adapter

Privacy:
  Adapters are EXTERNAL FETCHERS. They never read NIZAM strict_local
  data. They write into MARSAD__flight_radar/briefs/*.md only AFTER
  Ammar gates the resulting signal as `mirror_sanitized`.

Pure stdlib — no third-party imports here so the contract holds across
adapter implementations that may or may not be installed.
"""
from __future__ import annotations

import abc
import dataclasses
import datetime as _dt
import enum
from typing import Any, Iterable


class SignalKind(str, enum.Enum):
    """Categories Tariq cares about during the war room."""
    EXTERNAL_EVENT = "external_event"     # macro, regulation, market move
    OPPORTUNITY = "opportunity"           # something MARSAD recommends acting on
    CONSTRAINT = "constraint"             # something that limits the operator's plan
    SCHOLARLY = "scholarly"               # peer-reviewed insight, citation
    NEWS = "news"                         # journalistic dispatch
    SCAN_NEGATIVE = "scan_negative"       # null result — "we looked and found nothing"


@dataclasses.dataclass
class Signal:
    """One MARSAD signal. The unit of input to Tariq's war room."""
    source_name: str
    kind: SignalKind
    headline: str
    body: str
    url: str | None
    captured_ts: str           # ISO-8601 UTC
    confidence: float          # 0.0 .. 1.0, source's own estimate
    relevance_tags: list[str]  # operator-facing buckets, e.g., ["wealth", "ai-policy"]
    raw: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SourceBundle:
    """Batch result for one MARSAD fetch."""
    source_name: str
    signals: list[Signal]
    errors: list[str] = dataclasses.field(default_factory=list)
    rate_limited: bool = False
    fetch_duration_sec: float = 0.0

    def filter_relevance(self, tags: Iterable[str]) -> "SourceBundle":
        wanted = set(tags)
        kept = [s for s in self.signals
                if wanted.intersection(s.relevance_tags)]
        return dataclasses.replace(self, signals=kept)


class BaseIntelSource(abc.ABC):
    """Abstract adapter for non-flight MARSAD signals.

    Subclasses live in `radar/sources/` alongside the flight adapters.
    Recommended initial siblings (specs only, implementations land per
    operator demand):

      - `web_source.py`      — generic web crawl via Firecrawl / direct HTTP
      - `news_source.py`     — RSS + curated outlets
      - `scholarly_source.py`— Crossref / OpenAlex API
      - `social_source.py`   — limited X/Bluesky polling (off by default)
    """

    name: str = "generic"

    @abc.abstractmethod
    def search(
        self,
        query: str,
        *,
        window_start: _dt.datetime | None = None,
        window_end: _dt.datetime | None = None,
        max_results: int = 20,
    ) -> SourceBundle:
        ...

    @abc.abstractmethod
    def estimate_cost_cents(self, query: str) -> int:
        """Rough cost estimate so Ammar can pre-screen calls against
        the cost ceiling."""
        ...

    @staticmethod
    def utc_now_iso() -> str:
        return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def fingerprint(self, signal: Signal) -> str:
        """Stable hash for de-dup across adapters."""
        import hashlib
        key = f"{signal.source_name}::{signal.url or signal.headline}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def signals_to_brief_markdown(signals: list[Signal], *, title: str) -> str:
    """Render a signal list as the kind of brief the war room consumes.

    Output is deterministic — same input -> same markdown bytes.
    Used by Tahir when producing `MARSAD__flight_radar/briefs/*.md`.
    """
    if not signals:
        return f"# {title}\n\n_No signals captured during this window._\n"
    lines = [f"# {title}", "", f"Signals captured: {len(signals)}", ""]
    for s in sorted(signals, key=lambda x: x.captured_ts, reverse=True):
        lines.append(f"## {s.headline}")
        lines.append("")
        lines.append(f"- **source:** {s.source_name}  ·  **kind:** {s.kind.value}")
        lines.append(f"- **captured:** {s.captured_ts}  ·  **confidence:** {s.confidence:.2f}")
        if s.relevance_tags:
            lines.append(f"- **tags:** {', '.join(s.relevance_tags)}")
        if s.url:
            lines.append(f"- **url:** <{s.url}>")
        lines.append("")
        lines.append(s.body.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
