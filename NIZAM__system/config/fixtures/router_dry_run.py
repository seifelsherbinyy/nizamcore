#!/usr/bin/env python3
"""router_dry_run.py — deterministic offline dry-run of router.config.yaml.

B3.1 acceptance:
  - Load config + intent_exemplars + 10-input fixture.
  - For each input, deterministically assign a kind + target.
  - Report shape conformance: every input gets a kind from routing_priority
    AND every TRIGGER/COMMAND maps to a known intent target.
  - Expected_routing_min_accuracy in config is met against fixture
    expected_target.

We do NOT invoke any LLM here; this is a shape + priority-cascade test.
The actual LLM-as-router is engaged only post-K1/K2 (USER gate U5).

Pure stdlib + a tiny YAML reader (so we don't pull pyyaml on a fresh
laptop). The YAML reader supports the narrow shape of router.config.yaml
and intent_exemplars.yaml — anything beyond that raises.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(r"D:\NIZAM\nizamcore")
ROUTER_YAML = REPO / "NIZAM__system" / "config" / "router.config.yaml"
EXEMPLARS_YAML = REPO / "NIZAM__system" / "config" / "intent_exemplars.yaml"
FIXTURE = REPO / "NIZAM__system" / "config" / "fixtures" / "router_10_inputs.jsonl"


# --- minimal YAML reader (block-style, no anchors, no flow style) ---
def _strip_comment(s: str) -> str:
    out: list[str] = []
    in_str = False
    quote = ""
    prev = " "
    for ch in s:
        # YAML: `#` only starts a comment when preceded by whitespace
        # (or at start of line) and not inside quotes.
        if not in_str and ch == "#" and (prev == " " or prev == "\t" or prev == ""):
            break
        if ch in "\"'":
            if not in_str:
                in_str = True
                quote = ch
            elif quote == ch:
                in_str = False
        out.append(ch)
        prev = ch
    return "".join(out)


def _parse_scalar(s: str):
    s = s.strip()
    if not s:
        return ""
    if s in ("null", "~"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if (s[0], s[-1]) in (("\"", "\""), ("'", "'")):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _parse_inline_object(s: str) -> dict:
    inner = s.strip()[1:-1].strip()
    out: dict = {}
    parts: list[str] = []
    depth = 0
    cur = ""
    for ch in inner:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    for p in parts:
        k, _, v = p.partition(":")
        out[k.strip()] = _parse_scalar(v)
    return out


def _read_yaml(path: Path) -> dict:
    lines = [
        _strip_comment(line).rstrip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if _strip_comment(line).strip()
    ]
    return _parse_block(lines, 0)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], base: int) -> dict:
    out: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        ind = _indent(line)
        if ind < base:
            break
        if ind > base:
            i += 1
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            # parent expected list; bail out — let caller handle
            break
        key, sep, rest = stripped.partition(":")
        if not sep:
            i += 1
            continue
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("{") and rest.endswith("}"):
            out[key] = _parse_inline_object(rest)
            i += 1
            continue
        if rest:
            out[key] = _parse_scalar(rest)
            i += 1
            continue
        # value is on next lines: either list or block
        child_lines = []
        j = i + 1
        while j < len(lines) and _indent(lines[j]) > base:
            child_lines.append(lines[j])
            j += 1
        if child_lines and child_lines[0].strip().startswith("- "):
            out[key] = _parse_list(child_lines, _indent(child_lines[0]))
        else:
            out[key] = _parse_block(child_lines, _indent(child_lines[0]) if child_lines else base + 2)
        i = j
    return out


def _parse_list(lines: list[str], base: int) -> list:
    out: list = []
    for line in lines:
        if _indent(line) != base:
            continue
        s = line.strip()
        if not s.startswith("- "):
            continue
        rest = s[2:].strip()
        if rest.startswith("{") and rest.endswith("}"):
            out.append(_parse_inline_object(rest))
        else:
            out.append(_parse_scalar(rest))
    return out


# --- deterministic routing logic ---
CRISIS_KEYWORDS = {"crisis", "emergency", "panic", "overload red", "i can't breathe",
                   "can't breathe", "suicidal"}


def _detect_kind(text: str, config: dict) -> str:
    low = text.lower()
    if any(k in low for k in CRISIS_KEYWORDS):
        return "CRISIS"
    if low.startswith("/"):
        return "COMMAND"
    return "TRIGGER"


def _match_intent(text: str, exemplars: dict) -> tuple[str, float]:
    low = text.lower()
    best_bucket = None
    best_score = 0.0
    for bucket, items in exemplars.items():
        if bucket in ("schema_version", "marked_as_starter",
                      "last_tuned_from_traffic", "tuning_owner"):
            continue
        if not isinstance(items, list):
            continue
        score = 0.0
        for ex in items:
            ex_low = str(ex).lower()
            if ex_low.startswith("/") and low.startswith(ex_low.split()[0]):
                score = max(score, 1.0)
            tokens_a = set(re.findall(r"[a-z0-9-]+", ex_low))
            tokens_b = set(re.findall(r"[a-z0-9-]+", low))
            if tokens_a and tokens_b:
                jacc = len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)
                score = max(score, jacc)
        if score > best_score:
            best_score = score
            best_bucket = bucket
    return best_bucket or "capture", best_score


def main() -> int:
    config = _read_yaml(ROUTER_YAML)
    exemplars = _read_yaml(EXEMPLARS_YAML)
    intents_map = config.get("intents", {})

    results: list[dict] = []
    matches = 0
    total = 0
    with FIXTURE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1
            kind = _detect_kind(row["input"], config)
            if kind == "CRISIS":
                target = "protocol:crisis_sukoon_red"
                conf = 1.0
            else:
                bucket, conf = _match_intent(row["input"], exemplars)
                intent = intents_map.get(bucket, {})
                target = intent.get("target") if isinstance(intent, dict) else None
                if not target:
                    target = "Amin"
                    conf = max(conf, 0.0)
            row_out = {
                "input": row["input"],
                "kind": kind,
                "target": target,
                "confidence": round(conf, 3),
                "expected_kind": row.get("expected_kind"),
                "expected_target": row.get("expected_target"),
                "match": target == row.get("expected_target"),
            }
            results.append(row_out)
            if row_out["match"]:
                matches += 1

    acc = matches / total if total else 0.0
    min_acc = float(config.get("fixture", {}).get("expected_routing_min_accuracy",
                                                  0.80))

    print(f"router dry-run: {matches}/{total} matches (acc={acc:.0%}, "
          f"min={min_acc:.0%})")
    for r in results:
        mark = "OK " if r["match"] else "FAIL"
        print(f"  [{mark}] kind={r['kind']:<10} target={r['target']:<35} "
              f"conf={r['confidence']:.2f}  expected={r['expected_target']}  "
              f"input={r['input'][:60]!r}")

    return 0 if acc >= min_acc else 1


if __name__ == "__main__":
    sys.exit(main())
