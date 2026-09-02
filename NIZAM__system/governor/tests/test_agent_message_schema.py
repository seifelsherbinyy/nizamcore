"""Tests for agent_message.schema.json (E1.1) and trace.py (E1.5)."""
from __future__ import annotations

import json
import sys
import unittest
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import ledger_writer, trace  # noqa: E402

SCHEMA_PATH = (
    _REPO
    / "NIZAM__system"
    / "schemas"
    / "agent_message.schema.json"
)


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(instance: dict, schema: dict) -> list[str]:
    """Minimal JSON-schema-draft-7 validator covering the constructs we use.

    We avoid pulling in `jsonschema` because the package is not yet
    vendored. This validator is intentionally narrow.
    """
    errors: list[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})
    additional = schema.get("additionalProperties", True)
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    def check(value, sub, path):
        t = sub.get("type")
        if t is not None:
            ts = t if isinstance(t, list) else [t]
            py_types = []
            allow_null = "null" in ts
            for ti in ts:
                if ti == "null":
                    continue
                py_types.append(type_map.get(ti))
            py_types = tuple(x for x in py_types if x is not None)
            if value is None:
                if not allow_null:
                    errors.append(f"{path}: null not allowed")
                return
            if py_types and not isinstance(value, py_types):
                errors.append(f"{path}: bad type {type(value).__name__}, want {ts}")
                return
            if "boolean" not in ts and isinstance(value, bool):
                # JSON-schema treats booleans as a separate type
                errors.append(f"{path}: bool not allowed here")
                return
        if "enum" in sub and value not in sub["enum"]:
            errors.append(f"{path}: {value!r} not in enum")
        if "const" in sub and value != sub["const"]:
            errors.append(f"{path}: must be {sub['const']!r}")
        if isinstance(value, dict) and "properties" in sub:
            for k, vsub in sub["properties"].items():
                if k in value:
                    check(value[k], vsub, f"{path}.{k}")
            for req in sub.get("required", []):
                if req not in value:
                    errors.append(f"{path}.{req}: missing required")
        if isinstance(value, list) and "items" in sub:
            for i, item in enumerate(value):
                check(item, sub["items"], f"{path}[{i}]")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in sub and value < sub["minimum"]:
                errors.append(f"{path}: {value} < min {sub['minimum']}")
            if "maximum" in sub and value > sub["maximum"]:
                errors.append(f"{path}: {value} > max {sub['maximum']}")
        if isinstance(value, str):
            if "maxLength" in sub and len(value) > sub["maxLength"]:
                errors.append(f"{path}: length {len(value)} > {sub['maxLength']}")

    for req in required:
        if req not in instance:
            errors.append(f"$.{req}: missing required")
    for k, v in instance.items():
        if k in props:
            check(v, props[k], f"$.{k}")
        elif additional is False:
            errors.append(f"$.{k}: additional property not allowed")
    return errors


def _good_envelope(**overrides) -> dict:
    base = {
        "schema_version": "1.0",
        "trace_id": str(uuid.uuid4()),
        "message_id": str(uuid.uuid4()),
        "parent_message_id": None,
        "ts": "2026-05-28T20:00:00Z",
        "from_agent": "Operator",
        "to_agent": "Salman",
        "delegation_depth": 0,
        "kind": "request",
        "purpose": "Brainstorm Q3 priorities.",
        "privacy_class": "strict_local",
        "egress_class": "zdr_inference_only",
        "payload": {"topic": "Q3 priorities"},
        "context_refs": [
            {"kind": "persona", "ref": "NIZAM__system/personas/SHURA.json"}
        ],
        "confidence": 0.7,
        "alternatives": [],
        "needs_operator_confirm": False,
        "operator_confirm_reason": None,
        "cost_cents": None,
        "model": "deepseek-v4-pro",
        "tool_calls": [],
        "gate_decisions": [],
    }
    base.update(overrides)
    return base


class AgentMessageSchemaE11(unittest.TestCase):
    """E1.1 — schemas/agent_message.schema.json shape tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _load_schema()

    def test_good_envelope_validates(self) -> None:
        errs = _validate(_good_envelope(), self.schema)
        self.assertEqual([], errs)

    def test_missing_required_field_fails(self) -> None:
        bad = _good_envelope()
        del bad["trace_id"]
        errs = _validate(bad, self.schema)
        self.assertTrue(any("trace_id" in e for e in errs), errs)

    def test_delegation_depth_max_8_enforced(self) -> None:
        bad = _good_envelope(delegation_depth=9)
        errs = _validate(bad, self.schema)
        self.assertTrue(any("delegation_depth" in e for e in errs), errs)

    def test_unknown_kind_rejected(self) -> None:
        bad = _good_envelope(kind="random")
        errs = _validate(bad, self.schema)
        self.assertTrue(any("kind" in e for e in errs), errs)

    def test_privacy_class_enum_enforced(self) -> None:
        bad = _good_envelope(privacy_class="public")
        errs = _validate(bad, self.schema)
        self.assertTrue(any("privacy_class" in e for e in errs), errs)


class TraceE15(unittest.TestCase):
    """E1.5 — trace_id chain summary."""

    def test_chain_for_includes_payload_trace_id(self) -> None:
        tid = trace.generate_trace_id()
        row = ledger_writer.append(
            "EVENT_LEDGER",
            payload={"trace_id": tid, "target": "Salman", "note": "test"},
            record_id=f"e15-chain:{tid}",
            actor="Ammar",
            action="phase1_round_trip",
            module="NIZAM__governor.tests",
            trace_id=tid,
        )
        s = trace.chain_summary(tid)
        self.assertGreaterEqual(s["hop_count"], 1)
        self.assertIn(row["row_id"], {r.get("row_id")
                                     for r in trace.chain_for(tid)})

    def test_to_markdown_renders(self) -> None:
        tid = trace.generate_trace_id()
        ledger_writer.append(
            "EVENT_LEDGER",
            payload={"trace_id": tid, "target": "Salman"},
            record_id=f"e15-markdown:{tid}",
            actor="Operator",
            action="turn_start",
            module="NIZAM__relay",
            trace_id=tid,
        )
        md = trace.to_markdown(tid)
        self.assertIn("trace", md)
        self.assertIn(tid[:8], md)


if __name__ == "__main__":
    unittest.main()
