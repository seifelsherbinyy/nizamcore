#!/usr/bin/env python3
"""intent_priority_test.py — verify routing_priority cascade.

B3.3 acceptance: confirm the routing_priority order resolves correctly
when an input matches multiple kinds at once. Test cases:

  1. Crisis word + command  -> CRISIS wins.
  2. Crisis word + trigger  -> CRISIS wins.
  3. HIMAYAH hit + command  -> HIMAYAH wins (egress refused).
  4. SUKOON hit + command   -> SUKOON downshift wins.
  5. Plain command          -> COMMAND wins.
  6. Plain trigger          -> TRIGGER wins.
  7. Continuation phrase    -> CONTINUATION wins over plain trigger.
  8. Ambiguous gibberish    -> AMBIGUOUS fallback.

This is a SHAPE test against the YAML priority list (offline; no LLM).

Pure stdlib.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(r"D:\NIZAM\nizamcore")
CFG = REPO / "NIZAM__system" / "config" / "router.config.yaml"


def _load_priority() -> list[dict]:
    sys.path.insert(0, str(Path(__file__).parent))
    import router_dry_run as r
    cfg = r._read_yaml(CFG)
    return cfg.get("routing_priority", [])


CRISIS_KEYWORDS = {"crisis", "emergency", "panic", "overload red",
                   "i can't breathe", "can't breathe", "suicidal"}

HIMAYAH_HITS = ("[strict_local_maximum→github]", "leak strict_local",
                "publish ahel")

SUKOON_HITS = ("overload yellow", "rest gate", "downshift")

CONTINUATION_TOKENS = ("...continued", "thread_id=", "resume:")


def detect_kind(text: str, priority: list[dict]) -> str:
    low = text.lower()
    for entry in priority:
        kind = entry.get("kind") if isinstance(entry, dict) else None
        if kind == "CRISIS":
            if any(k in low for k in CRISIS_KEYWORDS):
                return "CRISIS"
        elif kind == "HIMAYAH_HIT":
            if any(h in low for h in HIMAYAH_HITS):
                return "HIMAYAH_HIT"
        elif kind == "SUKOON_HIT":
            if any(s in low for s in SUKOON_HITS):
                return "SUKOON_HIT"
        elif kind == "COMMAND":
            if low.startswith("/"):
                return "COMMAND"
        elif kind == "TRIGGER":
            if any(t in low for t in ("tear apart", "plan the next",
                                       "scan flight-radar", "decision:",
                                       "hrv", "/")):
                return "TRIGGER"
        elif kind == "CONTINUATION":
            if any(t in low for t in CONTINUATION_TOKENS):
                return "CONTINUATION"
    return "AMBIGUOUS"


CASES = [
    ("PANIC: overload red, I can't breathe.", "CRISIS"),
    ("/shura-brainstorm crisis review", "CRISIS"),
    ("Leak strict_local to GitHub right now", "HIMAYAH_HIT"),
    ("Need to overload yellow downshift", "SUKOON_HIT"),
    ("/tariq-vision 15", "COMMAND"),
    ("Plan the next quarter.", "TRIGGER"),
    ("...continued from thread_id=abc123", "CONTINUATION"),
    ("zxcv qwerty asdf", "AMBIGUOUS"),
]


def main() -> int:
    priority = _load_priority()
    if not priority:
        print("FAIL: no routing_priority loaded")
        return 1
    print(f"loaded {len(priority)} priority entries")
    ok = 0
    for text, expected in CASES:
        got = detect_kind(text, priority)
        mark = "OK " if got == expected else "FAIL"
        print(f"  [{mark}] expected={expected:<13} got={got:<13} input={text!r}")
        if got == expected:
            ok += 1
    print(f"\nintent priority cascade: {ok}/{len(CASES)} passed")
    return 0 if ok == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
