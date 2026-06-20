from __future__ import annotations

import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.companion.contracts import ContextRefresh, PulsationMessage  # noqa: E402
from NIZAM__system.companion.council.contracts import (  # noqa: E402
    AgentPosition,
    CouncilMotion,
    Vote,
)
from NIZAM__system.companion.council.decision_protocols import (  # noqa: E402
    apply_protocol,
    member_can_veto,
)
from NIZAM__system.companion.council.deliberation import deliberate, inject_veto  # noqa: E402
from NIZAM__system.companion.council.evidence import (  # noqa: E402
    build_evidence_pack,
    contains_journal_egress,
)
from NIZAM__system.companion.council.ledger import append_council_verdict  # noqa: E402
from NIZAM__system.companion.council.stability import update_stability  # noqa: E402
from NIZAM__system.companion.council.triggers import (  # noqa: E402
    minimal_pulse_note,
    should_convene_council,
)
from NIZAM__system.companion.council.view_renderer import render_view  # noqa: E402
from NIZAM__system.governor import ledger_writer  # noqa: E402


def _motion(**overrides) -> CouncilMotion:
    base = {
        "motion_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        "title": "Quarterly focus shift",
        "question": "Should we reprioritize housing savings?",
        "protocol": "majority",
        "urgency": "normal",
        "proposed_by": "Operator",
        "created_at": "2026-06-14T12:00:00Z",
    }
    base.update(overrides)
    return CouncilMotion(**base)


def _refresh(**overrides) -> ContextRefresh:
    base = {
        "refreshed_at": "2026-06-14T12:00:00Z",
        "sources_checked": ("yawmiyat_journal", "whoop_badan"),
        "sources_found": ("yawmiyat_journal",),
        "missing_sources": ("whoop_badan",),
        "latest_entry_timestamps": {"yawmiyat_journal": "2026-06-14T08:00:00Z"},
        "confidence": "medium",
        "privacy_level": "strict_local",
        "sukoon_capacity": "green",
        "source_snapshots": {
            "yawmiyat_journal": {"entry_date": "2026-06-14", "title_present": True},
        },
    }
    base.update(overrides)
    return ContextRefresh(**base)


class CouncilTests(unittest.TestCase):
    def test_evidence_pack_excludes_journal_body_egress(self) -> None:
        secret = "PRIVATE JOURNAL BODY TEXT THAT MUST NEVER EGRESS"
        refresh = _refresh(
            source_snapshots={
                "yawmiyat_journal": {
                    "entry_date": "2026-06-14",
                    "title_present": True,
                    "body": secret,
                    "journal_body": secret,
                    "content": secret,
                }
            }
        )
        pack = build_evidence_pack(refresh)
        serialized = json.dumps([ref.to_dict() for ref in pack])
        self.assertNotIn(secret, serialized)
        self.assertFalse(contains_journal_egress(pack, forbidden_text=secret))
        self.assertTrue(any(ref.kind == "journal_ref" for ref in pack))

    def test_veto_blocks_approval(self) -> None:
        votes = [
            Vote(agent="Salman", ballot="yes", weight=1.0),
            Vote(agent="Khalid", ballot="yes", weight=1.0),
            Vote(agent="Hazim", ballot="veto", weight=1.0, rationale="value conflict"),
        ]
        outcome, _ = apply_protocol(protocol="majority", votes=votes)
        self.assertEqual(outcome, "vetoed")
        self.assertTrue(member_can_veto("Ammar", "egress"))
        verdict = deliberate(_motion(protocol="majority"), max_rounds=3)
        vetoed = inject_veto(
            verdict,
            agent="Ammar",
            rationale="egress policy would be violated",
        )
        self.assertEqual(vetoed.outcome, "vetoed")

    def test_adaptive_stop_after_two_stable_rounds(self) -> None:
        positions = [
            AgentPosition(
                agent="Salman",
                stance="support",
                rationale="hold",
                confidence=0.7,
                round_index=1,
            ),
            AgentPosition(
                agent="Khalid",
                stance="conditional",
                rationale="hold",
                confidence=0.6,
                round_index=1,
            ),
        ]
        first = update_stability(
            prior_signature=None,
            current_positions=positions,
            stable_rounds=0,
            round_index=1,
            max_rounds=5,
        )
        self.assertFalse(first.should_stop)
        second = update_stability(
            prior_signature=tuple(
                sorted((p.agent, p.stance, round(p.confidence, 2)) for p in positions)
            ),
            current_positions=positions,
            stable_rounds=first.stable_rounds,
            round_index=2,
            max_rounds=5,
        )
        self.assertFalse(second.should_stop)
        third = update_stability(
            prior_signature=tuple(
                sorted((p.agent, p.stance, round(p.confidence, 2)) for p in positions)
            ),
            current_positions=positions,
            stable_rounds=second.stable_rounds,
            round_index=3,
            max_rounds=5,
        )
        self.assertTrue(third.should_stop)
        self.assertEqual(third.reason, "stable_positions")

        verdict = deliberate(_motion(), max_rounds=6)
        self.assertTrue(verdict.stability_stopped)
        self.assertGreaterEqual(verdict.rounds_completed, 2)

    def test_routine_pulse_skips_full_council(self) -> None:
        refresh = _refresh()
        message = PulsationMessage(
            message_type="companion_checkin",
            agent_name="Salman",
            agent_role="Brainstormer",
            generated_at="2026-06-14T08:00:00Z",
            context_refresh=refresh,
            message="routine check-in",
            focus_trigger="one priority",
        )
        self.assertFalse(
            should_convene_council(refresh, pulse_kind="companion_checkin", message=message)
        )
        note = minimal_pulse_note(refresh, pulse_kind="companion_checkin", message=message)
        self.assertEqual(note["council"], "skipped")
        self.assertEqual(note["reason"], "routine_pulse_skipped")

        strategic_refresh = _refresh(sukoon_capacity="yellow")
        self.assertTrue(
            should_convene_council(
                strategic_refresh,
                pulse_kind="strategic_motion",
            )
        )

    def test_view_renderer_and_ledger_append(self) -> None:
        motion = _motion()
        verdict = deliberate(motion, max_rounds=4)
        view = render_view(verdict, motion_title=motion.title, format="telegram_compact")
        self.assertIn("Votes:", view.body)
        self.assertGreater(len(view.vote_table), 0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = append_council_verdict(
                verdict,
                motion=motion,
                view=view,
                root=root,
            )
            self.assertIn("council_row", result)
            self.assertIn("event_row", result)
            council_tail = ledger_writer.tail_rows("COUNCIL_LEDGER", n=1, root=root)
            event_tail = ledger_writer.tail_rows("EVENT_LEDGER", n=1, root=root)
            self.assertEqual(council_tail[0]["payload"]["verdict_id"], verdict.verdict_id)
            self.assertEqual(
                event_tail[0]["payload"]["hash_excerpt"],
                council_tail[0]["payload"]["verdict_hash"],
            )


if __name__ == "__main__":
    unittest.main()
