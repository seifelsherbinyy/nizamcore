"""Sanity tests for MARSAD generic intel base (E4.2)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_MARSAD = Path(__file__).resolve().parents[1]
if str(_MARSAD) not in sys.path:
    sys.path.insert(0, str(_MARSAD))

from radar.sources.generic_base import (  # noqa: E402
    BaseIntelSource,
    Signal,
    SignalKind,
    SourceBundle,
    signals_to_brief_markdown,
)


class _FakeSource(BaseIntelSource):
    name = "fake"

    def search(self, query, *, window_start=None, window_end=None, max_results=20):
        sig = Signal(
            source_name=self.name,
            kind=SignalKind.NEWS,
            headline=f"hit for {query}",
            body="A short body.",
            url="https://example.com/x",
            captured_ts=self.utc_now_iso(),
            confidence=0.7,
            relevance_tags=["wealth"],
        )
        return SourceBundle(source_name=self.name, signals=[sig])

    def estimate_cost_cents(self, query):
        return 1


class GenericIntelE42(unittest.TestCase):

    def test_subclass_can_search(self) -> None:
        src = _FakeSource()
        bundle = src.search("ai-policy")
        self.assertEqual(1, len(bundle.signals))
        self.assertEqual("hit for ai-policy", bundle.signals[0].headline)

    def test_filter_relevance_keeps_only_matches(self) -> None:
        src = _FakeSource()
        b = src.search("q")
        kept = b.filter_relevance(["wealth"])
        dropped = b.filter_relevance(["unrelated"])
        self.assertEqual(1, len(kept.signals))
        self.assertEqual(0, len(dropped.signals))

    def test_brief_markdown_renders(self) -> None:
        src = _FakeSource()
        b = src.search("q")
        md = signals_to_brief_markdown(b.signals, title="Brief Q2")
        self.assertIn("# Brief Q2", md)
        self.assertIn("hit for q", md)
        self.assertIn("**source:** fake", md)

    def test_fingerprint_deterministic(self) -> None:
        src = _FakeSource()
        sig = src.search("q").signals[0]
        self.assertEqual(src.fingerprint(sig), src.fingerprint(sig))


if __name__ == "__main__":
    unittest.main()
