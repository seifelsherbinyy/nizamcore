"""Tests for the fail-closed Hermes profile adapter.

No process, provider, network, or secret is used by these tests.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from NIZAM__system.relay.hermes_adapter import (
    HermesInvocation,
    HermesUnavailable,
    build_command,
    invoke_hermes,
)
from NIZAM__system.relay import coordinator


class TestHermesAdapter(unittest.TestCase):
    def test_disabled_live_flag_refuses_before_process(self):
        with tempfile.TemporaryDirectory() as home:
            calls: list[object] = []

            def runner(*args, **kwargs):
                calls.append((args, kwargs))
                raise AssertionError("runner must not be called")

            with self.assertRaisesRegex(HermesUnavailable, "live_flag_disabled"):
                invoke_hermes(
                    HermesInvocation(home, "xiaomi/mimo-v2.5", "hello"),
                    environ={"NIZAM_HERMES_LIVE": "0"},
                    runner=runner,
                )
            self.assertEqual(calls, [])

    def test_prompt_is_stdin_and_command_contains_no_prompt(self):
        with tempfile.TemporaryDirectory() as home:
            captured: dict[str, object] = {}

            def runner(command, **kwargs):
                captured["command"] = command
                captured.update(kwargs)
                return __import__("subprocess").CompletedProcess(command, 0, "focused response\n", "")

            response = invoke_hermes(
                HermesInvocation(home, "xiaomi/mimo-v2.5", "private owner request"),
                environ={"NIZAM_HERMES_LIVE": "1", "OPENROUTER_API_KEY": "synthetic"},
                runner=runner,
            )
            command = captured["command"]
            self.assertNotIn("private owner request", command)
            self.assertEqual(captured["input"], "private owner request")
            self.assertEqual(captured["shell"], False)
            self.assertIn("--provider", command)
            self.assertIn("openrouter", command)
            self.assertEqual(response.text, "focused response")

    def test_secret_like_response_is_refused(self):
        with tempfile.TemporaryDirectory() as home:
            def runner(command, **kwargs):
                return __import__("subprocess").CompletedProcess(command, 0, "sk-or-v1-secret", "")

            with self.assertRaisesRegex(HermesUnavailable, "secret_pattern"):
                invoke_hermes(
                    HermesInvocation(home, "xiaomi/mimo-v2.5", "hello"),
                    environ={"NIZAM_HERMES_LIVE": "1"},
                    runner=runner,
                )

    def test_profile_home_must_be_absolute(self):
        with self.assertRaisesRegex(HermesUnavailable, "profile_home_must_be_absolute"):
            invoke_hermes(
                HermesInvocation("relative", "xiaomi/mimo-v2.5", "hello"),
                environ={"NIZAM_HERMES_LIVE": "1"},
                runner=lambda *args, **kwargs: None,
            )

    def test_coordinator_uses_hermes_only_when_live_is_enabled(self):
        with tempfile.TemporaryDirectory() as home, mock.patch.dict(
            "os.environ",
            {
                "NIZAM_HERMES_LIVE": "1",
                "NIZAM_HERMES_PROFILE_HOME": home,
                "NIZAM_HERMES_MODEL": "xiaomi/mimo-v2.5",
            },
            clear=False,
        ), mock.patch.object(
            coordinator,
            "invoke_hermes",
            return_value=SimpleNamespace(text="grounded response", model="xiaomi/mimo-v2.5"),
        ) as invoke:
            out = coordinator._agent_response("Salman", "owner request", "trace")
        invoke.assert_called_once()
        self.assertEqual(out["reply"], "grounded response")
        self.assertEqual(out["hermes_status"], "ok")

    def test_grounding_packet_excludes_local_only_health_and_journal(self):
        with tempfile.TemporaryDirectory() as home:
            packet = Path(home) / "evidence.json"
            packet.write_text(
                __import__("json").dumps(
                    {
                        "evidence": [
                            {
                                "sourceLabel": "contract",
                                "sourceRef": "https://example.invalid/contract",
                                "versionRef": "v1",
                                "contentHash": "a" * 64,
                                "privacyClass": "cloud_allowed",
                                "domain": "contract",
                                "content": "deterministic rule",
                            },
                            {
                                "sourceLabel": "journal",
                                "sourceRef": "https://example.invalid/journal",
                                "versionRef": "v1",
                                "contentHash": "b" * 64,
                                "privacyClass": "local_only",
                                "domain": "journal",
                                "content": "private journal text",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            captured: dict[str, object] = {}

            def runner(command, **kwargs):
                captured.update(kwargs)
                return __import__("subprocess").CompletedProcess(command, 0, "focused response\n", "")

            invoke_hermes(
                HermesInvocation(home, "xiaomi/mimo-v2.5", "private owner request"),
                environ={
                    "NIZAM_HERMES_LIVE": "1",
                    "NIZAM_HERMES_EVIDENCE_FILE": str(packet),
                },
                runner=runner,
            )
            self.assertIn("deterministic rule", captured["input"])
            self.assertNotIn("private journal text", captured["input"])

    def test_confirmed_owner_memory_is_loaded_without_raw_private_topics(self):
        with tempfile.TemporaryDirectory() as home:
            memory = Path(home) / "memory.jsonl"
            memory.write_text(
                __import__("json").dumps(
                    {
                        "status": "confirmed",
                        "confirmed_by": "Operator",
                        "content": "prefer concise replies",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            captured: dict[str, object] = {}

            def runner(command, **kwargs):
                captured.update(kwargs)
                return __import__("subprocess").CompletedProcess(command, 0, "focused response\n", "")

            invoke_hermes(
                HermesInvocation(home, "xiaomi/mimo-v2.5", "owner request"),
                environ={
                    "NIZAM_HERMES_LIVE": "1",
                    "NIZAM_HERMES_MEMORY_FILE": str(memory),
                },
                runner=runner,
            )
            self.assertIn("prefer concise replies", captured["input"])


if __name__ == "__main__":
    unittest.main()
