from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from NIZAM__system.companion.calendar_tasks import (
    Approval,
    ApprovalStore,
    execute,
    operation_hash,
)
from NIZAM__system.companion.capture import persist
from NIZAM__system.companion.context import build_context_packet
from NIZAM__system.companion.contracts import (
    ConnectorOperation,
    ContextItem,
    GatewayEnvelope,
    KnowledgeClaim,
    ProactiveCandidate,
)
from NIZAM__system.companion.gateway import envelope_from_update
from NIZAM__system.companion.knowledge import KnowledgeStore
from NIZAM__system.companion.knowledge_eval import evaluate as evaluate_knowledge
from NIZAM__system.companion.proactive import eligible
from NIZAM__system.companion.reminders import validate_sourced_reminder
from NIZAM__system.companion.whoop_import import correlation_notice, import_export
from NIZAM__system.connectors.health import probe_all


class FakeAdapter:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def read(self, capability: str) -> list[dict]:
        return list(self.rows)

    def write(self, capability: str, payload: dict) -> dict:
        self.rows.append(dict(payload))
        return dict(payload)


class CompanionTests(unittest.TestCase):
    def test_gateway_envelope_hashes_actor(self) -> None:
        envelope = GatewayEnvelope.build(
            message_id="m1", actor_id="operator-raw", route="Amin", channel="telegram"
        )
        self.assertNotEqual(envelope.actor_hash, "operator-raw")
        self.assertEqual(envelope.schema_version, "1.0")

    def test_gateway_envelope_from_telegram_update(self) -> None:
        envelope = envelope_from_update(
            {
                "update_id": 42,
                "message": {
                    "message_id": 7,
                    "from": {"id": 111222333},
                    "text": "hello",
                },
            },
            route="Amin",
        )
        self.assertEqual(envelope.message_id, "7")
        self.assertEqual(envelope.route, "Amin")
        self.assertNotEqual(envelope.actor_hash, "111222333")

    def test_full_capture_redacts_secrets_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.jsonl"
            first = persist(
                trace_id="t1",
                message_id="m1",
                channel="telegram",
                text="idea token=super-secret-value",
                path=path,
            )
            second = persist(
                trace_id="t2",
                message_id="m1",
                channel="telegram",
                text="different duplicate",
                path=path,
            )
            rows = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(first, second)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("super-secret-value", first["text"])

    def test_context_filters_expired_and_over_ceiling(self) -> None:
        now = datetime.now(timezone.utc)
        items = [
            ContextItem("fact", "kept", "fixture", now.isoformat(), "strict_local", 1.0),
            ContextItem(
                "fact",
                "expired",
                "fixture",
                now.isoformat(),
                "strict_local",
                1.0,
                (now - timedelta(seconds=1)).isoformat(),
            ),
            ContextItem(
                "fact",
                "maximum",
                "fixture",
                now.isoformat(),
                "strict_local_maximum",
                1.0,
            ),
        ]
        packet = build_context_packet(
            trace_id="t1", persona="Amin", items=items, now=now
        )
        self.assertEqual([item.text for item in packet.items], ["kept"])

    def test_calendar_write_requires_matching_single_use_approval(self) -> None:
        operation = ConnectorOperation(
            connector="google_calendar",
            capability="create_event",
            mode="execute_write",
            idempotency_key="event-1",
            approval_id="approve-1",
            payload={"title": "Review", "start": "2026-06-14T10:00:00+03:00", "end": "2026-06-14T11:00:00+03:00"},
        )
        store = ApprovalStore()
        store.grant(
            Approval(
                "approve-1",
                operation_hash(operation),
                datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        adapter = FakeAdapter()
        result = execute(operation, adapter=adapter, approvals=store)
        self.assertTrue(result["verified"])
        with self.assertRaises(PermissionError):
            execute(operation, adapter=adapter, approvals=store)

    def test_google_adapter_execute_maps_read_capability(self) -> None:
        from unittest.mock import patch

        from NIZAM__system.connectors.google_adapter import GoogleConnectorAdapter

        adapter = GoogleConnectorAdapter()
        with patch.object(adapter, "write", return_value={"id": "evt1"}) as mock_write:
            with patch.object(adapter, "read", return_value=[]) as mock_read:
                operation = ConnectorOperation(
                    connector="google_calendar",
                    capability="create_event",
                    mode="execute_write",
                    idempotency_key="evt1",
                    approval_id="approve-google",
                    payload={
                        "title": "Review",
                        "start": "2026-06-14T10:00:00+03:00",
                        "end": "2026-06-14T11:00:00+03:00",
                    },
                )
                store = ApprovalStore()
                store.grant(
                    Approval(
                        "approve-google",
                        operation_hash(operation),
                        datetime.now(timezone.utc) + timedelta(minutes=5),
                    )
                )
                execute(operation, adapter=adapter, approvals=store)
                mock_write.assert_called_once()
                mock_read.assert_called_once_with("read_calendar")

    def test_whoop_export_import_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "whoop.csv"
            path.write_text(
                "date,recovery score,hrv,strain\n"
                "2026-06-10,72,48,10.2\n"
                "2026-06-11,65,45,12.1\n",
                encoding="utf-8",
            )
            digest, observations = import_export(path)
        self.assertEqual(len(digest), 64)
        self.assertEqual(len(observations), 6)
        self.assertTrue(all(item.provenance_hash for item in observations))
        self.assertIn("not a diagnosis", correlation_notice(2))

    def test_knowledge_store_returns_cited_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(Path(tmp) / "knowledge.db")
            store.add(
                KnowledgeClaim(
                    claim_id="c1",
                    claim="Recovery trends require multiple observations.",
                    source_title="BADAN doctrine",
                    source_url="local://BADAN",
                    published_at=None,
                    retrieved_at="2026-06-13T00:00:00Z",
                    reliability="high",
                    summary="Use trend windows.",
                    implications="Avoid single-day conclusions.",
                )
            )
            rows = store.search("recovery")
            store.close()
        self.assertEqual(rows[0]["source_url"], "local://BADAN")

    def test_proactive_policy_enforces_quiet_hours_and_evidence(self) -> None:
        candidate = ProactiveCandidate(
            persona="Amin",
            trigger="calendar_deadline",
            relevance_score=0.9,
            source_refs=("calendar:event:1",),
            expires_at="2026-06-14T12:00:00Z",
            message="Review is due soon.",
        )
        allowed, reason, _tiny = eligible(
            candidate,
            now=datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc),
            sent_today=[],
            paused=False,
            sukoon_red=False,
        )
        self.assertTrue(allowed, reason)
        blocked, reason, _tiny = eligible(
            candidate,
            now=datetime(2026, 6, 13, 20, 30, tzinfo=timezone.utc),
            sent_today=[],
            paused=False,
            sukoon_red=False,
        )
        self.assertFalse(blocked)
        self.assertEqual(reason, "quiet_hours")

    def test_new_connectors_are_disabled_and_non_networked(self) -> None:
        result = probe_all(environ={})
        by_id = {item["connector_id"]: item for item in result["connectors"]}
        for connector_id in (
            "google_calendar",
            "google_tasks",
            "whoop_export",
            "research_fetch",
            "telegram_proactive",
        ):
            self.assertEqual(by_id[connector_id]["state"], "disabled")
            self.assertFalse(by_id[connector_id]["network_probed"])
            self.assertFalse(by_id[connector_id]["write_attempted"])

    def test_knowledge_benchmark_meets_thresholds(self) -> None:
        result = evaluate_knowledge()
        self.assertTrue(result["passed"])
        self.assertEqual(result["hit_rate"], 1.0)
        self.assertGreaterEqual(result["mrr"], 0.6)

    def test_sourced_reminder_rejects_fatwa_and_unapproved_sources(self) -> None:
        ok, reason = validate_sourced_reminder(
            "Remember Q2:286 about patience.",
            ("quran-2-286",),
        )
        self.assertTrue(ok, reason)
        blocked, reason = validate_sourced_reminder(
            "This is haram for you.",
            ("quran-2-286",),
        )
        self.assertFalse(blocked)
        self.assertEqual(reason, "fatwa_language")
        blocked, reason = validate_sourced_reminder(
            "This is consensus and definitely authentic.",
            ("disputed-sample",),
        )
        self.assertFalse(blocked)
        self.assertEqual(reason, "disputed_presented_as_settled")


if __name__ == "__main__":
    unittest.main()
