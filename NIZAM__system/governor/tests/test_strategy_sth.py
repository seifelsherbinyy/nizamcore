"""Tests for strategy_sth.py (E4.3) — RFC 6962 + Ed25519 STH."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import ledger_writer, strategy_sth  # noqa: E402


class MerkleRFC6962E43(unittest.TestCase):

    def test_empty_input_gives_zero_root(self) -> None:
        root = strategy_sth.merkle_root([])
        self.assertEqual(b"\x00" * 32, root)

    def test_single_leaf_matches_leaf_hash(self) -> None:
        # RFC 6962: single-leaf tree root == LeafHash(d0)
        h = "a" * 64
        expected = strategy_sth._leaf_hash(h)
        self.assertEqual(expected, strategy_sth.merkle_root([h]))

    def test_two_leaves_node_hash(self) -> None:
        h1 = "a" * 64
        h2 = "b" * 64
        expected = strategy_sth._node_hash(
            strategy_sth._leaf_hash(h1),
            strategy_sth._leaf_hash(h2),
        )
        self.assertEqual(expected, strategy_sth.merkle_root([h1, h2]))

    def test_three_leaves_carries_odd_up(self) -> None:
        h1 = "a" * 64
        h2 = "b" * 64
        h3 = "c" * 64
        n12 = strategy_sth._node_hash(
            strategy_sth._leaf_hash(h1),
            strategy_sth._leaf_hash(h2),
        )
        # Odd leaf carried up unhashed per RFC 6962-faithful local impl.
        expected = strategy_sth._node_hash(n12, strategy_sth._leaf_hash(h3))
        self.assertEqual(expected, strategy_sth.merkle_root([h1, h2, h3]))


class PublishVerifyE43(unittest.TestCase):

    def test_publish_then_verify_roundtrip(self) -> None:
        # Append one fresh strategy ledger row so there's something to sign.
        row = ledger_writer.append(
            "STRATEGY_LEDGER",
            payload={"note": "E4.3 test round-trip", "kind": "test"},
            actor="Ammar",
            action="test_strategy_sth",
            module="NIZAM__governor.tests",
            privacy_class="strict_local",
        )
        self.assertIn("row_hash", row)

        sth = strategy_sth.publish_sth()
        self.assertGreaterEqual(sth["tree_size"], 1)
        self.assertEqual(len(sth["root_hash_hex"]), 64)

        ok, reason = strategy_sth.verify_sth(sth)
        self.assertTrue(ok, reason)

    def test_tamper_detected_on_size_change(self) -> None:
        sth = strategy_sth.publish_sth()
        tampered = dict(sth)
        tampered["tree_size"] = (sth["tree_size"] or 0) + 5
        ok, reason = strategy_sth.verify_sth(tampered)
        self.assertFalse(ok, reason)

    def test_tamper_detected_on_root(self) -> None:
        sth = strategy_sth.publish_sth()
        tampered = dict(sth)
        tampered["root_hash_hex"] = "0" * 64
        ok, reason = strategy_sth.verify_sth(tampered)
        self.assertFalse(ok, reason)

    def test_sth_file_on_disk(self) -> None:
        strategy_sth.publish_sth()
        path = (_REPO / "NIZAM__system" / "ledgers"
                / "sth" / "STRATEGY_LEDGER.sth.json")
        self.assertTrue(path.exists(), str(path))
        sth = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(sth["ledger"], "STRATEGY_LEDGER")


if __name__ == "__main__":
    unittest.main()
